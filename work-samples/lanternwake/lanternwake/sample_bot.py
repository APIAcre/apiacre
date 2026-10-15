"""A dependency-free HTTP client: join a human's table or create a new one."""

from __future__ import annotations

import argparse
import copy
import json
import time
from http.client import IncompleteRead
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def choose(room: dict[str, Any], seat: int) -> dict[str, Any]:
    """Prefer control this tide, with a small allowance for the next tide."""
    game = room["game"]

    def value(action: dict[str, Any]) -> float:
        harbors = copy.deepcopy(game["harbors"])
        bank = action["count"] if action["type"] == "bank" else 0
        if action["type"] == "deploy":
            harbors[action["harbor"]]["lanterns"][seat] += action["count"]
        elif action["type"] == "bank":
            harbors[action["harbor"]]["lanterns"][seat] -= action["count"]
        else:
            harbors[action["from"]]["lanterns"][seat] -= action["count"]
            harbors[action["to"]]["lanterns"][seat] += action["count"]
        utility = float(bank)
        next_tide = game["forecast"][min(game["round"], game["max_rounds"] - 1)]
        for index, harbor in enumerate(harbors):
            mine = harbor["lanterns"][seat]
            rival = max(n for i, n in enumerate(harbor["lanterns"]) if i != seat)
            reward = harbor["reward"] + (
                0.2 * next_tide[index] if game["round"] < game["max_rounds"] else 0
            )
            if mine > rival:
                utility += reward + min(mine - rival - 1, 2) * 0.15
            elif rival > mine:
                utility -= reward * 0.35
            utility += mine * 0.05
        return utility

    return max(room["legal_actions"], key=value)


def call(
    base: str, path: str, payload: dict[str, Any] | None = None, token: str | None = None
) -> dict[str, Any]:
    headers = {"User-Agent": "Lanternwake-Sample-Bot/1", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    raw = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        raw = json.dumps(payload).encode()
    with urlopen(Request(base + path, data=raw, headers=headers), timeout=10) as response:
        result: dict[str, Any] = json.load(response)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="https://apiacre.com",
        help="Origin, without /arcade (default: https://apiacre.com)",
    )
    parser.add_argument("--room", help="Join this lobby code; its human host starts the match")
    parser.add_argument("--name", default="Tide Reader")
    parser.add_argument("--seats", type=int, choices=(2, 3, 4), default=2)
    parser.add_argument(
        "--wait", type=float, default=20, help="Seconds for humans to join when creating a table"
    )
    args = parser.parse_args()
    parsed = urlsplit(args.base)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        parser.error("--base must be an HTTP(S) origin, for example http://127.0.0.1:8000")
    if not 0 <= args.wait <= 300:
        parser.error("--wait must be between 0 and 300 seconds")
    base = args.base.rstrip("/") + "/arcade/lanternwake/api"
    try:
        if args.room:
            joined = call(
                base, "/rooms/" + args.room.upper() + "/join", {"name": args.name, "kind": "agent"}
            )
        else:
            joined = call(base, "/rooms", {"name": args.name, "kind": "agent", "seats": args.seats})
        code, token, seat = joined["code"], joined["token"], joined["seat"]
        print(
            json.dumps(
                {
                    "room": code,
                    "seat": seat,
                    "watch": args.base.rstrip("/") + "/arcade/lanternwake?room=" + code,
                }
            ),
            flush=True,
        )
        if not args.room:
            time.sleep(args.wait)
            call(base, "/rooms/" + code + "/start", {}, token)
        until = time.monotonic() + 1800
        while time.monotonic() < until:
            try:
                room = call(base, "/rooms/" + code)
                if room["phase"] == "finished":
                    print(
                        json.dumps(
                            {
                                "finished": True,
                                "scores": room["game"]["scores"],
                                "winners": [
                                    room["seats"][i]["name"] for i in room["game"]["winners"]
                                ],
                            }
                        ),
                        flush=True,
                    )
                    return 0
                if room["phase"] == "active" and room["game"]["current_player"] == seat:
                    room = call(
                        base,
                        "/rooms/" + code + "/moves",
                        {"version": room["version"], "action": choose(room, seat)},
                        token,
                    )
                    print(
                        json.dumps(
                            {"turn": room["game"]["turn"], "scores": room["game"]["scores"]}
                        ),
                        flush=True,
                    )
                time.sleep(1)
            except HTTPError as exc:
                if exc.code == 409:
                    continue
                if exc.code == 429:
                    time.sleep(min(60, max(1, int(exc.headers.get("Retry-After", "5")))))
                    continue
                if exc.code in {408, 500, 502, 503, 504}:
                    # The move may have reached the server. Read fresh state next;
                    # never replay an uncertain move with its old version.
                    time.sleep(1)
                    continue
                raise
            except (URLError, TimeoutError, OSError, IncompleteRead):
                # Refresh state after a dropped connection, including a lost reply.
                time.sleep(1)
        print("The lobby wait expired. Join a new table and ask its host to start.")
        return 1
    except HTTPError as exc:
        try:
            detail = json.load(exc).get("detail", "Request failed")
        except (ValueError, AttributeError):
            detail = "Request failed"
        print(f"HTTP {exc.code}: {detail}")
        return 1
    except (URLError, TimeoutError, OSError):
        print("Could not reach the game. Check --base and your connection, then try again.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
