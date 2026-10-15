from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from lanternwake.sample_bot import choose
from lanternwake.server import MATCH_SECONDS, PREFIX, RoomManager, create_app


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def auth(token: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + token}


def table(client: TestClient, seats: int = 2) -> dict[str, Any]:
    response = client.post(PREFIX + "/api/rooms", json={"name": "Captain Moss", "seats": seats})
    assert response.status_code == 201
    return response.json()  # type: ignore[no-any-return]


@pytest.mark.parametrize("seats", [2, 3, 4])
def test_mixed_seats_play_complete_game_through_http(seats: int) -> None:
    app = create_app()
    clock = Clock()
    app.state.lanternwake.clock = clock
    with TestClient(app) as client:
        host = table(client, seats)
        path = PREFIX + "/api/rooms/" + host["code"]
        tokens = [host["token"]]
        for index in range(1, seats):
            joined = client.post(path + "/join", json={"name": f"Agent {index}", "kind": "agent"})
            assert joined.status_code == 201
            tokens.append(joined.json()["token"])
        assert client.post(path + "/start", json={}, headers=auth(tokens[1])).status_code == 403
        started = client.post(path + "/start", json={}, headers=auth(tokens[0]))
        assert started.status_code == 200
        room = started.json()
        previous_version = room["version"]
        while room["phase"] == "active":
            player = room["game"]["current_player"]
            moved = client.post(
                path + "/moves",
                json={"version": room["version"], "action": choose(room, player)},
                headers=auth(tokens[player]),
            )
            assert moved.status_code == 200
            room = moved.json()
            assert room["version"] == previous_version + 1
            previous_version = room["version"]
        assert room["game"]["turn"] == seats * (9 if seats == 3 else 8)
        assert (
            len([e for e in room["game"]["log"] if e["kind"] == "tide"])
            == room["game"]["max_rounds"]
        )
        assert room["game"]["winners"]
        assert room["legal_actions"] == []
        assert all(token not in json.dumps(room) for token in tokens)
        assert client.get(path).json()["game"] == room["game"]
        assert client.post(path + "/join", json={"name": "Late"}).status_code == 409


def test_versions_tokens_and_invalid_moves_do_not_change_game() -> None:
    app = create_app()
    app.state.lanternwake.clock = Clock()
    with TestClient(app) as client:
        host = table(client)
        path = PREFIX + "/api/rooms/" + host["code"]
        guest = client.post(path + "/join", json={"name": "Second captain"}).json()
        room = client.post(path + "/start", json={}, headers=auth(host["token"])).json()
        current_token = [host["token"], guest["token"]][room["game"]["current_player"]]
        action = room["legal_actions"][0]
        payload = {"version": room["version"], "action": action}
        assert client.post(path + "/moves", json=payload).status_code == 401
        assert client.post(path + "/moves", json=payload, headers=auth("wrong")).status_code == 401
        invalid = {**payload, "action": {"type": "deploy", "harbor": 0, "count": True}}
        assert (
            client.post(path + "/moves", json=invalid, headers=auth(current_token)).status_code
            == 422
        )
        assert client.get(path).json()["game"] == room["game"]
        moved = client.post(path + "/moves", json=payload, headers=auth(current_token))
        assert moved.status_code == 200
        assert (
            client.post(path + "/moves", json=payload, headers=auth(current_token)).status_code
            == 409
        )
        assert client.get(path).json()["game"] == moved.json()["game"]
        assert client.get(path).headers["cache-control"] == "no-store"


def test_disconnect_fallback_finishes_four_humans_below_ten_minutes() -> None:
    clock = Clock()
    manager = RoomManager(clock)
    room, _ = manager.create("First", "human", 4, "local")
    for name in ("Second", "Third", "Fourth"):
        manager.join(room, name, "human")
    manager.start(room, 0)
    started = clock.now
    while room.game and room.game["phase"] == "active":
        clock.now += 16.25
        manager.advance(room)
    assert room.game is not None
    assert room.game["turn"] == 32
    assert clock.now - started == 520 < 600
    moves = [e for e in room.game["log"] if e["kind"] == "move"]
    assert all(e["details"]["reason"] == "turn_timeout" for e in moves)
    assert [sum(e["player"] == p for e in moves) for p in range(4)] == [8] * 4


def test_hard_deadline_completes_equal_turns_and_keeps_final_log() -> None:
    clock = Clock()
    manager = RoomManager(clock)
    room, _ = manager.create("First", "human", 4, "local")
    manager.start(room, 0)
    clock.now += MATCH_SECONDS
    manager.advance(room)
    assert room.game is not None
    assert room.game["phase"] == "finished"
    assert room.game["turn"] == 32
    assert "Time limit" in room.game["finish_reason"]
    assert len([e for e in room.game["log"] if e["kind"] == "tide"]) == 8
    clock.now += 3599
    assert manager.get(room.code) is room
    clock.now += 2
    with pytest.raises(HTTPException) as error:
        manager.get(room.code)
    assert error.value.status_code == 404


def test_lobby_bot_fill_and_expiry_do_not_expire_an_active_game() -> None:
    clock = Clock()
    manager = RoomManager(clock)
    room, _ = manager.create("First", "human", 3, "local")
    clock.now += 1799
    manager.start(room, 0)
    assert [s.kind for s in room.seats if s] == ["human", "bot", "bot"]
    assert room.game is not None
    while room.game["current_player"] != 0:
        clock.now += 0.81
        manager.advance(room)
    before_turn = room.game["turn"]
    manager.move(room, 0, room.version, manager.public(room)["legal_actions"][0])
    clock.now += 0.81
    manager.advance(room)
    assert room.game["turn"] == before_turn + 2
    clock.now += 2
    assert manager.get(room.code) is room
    abandoned, _ = manager.create("Forgotten", "human", 2, "local")
    clock.now += 1801
    manager.cleanup()
    assert abandoned.code not in manager.rooms


@pytest.mark.parametrize(
    "payload",
    [
        {"name": " ", "seats": 2},
        {"name": "Line\nbreak", "seats": 2},
        {"name": "A", "seats": 5},
        {"name": "A", "seats": "2"},
        {"name": "A", "seats": True},
        {"name": "A", "kind": "bot"},
        {"name": "A", "unknown": 1},
        [],
    ],
)
def test_invalid_lobby_inputs_create_no_room(payload: Any) -> None:
    app = create_app()
    with TestClient(app) as client:
        assert client.post(PREFIX + "/api/rooms", json=payload).status_code == 422
        assert app.state.lanternwake.rooms == {}


def test_json_size_origin_and_rate_errors_recover() -> None:
    app = create_app()
    clock = Clock()
    app.state.lanternwake.clock = clock
    path = PREFIX + "/api/rooms"
    with TestClient(app) as client:
        assert client.post(path, content="name=A").status_code == 415
        assert (
            client.post(
                path, content="{" + " " * 4096, headers={"Content-Type": "application/json"}
            ).status_code
            == 413
        )
        assert (
            client.post(
                path, json={"name": "A"}, headers={"Origin": "https://other.invalid"}
            ).status_code
            == 403
        )
        assert (
            client.post(
                path, json={"name": "A"}, headers={"Origin": "http://testserver"}
            ).status_code
            == 201
        )
        host = table(client)
        read = path + "/" + host["code"]
        for _ in range(600):
            assert client.get(read).status_code == 200
        limited = client.get(read)
        assert limited.status_code == 429 and int(limited.headers["retry-after"]) == 60
        clock.now += 61
        assert client.get(read).status_code == 200
