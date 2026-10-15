from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from random import Random

import pytest

from lanternwake.engine import (
    LANTERNS_PER_PLAYER,
    apply_action,
    choose_bot_action,
    finish_game,
    legal_actions,
    new_game,
)


def assert_conservation(state: dict) -> None:
    for player in range(state["player_count"]):
        counts = [state["reserves"][player]] + [
            harbor["lanterns"][player] for harbor in state["harbors"]
        ]
        assert all(type(count) is int and count >= 0 for count in counts)
        assert sum(counts) == LANTERNS_PER_PLAYER
    assert all(score >= 0 for score in state["scores"])


def scenario_game(players: int, seed: int) -> dict:
    """Choose seat zero to open hand-authored tactical test positions."""
    state = new_game(players, seed)
    state["starting_player"] = 0
    state["current_player"] = 0
    state["log"][0]["details"]["starting_player"] = 0
    state["log"][0]["text"] = (
        f"{players} captains set sail for {state['max_rounds']} tides. Captain 1 opens."
    )
    return state


@pytest.mark.parametrize("players,rounds", [(2, 8), (3, 9), (4, 8)])
def test_public_setup_and_round_limits(players: int, rounds: int) -> None:
    state = new_game(players, 31)
    assert state == new_game(players, 31)
    assert json.loads(json.dumps(state)) == state
    assert state["max_rounds"] == rounds
    assert len(state["forecast"]) == rounds
    assert all(sorted(tide) == [2, 3, 5] for tide in state["forecast"])
    assert state["reserves"] == [7] * players
    assert state["scores"] == [0] * players
    assert 0 <= state["starting_player"] < players
    assert state["current_player"] == state["starting_player"]
    assert len(legal_actions(state)) == 6
    assert_conservation(state)


@pytest.mark.parametrize("players", [2, 3, 4])
def test_opening_seat_varies_with_seed_instead_of_belonging_to_host(players: int) -> None:
    games = [new_game(players, seed) for seed in range(24)]
    assert {state["starting_player"] for state in games} == set(range(players))
    for state in games:
        opener = state["starting_player"]
        assert state["log"][0]["details"]["starting_player"] == opener
        assert f"Captain {opener + 1} opens" in state["log"][0]["text"]


@pytest.mark.parametrize("players", [1, 5, 0, -1, True, 2.0, "2"])
def test_reject_invalid_player_count(players: object) -> None:
    with pytest.raises(ValueError):
        new_game(players, 1)  # type: ignore[arg-type]


@pytest.mark.parametrize("seed", [True, 1.0, "1", None])
def test_reject_noninteger_seed(seed: object) -> None:
    with pytest.raises(ValueError):
        new_game(2, seed)  # type: ignore[arg-type]


def test_tide_unique_winners_receive_reward_and_one_lantern_returns() -> None:
    original = scenario_game(2, 19)
    first = apply_action(original, 0, {"type": "deploy", "harbor": 0, "count": 2})
    assert original["turn"] == 0
    assert original["harbors"][0]["lanterns"] == [0, 0]
    assert first["scores"] == [0, 0]
    second = apply_action(first, 1, {"type": "deploy", "harbor": 1, "count": 1})
    assert second["scores"] == [original["forecast"][0][0], original["forecast"][0][1]]
    assert second["harbors"][0]["lanterns"] == [1, 0]
    assert second["harbors"][1]["lanterns"] == [0, 0]
    assert second["reserves"] == [6, 7]
    assert second["round"] == 2
    assert second["current_player"] == 1
    assert [harbor["reward"] for harbor in second["harbors"]] == second["forecast"][1]
    assert second["log"][-1]["details"]["awards"][2]["leaders"] == []
    assert_conservation(second)


def test_tied_control_scores_nothing_and_returns_no_lanterns() -> None:
    state = scenario_game(2, 2)
    state = apply_action(state, 0, {"type": "deploy", "harbor": 2, "count": 2})
    state = apply_action(state, 1, {"type": "deploy", "harbor": 2, "count": 2})
    assert state["scores"] == [0, 0]
    assert state["harbors"][2]["lanterns"] == [2, 2]
    assert state["reserves"] == [5, 5]
    assert state["log"][-1]["details"]["awards"][2]["winner"] is None
    assert state["log"][-1]["details"]["awards"][2]["leaders"] == [0, 1]


def test_ferry_and_bank_have_exact_resource_and_point_effects() -> None:
    state = scenario_game(3, 4)
    state = apply_action(state, 0, {"type": "deploy", "harbor": 0, "count": 2})
    state = apply_action(state, 1, {"type": "deploy", "harbor": 0, "count": 2})
    state = apply_action(state, 2, {"type": "deploy", "harbor": 0, "count": 2})
    assert state["current_player"] == 1
    moved = apply_action(state, 1, {"type": "ferry", "from": 0, "to": 1, "count": 2})
    assert moved["harbors"][0]["lanterns"] == [2, 0, 2]
    assert moved["harbors"][1]["lanterns"] == [0, 2, 0]
    assert moved["reserves"] == state["reserves"]
    banked = apply_action(moved, 2, {"type": "bank", "harbor": 0, "count": 1})
    assert banked["scores"] == [0, 0, 1]
    assert banked["reserves"] == [5, 5, 6]
    assert banked["harbors"][0]["lanterns"] == [2, 0, 1]
    assert_conservation(banked)


@pytest.mark.parametrize(
    "action",
    [
        {},
        {"type": "pass"},
        {"type": ["deploy"]},
        {"type": "deploy", "harbor": 0},
        {"type": "deploy", "harbor": 0, "count": 2, "score": 100},
        {"type": "deploy", "harbor": -1, "count": 1},
        {"type": "deploy", "harbor": 3, "count": 1},
        {"type": "deploy", "harbor": True, "count": 1},
        {"type": "deploy", "harbor": 0.0, "count": 1},
        {"type": "deploy", "harbor": "0", "count": 1},
        {"type": "deploy", "harbor": 0, "count": 0},
        {"type": "deploy", "harbor": 0, "count": 3},
        {"type": "deploy", "harbor": 0, "count": True},
        {"type": "deploy", "harbor": 0, "count": 1.0},
        {"type": "deploy", "harbor": 0, "count": "1"},
        {"type": "bank", "harbor": 0, "count": 1},
        {"type": "ferry", "from": 0, "to": 0, "count": 1},
        {"type": "ferry", "from": 0, "to": 1, "count": 1},
        None,
        [],
    ],
)
def test_invalid_moves_leave_input_unchanged_and_valid_recovery_works(action: object) -> None:
    state = scenario_game(2, 17)
    before = deepcopy(state)
    with pytest.raises(ValueError):
        apply_action(state, 0, action)  # type: ignore[arg-type]
    assert state == before
    recovered = apply_action(state, 0, {"type": "deploy", "harbor": 0, "count": 1})
    assert recovered["turn"] == 1


@pytest.mark.parametrize("player", [1, -1, 2, True, 0.0, "0"])
def test_wrong_or_invalid_seat_cannot_act(player: object) -> None:
    state = scenario_game(2, 7)
    with pytest.raises(ValueError):
        apply_action(state, player, legal_actions(state)[0])  # type: ignore[arg-type]
    assert state["turn"] == 0


def test_resource_bounds_and_same_harbor_ferry() -> None:
    state = scenario_game(2, 8)
    state["reserves"][0] = 0
    state["harbors"][0]["lanterns"][0] = 7
    with pytest.raises(ValueError, match="reserve"):
        apply_action(state, 0, {"type": "deploy", "harbor": 1, "count": 1})
    with pytest.raises(ValueError, match="different"):
        apply_action(state, 0, {"type": "ferry", "from": 0, "to": 0, "count": 1})
    assert {action["type"] for action in legal_actions(state)} == {"bank", "ferry"}
    assert_conservation(state)


@pytest.mark.parametrize("players", [2, 3, 4])
def test_complete_random_games_conserve_resources_and_rotate_every_seat_equally(
    players: int,
) -> None:
    rng = Random(871)
    for seed in range(12):
        state = new_game(players, seed)
        starters: list[int] = []
        turns: Counter[int] = Counter()
        while state["phase"] == "active":
            player = state["current_player"]
            if state["turn_in_round"] == 0:
                assert player == (state["starting_player"] + state["round"] - 1) % players
                starters.append(player)
            actions = legal_actions(state)
            assert len(actions) >= 2
            assert len(actions) == len({json.dumps(action, sort_keys=True) for action in actions})
            # Validate the advertised action set at meaningful changing states.
            for action in actions:
                assert_conservation(apply_action(state, player, action))
            snapshot = deepcopy(state)
            state = apply_action(state, player, rng.choice(actions))
            turns[player] += 1
            assert snapshot["turn"] + 1 == state["turn"]
            assert_conservation(state)
        assert state["turn"] == players * state["max_rounds"]
        assert turns == Counter({seat: state["max_rounds"] for seat in range(players)})
        assert Counter(starters) == Counter(
            {seat: state["max_rounds"] // players for seat in range(players)}
        )
        assert state["current_player"] is None
        assert (
            len([entry for entry in state["log"] if entry["kind"] == "tide"]) == state["max_rounds"]
        )
        assert state["winners"] == [
            seat for seat, score in enumerate(state["scores"]) if score == max(state["scores"])
        ]
        assert [entry["seq"] for entry in state["log"]] == list(range(len(state["log"])))
        assert json.loads(json.dumps(state)) == state
        assert legal_actions(state) == []
        with pytest.raises(ValueError, match="finished"):
            apply_action(state, 0, {"type": "deploy", "harbor": 0, "count": 1})
        with pytest.raises(ValueError, match="finished"):
            choose_bot_action(state)


def test_explicit_shared_victory() -> None:
    state = scenario_game(2, 12)
    state["round"] = state["max_rounds"]
    state["turn"] = (state["max_rounds"] - 1) * 2
    state["current_player"] = 1
    state = apply_action(state, 1, {"type": "deploy", "harbor": 0, "count": 2})
    state = apply_action(state, 0, {"type": "deploy", "harbor": 0, "count": 2})
    assert state["phase"] == "finished"
    assert state["scores"] == [0, 0]
    assert state["winners"] == [0, 1]
    assert "share victory" in state["log"][-1]["text"]


@pytest.mark.parametrize("players", [2, 3, 4])
def test_bot_deterministic_full_matches_and_deadline_finish(players: int) -> None:
    state = new_game(players, 781)
    first = choose_bot_action(state)
    assert first == choose_bot_action(state)
    assert first in legal_actions(state)
    state = apply_action(state, state["current_player"], first)
    before = deepcopy(state)
    finished = finish_game(state, "match_deadline")
    assert state == before
    assert finished == finish_game(state, "match_deadline")
    assert finished["phase"] == "finished"
    assert finished["finish_reason"] == "match_deadline"
    assert finished["turn"] == players * finished["max_rounds"]
    moves = [entry for entry in finished["log"] if entry["kind"] == "move"]
    assert Counter(entry["player"] for entry in moves) == Counter(
        {seat: finished["max_rounds"] for seat in range(players)}
    )
    assert all(entry["details"]["automatic"] for entry in moves[1:])
    assert "automatic" not in moves[0]["details"]
    assert finished == finish_game(finished, "second_call")
    assert_conservation(finished)


def test_bot_banks_surplus_instead_of_throwing_away_final_points() -> None:
    state = scenario_game(2, 3)
    state["round"] = state["max_rounds"]
    state["turn_in_round"] = 1
    state["current_player"] = 0
    state["reserves"][0] = 4
    state["harbors"][0]["lanterns"][0] = 3
    # All other harbors are already controlled by the rival with an unreachable
    # lead. Banking two preserves this harbor while securing two final points.
    state["reserves"][1] = 0
    state["harbors"][1]["lanterns"][1] = 3
    state["harbors"][2]["lanterns"][1] = 4
    state["scores"] = [10, 0]
    assert choose_bot_action(state) == {"type": "bank", "harbor": 0, "count": 2}


@pytest.mark.parametrize("players", [2, 3, 4])
def test_bot_ignores_narrative_history_without_mutating_public_state(players: int) -> None:
    state = new_game(players, 311)
    for _ in range(players * 2):
        state = apply_action(state, state["current_player"], legal_actions(state)[-1])
    before = deepcopy(state)
    without_history = deepcopy(state)
    without_history["log"] = []
    assert choose_bot_action(state) == choose_bot_action(without_history)
    assert state == before


@pytest.mark.parametrize("reason", ["", " ", None, "x" * 121])
def test_finish_requires_a_reason(reason: object) -> None:
    with pytest.raises(ValueError):
        finish_game(new_game(2, 1), reason)  # type: ignore[arg-type]
