"""One-process HTTP rooms. The browser and external agents use identical moves."""

from __future__ import annotations

import asyncio
import copy
import json
import math
import secrets
import time
import unicodedata
from collections import deque
from collections.abc import Callable
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError

from .engine import apply_action, choose_bot_action, finish_game, legal_actions, new_game

PREFIX = "/arcade/lanternwake"
STATIC = Path(__file__).parent / "static"
TURN_SECONDS = 16.0
MATCH_SECONDS = 540.0
BOT_SECONDS = 0.8
MAX_ROOMS = 64
RULES = (
    "On your turn, place 1-2 of your seven lanterns from reserve, ferry 1-2 between "
    "harbors, or bank 1-2 for one point each. After everyone acts, each harbor's sole "
    "lantern leader earns its shown tide reward and returns one winning lantern to "
    "reserve; tied leaders earn nothing. The full tide forecast is public. The "
    "opening captain is drawn, then the first player rotates each round. After eight tides (nine with three players), "
    "the most points wins; tied top scores share victory. You have 16 seconds per "
    "turn; a bot makes a move if you run out of time."
)


class SeatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=22)
    kind: Literal["human", "agent"] = "human"


class CreateRequest(SeatRequest):
    seats: StrictInt = Field(default=2, ge=2, le=4)


class MoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: StrictInt = Field(ge=0)
    action: dict[str, Any]


@dataclass
class Seat:
    name: str
    kind: str
    token: str = field(repr=False, default="")


@dataclass
class Room:
    code: str
    seats: list[Seat | None]
    owner_key: str = field(repr=False)
    created: float
    version: int = 0
    game: dict[str, Any] | None = None
    started: float | None = None
    turn_due: float | None = None
    finished: float | None = None


class RoomManager:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.rooms: dict[str, Room] = {}
        self.lock = asyncio.Lock()
        self.recent: dict[tuple[str, str], deque[float]] = {}

    def limit(self, client: str, bucket: str) -> None:
        now = self.clock()
        seconds, maximum = (
            (600, 10) if bucket == "create" else (60, 600 if bucket == "read" else 180)
        )
        key = (client, bucket)
        if key not in self.recent and len(self.recent) >= 4096:
            self.recent = {k: q for k, q in self.recent.items() if q and q[-1] > now - 600}
            if len(self.recent) >= 4096:
                raise HTTPException(503, "The harbor is busy. Please try again shortly.")
        queue = self.recent.setdefault(key, deque())
        while queue and queue[0] <= now - seconds:
            queue.popleft()
        if len(queue) >= maximum:
            retry = max(1, math.ceil(queue[0] + seconds - now))
            raise HTTPException(
                429, "Too many requests. Wait, then try again.", headers={"Retry-After": str(retry)}
            )
        queue.append(now)

    def cleanup(self) -> None:
        now = self.clock()
        expired = [
            code
            for code, room in self.rooms.items()
            if (room.game is None and now - room.created > 1800)
            or (room.finished is not None and now - room.finished > 3600)
        ]
        for code in expired:
            del self.rooms[code]

    def get(self, code: str) -> Room:
        self.cleanup()
        room = self.rooms.get(code.upper())
        if room is None:
            raise HTTPException(
                404, "That table has expired or does not exist. Create a new table."
            )
        self.advance(room)
        return room

    def create(self, name: str, kind: str, seats: int, client: str) -> tuple[Room, str]:
        self.cleanup()
        self.limit(client, "create")
        if len(self.rooms) >= MAX_ROOMS:
            raise HTTPException(503, "All tables are occupied. Please try again later.")
        if sum(r.owner_key == client and r.finished is None for r in self.rooms.values()) >= 6:
            raise HTTPException(
                429, "You already have six open tables. Finish a match before creating another."
            )
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        while code in self.rooms:
            code = "".join(secrets.choice(alphabet) for _ in range(6))
        token = secrets.token_urlsafe(32)
        room = Room(code, [Seat(name, kind, token)] + [None] * (seats - 1), client, self.clock())
        self.rooms[code] = room
        return room, token

    def join(self, room: Room, name: str, kind: str) -> tuple[int, str]:
        if room.game is not None:
            raise HTTPException(
                409, "This match has started. You can watch it or create a new table."
            )
        for index, seat in enumerate(room.seats):
            if seat is None:
                token = secrets.token_urlsafe(32)
                room.seats[index] = Seat(name, kind, token)
                room.version += 1
                return index, token
        raise HTTPException(409, "This table is full. You can watch it or create a new table.")

    @staticmethod
    def authorize(room: Room, header: str | None) -> int:
        if header and header.startswith("Bearer ") and len(header) <= 128:
            token = header[7:]
            for index, seat in enumerate(room.seats):
                if (
                    seat is not None
                    and seat.token
                    and secrets.compare_digest(token.encode(), seat.token.encode())
                ):
                    return index
        raise HTTPException(
            401, "Use the private seat token returned when you created or joined this table."
        )

    def start(self, room: Room, seat: int) -> None:
        if seat != 0:
            raise HTTPException(403, "Only the host can start the match.")
        if room.game is not None:
            raise HTTPException(409, "This match has already started. Read its current state.")
        names = ["Pip the Puffin", "Moss the Otter", "Tansy the Gull", "Bramble the Crab"]
        for index, player in enumerate(room.seats):
            if player is None:
                room.seats[index] = Seat(names[index], "bot")
        room.game = new_game(len(room.seats), secrets.randbelow(2**31))
        room.started = self.clock()
        room.version += 1
        self.schedule(room)

    def schedule(self, room: Room) -> None:
        assert room.game is not None
        if room.game["phase"] == "finished":
            room.finished = self.clock()
            room.turn_due = None
            return
        seat = room.seats[room.game["current_player"]]
        assert seat is not None
        room.turn_due = self.clock() + (BOT_SECONDS if seat.kind == "bot" else TURN_SECONDS)

    def move(self, room: Room, seat: int, version: int, action: dict[str, Any]) -> None:
        if room.game is None or room.game["phase"] != "active":
            raise HTTPException(409, "This table is not in an active match.")
        if version != room.version:
            raise HTTPException(
                409, "The table has changed. Read the state and choose a fresh legal move."
            )
        if seat != room.game["current_player"]:
            raise HTTPException(409, "It is another captain's turn.")
        try:
            room.game = apply_action(room.game, seat, action)
        except (ValueError, TypeError, KeyError) as exc:
            raise HTTPException(
                422, "That move is not legal. Choose an action from legal_actions."
            ) from exc
        room.version += 1
        self.schedule(room)

    def advance(self, room: Room) -> None:
        if room.game is None or room.game["phase"] != "active":
            return
        now = self.clock()
        assert room.started is not None and room.turn_due is not None
        if now >= room.started + MATCH_SECONDS:
            room.game = finish_game(
                room.game, "Time limit: the harbor crew completed the remaining turns."
            )
            room.version += 1
            self.schedule(room)
        elif now >= room.turn_due:
            player = room.game["current_player"]
            current_seat = room.seats[player]
            assert current_seat is not None
            room.game = apply_action(room.game, player, choose_bot_action(room.game))
            for entry in reversed(room.game["log"]):
                if entry["kind"] == "move":
                    entry["details"]["automatic"] = True
                    entry["details"]["reason"] = (
                        "bot" if current_seat.kind == "bot" else "turn_timeout"
                    )
                    break
            room.version += 1
            self.schedule(room)

    def public(self, room: Room) -> dict[str, Any]:
        now = self.clock()
        phase = room.game["phase"] if room.game else "lobby"
        left = max(0, room.turn_due - now) if room.turn_due is not None else 0
        match_left = (
            max(0, room.started + MATCH_SECONDS - now)
            if room.started is not None and phase == "active"
            else 0
        )
        return {
            "code": room.code,
            "phase": phase,
            "host_seat": 0,
            "seats": [
                {"name": s.name, "kind": s.kind} if s else {"name": "Open seat", "kind": "empty"}
                for s in room.seats
            ],
            "version": room.version,
            "game": copy.deepcopy(room.game),
            "legal_actions": legal_actions(room.game) if room.game else [],
            "turn_seconds_left": round(left, 2),
            "match_seconds_left": round(match_left, 2),
            "turn_deadline": datetime.fromtimestamp(time.time() + left, UTC).isoformat()
            if room.turn_due
            else None,
            "server_time": datetime.now(UTC).isoformat(),
        }

    async def run(self) -> None:
        while True:
            async with self.lock:
                rooms = list(self.rooms.values())
                self.cleanup()
            for room in rooms:
                async with self.lock:
                    self.advance(room)
                # Yield between rooms so other API Acre routes remain responsive.
                await asyncio.sleep(0)
            await asyncio.sleep(0.25)


async def body(request: Request, model: type[BaseModel] | None = None) -> Any:
    origin = request.headers.get("origin")
    if origin:
        try:
            parsed = urlsplit(origin)
        except ValueError as exc:
            raise HTTPException(403, "Open the game on its own website.") from exc
        if parsed.scheme not in {"http", "https"} or parsed.netloc != request.headers.get("host"):
            raise HTTPException(
                403, "Open the game on its own website before creating or changing a table."
            )
    if (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        != "application/json"
    ):
        raise HTTPException(415, "Send Content-Type: application/json.")
    raw = bytearray()
    try:
        async with asyncio.timeout(5):
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw) > 4096:
                    raise HTTPException(413, "This game accepts JSON requests up to 4096 bytes.")
    except TimeoutError as exc:
        raise HTTPException(408, "Request timed out. Try again.") from exc
    try:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("Expected an object")
        if model is None:
            if value:
                raise ValueError("Expected an empty object")
            return value
        result = model.model_validate(value)
        if isinstance(result, SeatRequest):
            result.name = result.name.strip()
            if not result.name or any(unicodedata.category(c).startswith("C") for c in result.name):
                raise ValueError("Choose a short, single-line captain name")
        return result
    except (ValueError, ValidationError, UnicodeError, RecursionError) as exc:
        raise HTTPException(
            422,
            "Check your JSON fields. Use a single-line name (1-22 characters), 2-4 seats, and a legal action.",
        ) from exc


def install_routes(app: FastAPI, client_key: Callable[[Request], str] | None = None) -> None:
    manager = RoomManager()
    app.state.lanternwake = manager
    identify = client_key or (lambda request: request.client.host if request.client else "unknown")

    def response(value: dict[str, Any], status: int = 200) -> JSONResponse:
        return JSONResponse(
            value,
            status_code=status,
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            },
        )

    @app.get(PREFIX, include_in_schema=False)
    async def page() -> FileResponse:
        return FileResponse(
            STATIC / "index.html",
            headers={
                "Cache-Control": "no-cache",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'self'",
            },
        )

    @app.get(PREFIX + "/assets/{filename}", include_in_schema=False)
    async def asset(filename: str) -> FileResponse:
        if filename not in {"game.css", "game.js", "cover.svg"}:
            raise HTTPException(404, "Asset not found")
        return FileResponse(STATIC / filename, headers={"Cache-Control": "public, max-age=300"})

    @app.get(PREFIX + "/docs", response_class=HTMLResponse, include_in_schema=False)
    async def docs() -> FileResponse:
        return FileResponse(STATIC / "docs.html", headers={"Cache-Control": "public, max-age=300"})

    @app.get(PREFIX + "/sample_bot.py", include_in_schema=False)
    async def sample_bot() -> FileResponse:
        return FileResponse(
            Path(__file__).parent / "sample_bot.py",
            media_type="text/plain",
            headers={"Cache-Control": "public, max-age=300"},
        )

    @app.get(PREFIX + "/api/rules", include_in_schema=False)
    async def rules() -> JSONResponse:
        return response(
            {
                "name": "Lanternwake",
                "rules": RULES,
                "players": [2, 3, 4],
                "turn_seconds": TURN_SECONDS,
                "match_cap_seconds": MATCH_SECONDS,
                "api_docs": PREFIX + "/docs",
            }
        )

    @app.post(PREFIX + "/api/rooms", include_in_schema=False)
    async def create(request: Request) -> JSONResponse:
        payload = await body(request, CreateRequest)
        async with manager.lock:
            room, token = manager.create(
                payload.name, payload.kind, payload.seats, identify(request)
            )
            return response(
                {"code": room.code, "token": token, "seat": 0, "room": manager.public(room)}, 201
            )

    @app.get(PREFIX + "/api/rooms/{code}", include_in_schema=False)
    async def read(code: str, request: Request) -> JSONResponse:
        async with manager.lock:
            manager.limit(identify(request), "read")
            return response(manager.public(manager.get(code)))

    @app.post(PREFIX + "/api/rooms/{code}/join", include_in_schema=False)
    async def join(code: str, request: Request) -> JSONResponse:
        payload = await body(request, SeatRequest)
        async with manager.lock:
            manager.limit(identify(request), "write")
            room = manager.get(code)
            seat, token = manager.join(room, payload.name, payload.kind)
            return response(
                {"code": room.code, "token": token, "seat": seat, "room": manager.public(room)}, 201
            )

    @app.post(PREFIX + "/api/rooms/{code}/start", include_in_schema=False)
    async def start(code: str, request: Request) -> JSONResponse:
        await body(request)
        async with manager.lock:
            manager.limit(identify(request), "write")
            room = manager.get(code)
            manager.start(room, manager.authorize(room, request.headers.get("authorization")))
            return response(manager.public(room))

    @app.post(PREFIX + "/api/rooms/{code}/moves", include_in_schema=False)
    async def move(code: str, request: Request) -> JSONResponse:
        payload = await body(request, MoveRequest)
        async with manager.lock:
            manager.limit(identify(request), "write")
            room = manager.get(code)
            manager.move(
                room,
                manager.authorize(room, request.headers.get("authorization")),
                payload.version,
                payload.action,
            )
            return response(manager.public(room))


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        task = asyncio.create_task(app.state.lanternwake.run())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title="Lanternwake", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    install_routes(app)
    return app


app = create_app()
