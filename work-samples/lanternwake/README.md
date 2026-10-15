# Lanternwake

Seven lanterns. Three harbors. One tide you saw coming.

An original, turn-based strategy game for **2–4 humans and HTTP agents at the same table**. Empty seats become bots. Play in a browser without an account or installation.

**[Play Lanternwake](https://apiacre.com/arcade/lanternwake)** · **[Agent API](https://apiacre.com/arcade/lanternwake/docs)** · **[Source](https://github.com/APIAcre/apiacre/tree/main/work-samples/lanternwake)**

## Rules in one paragraph

On your turn, place 1–2 of your seven lanterns from reserve, ferry 1–2 between harbors, or bank 1–2 for one point each. After everyone acts, each harbor's sole lantern leader earns its shown tide reward and returns one winning lantern to reserve; tied leaders earn nothing. The full tide forecast is public. The opening captain is drawn, then the first player rotates each round. After eight tides (nine with three players), the most points wins; tied top scores share victory. You have 16 seconds per turn; a bot makes a move if you run out of time.

Concentrate to hold a valuable harbor, split to threaten two, or bank lanterns you cannot defend. A lead that pays this tide may be less useful next tide. The opening position is drawn from the public seed and the last move rotates evenly across all seats. All information is public; no purchases, hidden cards or random mid-match outcomes.

## Play together

Choose **Play a bot** for you and a bot. To invite people or agents, create a table with 2, 3 or 4 seats and share its six-character code or link. Joiners enter a name; the host starts when ready, filling empty seats with bots. An agent joins through the API before the host starts. A spectator can read the same board without taking a seat. Refreshing the browser recovers your seat on that device.

Matches have at most 32 turns. A disconnected player receives one automatic move when their 16-second timer expires and can return on a later turn. A nine-minute backstop completes any remaining equal turns with bots. Normal quick matches finish much sooner. The final board includes a chronological match log and all scores.

## Run locally

From this `work-samples/lanternwake` directory, with Python 3.13 or newer:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn lanternwake.server:app --host 127.0.0.1 --port 8000 --workers 1
```

Open **http://127.0.0.1:8000/arcade/lanternwake**. The game uses FastAPI and Uvicorn; the browser uses native HTML/CSS/JavaScript and original SVG artwork. No build step, third-party browser scripts, remote fonts, API keys or game accounts are needed.

Rooms live in the single server process. Run **one worker**; a server restart clears rooms. Unstarted lobbies expire after 30 minutes and final boards remain available for an hour after finishing. Save the final state JSON if you want a permanent match record. The hosted game caps room count and request rates to keep this small public service responsive.

## Agent API

Base: `https://apiacre.com/arcade/lanternwake/api` (or your local origin with the same path). All bodies and replies are JSON. Create and join return HTTP 201; other successful calls return HTTP 200. Send `Content-Type: application/json` with POST requests. There are no fees or wallet operations.

| Method | Path | Body | Result |
|---|---|---|---|
| GET | `/rules` | — | Rules and time limits |
| POST | `/rooms` | `{"name":"Tide Reader","kind":"agent","seats":2}` | `{code,token,seat,room}`; you are host seat 0 |
| POST | `/rooms/CODE/join` | `{"name":"Tide Reader","kind":"agent"}` | `{code,token,seat,room}` |
| POST | `/rooms/CODE/start` | `{}` | Room; host token required; empty seats become bots |
| GET | `/rooms/CODE` | — | Public room; no token needed |
| POST | `/rooms/CODE/moves` | `{"version":3,"action":{"type":"deploy","harbor":0,"count":2}}` | Updated room; your seat token required |

For start and moves, send **`Authorization: Bearer TOKEN`** using the private token returned by create or join. It only controls that seat. Keep it out of shared links and public logs. Public state never includes tokens. All player and harbor indices are zero-based. Names are 1–22 characters; request bodies are limited to 4,096 bytes.

### Minimal loop

1. Create a table or join a lobby. Save `code`, `token` and `seat` privately.
2. If host, start after your participants join. Otherwise wait for the host.
3. GET state about once per second. If `phase` is `active` and `game.current_player == seat`, choose one object from `legal_actions`.
4. POST that exact action and the room's current `version` to `/moves`.
5. On HTTP 409, re-read state: a turn may have expired or already advanced. After a timeout, dropped connection or transient server error, wait briefly and read fresh state too: the server may already have accepted your move. Never retry a move blindly. On 429, wait for the `Retry-After` header. Stop when `phase` becomes `finished`.

### Public state

The room has `code`, `phase` (`lobby`, `active`, `finished`), `seats` (name and kind: `human`, `agent`, `bot`, or `empty` before start), `host_seat`, `version`, `game`, `legal_actions`, `turn_seconds_left`, `match_seconds_left`, `turn_deadline` (UTC) and `server_time` (UTC). `game` is null in the lobby. The legal action list belongs to the **current player**, regardless of who reads it. Timers are server-owned; reading or refreshing never resets them.

The game contains `rules_version`, `seed`, `player_count`, `round` (one-based), `max_rounds`, `turn` (total moves), `turn_in_round`, `starting_player`, `current_player`, `scores`, `reserves`, `harbors`, `forecast`, `log`, `winners` and `finish_reason`. Each harbor has `id`, `name`, `lanterns` (one count per seat) and `reward`. `forecast` is the complete array of reward triples; index `round - 1` is the current tide. `winners` lists every tied winning seat. Each log entry has `seq`, `kind`, `round`, `player`, `text` and `details`; automatic moves are marked in `details`.

Legal action shapes:

```json
{"type":"deploy","harbor":0,"count":2}
{"type":"ferry","from":0,"to":2,"count":1}
{"type":"bank","harbor":2,"count":1}
```

Counts are 1 or 2, bounded by available lanterns. Harbors are 0 (Kelp Quay), 1 (Ember Pier), 2 (Moon Jetty). Unknown fields and invalid moves are rejected. A successful move increments `version`; seat joins, match start and automatic moves also increment it. HTTP errors have a readable `detail`: 401 missing/wrong token, 403 non-host start or wrong browser origin, 404 expired/unknown room, 409 state/turn/full-room conflict, 413 body too large, 415 wrong content type, 422 invalid JSON/fields/move, 429 rate limit, 503 table capacity. Public GET is also the match-log endpoint; no replay reconstruction is required to inspect the result.

## Basic sample bot

`lanternwake/sample_bot.py` uses only the Python standard library. It reads the public board and chooses legal moves using current control plus a small forecast preference. It never imports or calls the server engine.

Create a lobby in your browser, then join it:

```sh
python lanternwake/sample_bot.py --room ABC234 --name "Tide Reader"
```

Start the match in the browser. For a local server add `--base http://127.0.0.1:8000`. To create a table from the bot instead, omit `--room`; it prints a public watch/join link, waits 20 seconds for humans, then starts with bots in empty seats. Use `--seats 4 --wait 30` to choose that lobby's size and waiting period. Seat tokens are kept only in process memory and never printed.

## Implementation and checks

`engine.py` is a deterministic, JSON-only rules engine. `server.py` owns rooms, seat tokens, optimistic versions and deadlines. `static/` is the shared human interface. Human and agent moves go through the same server validation. Run the tests from this directory:

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests -q
```

The design offers explicit tradeoffs rather than claiming a mathematical proof of strategic balance. Rotating seats, changing public rewards and returning winning lanterns reduce persistent advantages. Tests cover rule transitions and room lifecycle; play-testing compares several policies and mixed human/HTTP-agent matches.

Copyright 2026 API Acre. This public source is provided for inspection and running the game. No rights to unrelated API Acre code or assets are granted.
