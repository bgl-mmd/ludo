import json
from dataclasses import replace

from ludo.bots import make_greedy_bot, make_random_bot
from ludo.dice import create_rng, roll_dice
from ludo.engine import apply_action, get_result, new_game
from ludo.model import GameConfig, MoveRecord
from ludo.observation import get_observation
from ludo.rules import is_game_over
from ludo.simulation import (
    export_history,
    import_history,
    run_simulation,
    step_through,
)

CONFIG = GameConfig()

HAND_BUILT_LOG = (
    MoveRecord(
        turn=0,
        player=0,
        action=0,
        dice_value=6,
        destination=1,
        captured=None,
        is_extra_turn=True,
        error=False,
    ),
    MoveRecord(
        turn=1,
        player=0,
        action=None,
        dice_value=3,
        destination=0,
        captured=None,
        is_extra_turn=False,
        error=False,
    ),
    MoveRecord(
        turn=2,
        player=1,
        action=1,
        dice_value=2,
        destination=5,
        captured=0,
        is_extra_turn=False,
        error=False,
    ),
    MoveRecord(
        turn=3,
        player=1,
        action=None,
        dice_value=4,
        destination=0,
        captured=None,
        is_extra_turn=False,
        error=True,
    ),
)


def _fresh_bots() -> tuple:
    return (make_random_bot(seed=1), make_random_bot(seed=2))


def _fresh_mixed_bots() -> tuple:
    return (make_random_bot(seed=3), make_greedy_bot())


def _run_full(bots: tuple, config: GameConfig, seed: int | None) -> tuple:
    rng = create_rng(seed)
    names = tuple(b.__name__ for b in bots)
    state = new_game(config, names)
    game_id = f"game-{seed}" if seed is not None else "game"
    log: tuple[MoveRecord, ...] = ()
    while not is_game_over(state):
        state, _ = roll_dice(state, rng)
        player = state.current_player
        obs = get_observation(state, player, config, game_id=game_id)
        action = bots[player](obs)
        state, record = apply_action(state, action, config)
        log = (*log, record)
    result = get_result(state, names)
    return result, log, state


def _replay(log: tuple[MoveRecord, ...], config: GameConfig) -> object:
    names = tuple(f"p{i}" for i in range(config.num_players))
    state = new_game(config, names)
    for record in log:
        state, _ = apply_action(
            replace(
                state,
                dice_value=record.dice_value,
                current_player=record.player,
            ),
            record.action,
            config,
        )
    return state


class TestHistoryExportImport:
    def test_export_import_roundtrip(self) -> None:
        for seed in (1, 2, 3, 42, 7):
            for bots in (_fresh_bots(), _fresh_mixed_bots()):
                _, log = run_simulation(bots, CONFIG, seed=seed)
                exported = export_history(log)
                json.dumps(exported)
                assert import_history(exported) == log

    def test_export_import_roundtrip_hand_built_log(self) -> None:
        exported = export_history(HAND_BUILT_LOG)
        json.dumps(exported)
        assert import_history(exported) == HAND_BUILT_LOG

    def test_step_through_iterates_records_in_order(self) -> None:
        _, log = run_simulation(_fresh_bots(), CONFIG, seed=42)
        assert list(step_through(log)) == list(log)
        assert tuple(step_through(HAND_BUILT_LOG)) == HAND_BUILT_LOG


class TestReplay:
    def test_replay_matches_original_game(self) -> None:
        for seed in (1, 2, 3, 42, 7):
            for factory in (_fresh_bots, _fresh_mixed_bots):
                result, log = run_simulation(factory(), CONFIG, seed=seed)
                final_state = _replay(log, CONFIG)
                assert is_game_over(final_state)
                assert final_state.winner == result.winner
                result_check, log_check, original_final = _run_full(
                    factory(), CONFIG, seed
                )
                assert log_check == log
                assert result_check == result
                assert final_state.tokens == original_final.tokens

    def test_deterministic_replay(self) -> None:
        for seed in (1, 2, 3, 42, 7):
            for factory in (_fresh_bots, _fresh_mixed_bots):
                _, log = run_simulation(factory(), CONFIG, seed=seed)
                first = _replay(log, CONFIG)
                second = _replay(log, CONFIG)
                assert first == second
                assert first.tokens == second.tokens

    def test_deterministic_replay_hand_built_log(self) -> None:
        first = _replay(HAND_BUILT_LOG, CONFIG)
        second = _replay(HAND_BUILT_LOG, CONFIG)
        assert first == second