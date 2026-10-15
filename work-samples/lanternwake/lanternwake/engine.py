"""Deterministic, public-information rules for Lanternwake.

There is no network, identity, persistence, clock, or hidden state in this module.
The server owns those concerns and passes only a validated seat and move here.
Every transition returns a new JSON-serializable state without mutating its input.
"""

from __future__ import annotations

from copy import deepcopy
from random import Random
from typing import Any

State = dict[str, Any]
Action = dict[str, Any]

LANTERNS_PER_PLAYER = 7
HARBOR_NAMES = ("Kelp Quay", "Ember Pier", "Moon Jetty")
RULES_VERSION = 1


def new_game(player_count: int, seed: int) -> State:
    """Create a public match with seeded visible tides and an opening captain."""
    if type(player_count) is not int or player_count not in (2, 3, 4):
        raise ValueError("A match needs 2, 3, or 4 players.")
    if type(seed) is not int:
        raise ValueError("seed must be an integer.")
    rounds = 9 if player_count == 3 else 8
    # Draw the opener separately so the same seed retains its tide forecast.
    starting_player = Random(f"lanternwake-opening-{seed}").randrange(player_count)
    rng = Random(seed)
    forecast: list[list[int]] = []
    while len(forecast) < rounds:
        # Every complete three-tide set gives each harbor each payout once.
        base = [2, 3, 5]
        rng.shuffle(base)
        cycle = [base[index:] + base[:index] for index in range(3)]
        rng.shuffle(cycle)
        forecast.extend(cycle)
    forecast = forecast[:rounds]
    return {
        "rules_version": RULES_VERSION,
        "seed": seed,
        "phase": "active",
        "player_count": player_count,
        "round": 1,
        "max_rounds": rounds,
        "turn": 0,
        "turn_in_round": 0,
        "starting_player": starting_player,
        "current_player": starting_player,
        "scores": [0] * player_count,
        "reserves": [LANTERNS_PER_PLAYER] * player_count,
        "harbors": [
            {
                "id": index,
                "name": name,
                "lanterns": [0] * player_count,
                "reward": forecast[0][index],
            }
            for index, name in enumerate(HARBOR_NAMES)
        ],
        "forecast": forecast,
        "log": [
            {
                "seq": 0,
                "kind": "start",
                "round": 1,
                "player": None,
                "text": f"{player_count} captains set sail for {rounds} tides. Captain {starting_player + 1} opens.",
                "details": {
                    "seed": seed,
                    "rules_version": RULES_VERSION,
                    "starting_player": starting_player,
                },
            }
        ],
        "winners": [],
        "finish_reason": None,
    }


def legal_actions(state: State) -> list[Action]:
    """Enumerate every allowed move for the seat whose turn it currently is."""
    if state["phase"] != "active":
        return []
    player = state["current_player"]
    actions: list[Action] = []
    for harbor in state["harbors"]:
        harbor_id = harbor["id"]
        for count in range(1, min(2, state["reserves"][player]) + 1):
            actions.append({"type": "deploy", "harbor": harbor_id, "count": count})
        for count in range(1, min(2, harbor["lanterns"][player]) + 1):
            actions.append({"type": "bank", "harbor": harbor_id, "count": count})
            for destination in range(3):
                if destination != harbor_id:
                    actions.append(
                        {"type": "ferry", "from": harbor_id, "to": destination, "count": count}
                    )
    return actions


def _validate_action(state: State, player: int, action: Action) -> None:
    if state["phase"] != "active":
        raise ValueError("This match is already finished.")
    if type(player) is not int or not 0 <= player < state["player_count"]:
        raise ValueError("player_index must name an occupied seat.")
    if player != state["current_player"]:
        raise ValueError(f"It is Captain {state['current_player'] + 1}'s turn.")
    if not isinstance(action, dict):
        raise ValueError("An action must be a JSON object.")
    action_type = action.get("type")
    if action_type not in ("deploy", "ferry", "bank"):
        raise ValueError("Action type must be deploy, ferry, or bank.")
    expected = (
        {"type", "from", "to", "count"} if action_type == "ferry" else {"type", "harbor", "count"}
    )
    if set(action) != expected:
        raise ValueError(f"{action_type} expects exactly {', '.join(sorted(expected))}.")
    count = action["count"]
    if type(count) is not int or count not in (1, 2):
        raise ValueError("count must be the integer 1 or 2.")
    harbor_fields = ("from", "to") if action_type == "ferry" else ("harbor",)
    for field in harbor_fields:
        if type(action[field]) is not int or not 0 <= action[field] < 3:
            raise ValueError(f"{field} must be harbor 0, 1, or 2.")
    if action_type == "deploy":
        if state["reserves"][player] < count:
            raise ValueError("Not enough lanterns in reserve.")
    else:
        source = action["from"] if action_type == "ferry" else action["harbor"]
        if state["harbors"][source]["lanterns"][player] < count:
            raise ValueError("Not enough of your lanterns in that harbor.")
        if action_type == "ferry" and source == action["to"]:
            raise ValueError("Ferry between two different harbors.")


def _append_log(
    state: State, kind: str, text: str, details: dict[str, Any], player: int | None = None
) -> None:
    state["log"].append(
        {
            "seq": len(state["log"]),
            "kind": kind,
            "round": state["round"],
            "player": player,
            "text": text,
            "details": details,
        }
    )


def _finish(state: State, reason: str) -> None:
    state["phase"] = "finished"
    state["current_player"] = None
    state["finish_reason"] = reason
    highest = max(state["scores"])
    state["winners"] = [player for player, score in enumerate(state["scores"]) if score == highest]
    names = ", ".join(f"Captain {player + 1}" for player in state["winners"])
    result = "wins" if len(state["winners"]) == 1 else "share victory"
    _append_log(
        state,
        "finish",
        f"{names} {result} with {highest} points.",
        {"winners": state["winners"][:], "scores": state["scores"][:], "reason": reason},
    )


def _settle_tide(state: State) -> None:
    awards: list[dict[str, Any]] = []
    descriptions: list[str] = []
    for harbor in state["harbors"]:
        lanterns = harbor["lanterns"]
        counts_before = lanterns[:]
        highest = max(lanterns)
        leaders = (
            [player for player, count in enumerate(lanterns) if count == highest] if highest else []
        )
        winner = leaders[0] if len(leaders) == 1 else None
        if winner is not None:
            state["scores"][winner] += harbor["reward"]
            lanterns[winner] -= 1
            state["reserves"][winner] += 1
            descriptions.append(
                f"Captain {winner + 1} earns {harbor['reward']} at {harbor['name']}"
            )
        elif leaders:
            descriptions.append(f"{harbor['name']} is tied: no payout")
        else:
            descriptions.append(f"{harbor['name']} is empty")
        awards.append(
            {
                "harbor": harbor["id"],
                "reward": harbor["reward"],
                "winner": winner,
                "leaders": leaders,
                "lanterns": counts_before,
            }
        )
    _append_log(
        state,
        "tide",
        f"Tide {state['round']}: " + "; ".join(descriptions) + ".",
        {"awards": awards, "scores": state["scores"][:]},
    )
    state["turn_in_round"] = 0
    if state["round"] == state["max_rounds"]:
        _finish(state, "rounds_complete")
        return
    state["round"] += 1
    for harbor in state["harbors"]:
        harbor["reward"] = state["forecast"][state["round"] - 1][harbor["id"]]
    state["current_player"] = (state["starting_player"] + state["round"] - 1) % state[
        "player_count"
    ]


def apply_action(state: State, player_index: int, action: Action) -> State:
    """Apply exactly one legal move, score a completed tide, and return a copy.

    Invalid moves raise ``ValueError`` before copying or changing any state.
    Extra fields and non-integer counts/harbor identifiers are rejected so the
    exact documented move is the move that actually takes effect.
    """
    _validate_action(state, player_index, action)
    result = deepcopy(state)
    count = action["count"]
    action_type = action["type"]
    if action_type == "deploy":
        harbor = result["harbors"][action["harbor"]]
        result["reserves"][player_index] -= count
        harbor["lanterns"][player_index] += count
        description = f"deploys {count} to {harbor['name']}"
    elif action_type == "bank":
        harbor = result["harbors"][action["harbor"]]
        harbor["lanterns"][player_index] -= count
        result["reserves"][player_index] += count
        result["scores"][player_index] += count
        description = f"banks {count} from {harbor['name']} for {count} points"
    else:
        source = result["harbors"][action["from"]]
        destination = result["harbors"][action["to"]]
        source["lanterns"][player_index] -= count
        destination["lanterns"][player_index] += count
        description = f"ferries {count} from {source['name']} to {destination['name']}"
    _append_log(
        result,
        "move",
        f"Captain {player_index + 1} {description}.",
        {"action": dict(action), "turn": state["turn"]},
        player_index,
    )
    result["turn"] += 1
    result["turn_in_round"] += 1
    if result["turn_in_round"] == result["player_count"]:
        _settle_tide(result)
    else:
        result["current_player"] = (player_index + 1) % result["player_count"]
    return result


def _position_value(state: State, player: int) -> float:
    """Small public-state heuristic, deliberately separate from game rules."""
    value = float(state["scores"][player])
    if state["phase"] == "finished":
        return value
    value += 0.11 * state["reserves"][player]
    remaining_tides = state["max_rounds"] - state["round"] + 1
    current = state["current_player"]
    to_act = {
        (current + offset) % state["player_count"]
        for offset in range(state["player_count"] - state["turn_in_round"])
    }
    for harbor in state["harbors"]:
        own = harbor["lanterns"][player]
        if not own:
            continue
        enemy = max(count for index, count in enumerate(harbor["lanterns"]) if index != player)
        gap = own - enemy
        opponents_left = any(index != player for index in to_act)
        if not opponents_left:
            share = 1.0 if gap > 0 else 0.0
        elif gap > 0:
            share = min(0.95, 0.54 + 0.13 * gap)
        elif gap == 0:
            share = 0.18
        else:
            share = max(0.02, 0.10 + 0.025 * gap)
        value += harbor["reward"] * share
        # Some of today's pieces can survive into the next public tide; avoid
        # valuing remote future tides as though opponents cannot react.
        if remaining_tides > 1:
            future_reward = state["forecast"][state["round"]][harbor["id"]]
            future_share = (
                own
                * own
                / (
                    own * own
                    + sum(
                        count * count
                        for index, count in enumerate(harbor["lanterns"])
                        if index != player
                    )
                    + 2.0
                )
            )
            value += 0.38 * future_reward * future_share
        value += 0.15 * own
    return float(value)


def _bot_value(state: State, player: int) -> float:
    values = [_position_value(state, seat) for seat in range(state["player_count"])]
    rival = max(value for seat, value in enumerate(values) if seat != player)
    rival_weight = 1.0 if state["player_count"] == 2 else 0.6
    value = values[player] - rival_weight * rival
    # Terminal victory matters more than its margin: a safe shared victory
    # is preferred to a loss with a higher personal point total.
    if state["phase"] == "finished":
        value += 1000 if player in state["winners"] else 0
        value += 10 if state["winners"] == [player] else 0
    return value


def choose_bot_action(state: State) -> Action:
    """Choose a deterministic legal move using only the public game state.

    The bot compares score, contested control, the next tide, and the strongest
    rival. Two-player matches additionally examine one reply, including their
    own consecutive turn when the starting seat rotates. This finite heuristic
    is neither a solved game nor an unbeatable policy.
    """
    actions = legal_actions(state)
    if not actions:
        raise ValueError("A finished match has no bot move.")
    player = state["current_player"]
    rng = Random(state["seed"] ^ (state["turn"] << 8) ^ player)
    # Narrative history cannot affect a move. Keep it out of the private search
    # copies, while leaving the authoritative state's complete log untouched.
    search_state = {**state, "log": []}
    best_action = actions[0]
    best_value = float("-inf")
    for action in actions:
        candidate = apply_action(search_state, player, action)
        if state["player_count"] == 2 and candidate["phase"] == "active":
            next_player = candidate["current_player"]
            replies = [
                _bot_value(apply_action(candidate, next_player, reply), player)
                for reply in legal_actions(candidate)
            ]
            value = max(replies) if next_player == player else min(replies)
        else:
            value = _bot_value(candidate, player)
        value += rng.random() * 0.00001
        if value > best_value:
            best_value = value
            best_action = action
    return dict(best_action)


def finish_game(state: State, reason: str) -> State:
    """Finish remaining turns with the bot, preserving equal turns per seat.

    The HTTP manager calls this at its absolute deadline. Partially played tides
    are completed, rather than discarded or awarded without all seats acting.
    Calling it again on a finished match is a harmless independent copy.
    """
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 120:
        raise ValueError("A short nonempty finish reason is required.")
    result = deepcopy(state)
    if result["phase"] == "finished":
        return result
    while result["phase"] == "active":
        start = len(result["log"])
        result = apply_action(result, result["current_player"], choose_bot_action(result))
        for entry in result["log"][start:]:
            if entry["kind"] == "move":
                entry["details"]["automatic"] = True
                entry["details"]["automatic_reason"] = reason
    result["finish_reason"] = reason
    final_entry = result["log"][-1]
    final_entry["details"]["reason"] = reason
    final_entry["text"] += " Remaining turns were completed automatically."
    return result
