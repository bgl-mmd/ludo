from ludo.bots import make_greedy_bot, make_random_bot
from ludo.model import GameConfig, GameResult, MoveRecord
from ludo.simulation import run_simulation

CONFIG = GameConfig()


def _random_bots() -> tuple:
    return (make_random_bot(seed=1), make_random_bot(seed=2))


def _mixed_bots() -> tuple:
    return (make_random_bot(seed=3), make_greedy_bot())


def _greedy_bots() -> tuple:
    return (make_greedy_bot(), make_greedy_bot())


def _greedy_random_bots() -> tuple:
    return (make_greedy_bot(), make_random_bot(seed=5))


def _bot_factories() -> tuple:
    return (_random_bots, _mixed_bots, _greedy_bots, _greedy_random_bots)


class TestSimulation:
    def test_game_completes_with_random_bots(self) -> None:
        result, log = run_simulation(_random_bots(), CONFIG, seed=42)
        assert isinstance(result, GameResult)
        assert isinstance(log, tuple)
        assert len(log) > 0
        assert all(isinstance(record, MoveRecord) for record in log)

    def test_game_always_has_a_winner(self) -> None:
        for seed in range(5):
            for factory in _bot_factories():
                result, _ = run_simulation(factory(), CONFIG, seed=seed)
                assert result.winner is not None
                assert result.winner in (0, 1)

    def test_game_deterministic_with_same_seed(self) -> None:
        for factory in _bot_factories():
            first = run_simulation(factory(), CONFIG, seed=42)
            second = run_simulation(factory(), CONFIG, seed=42)
            assert first == second

    def test_game_records_all_moves(self) -> None:
        result, log = run_simulation(_mixed_bots(), CONFIG, seed=42)
        assert len(log) == result.turn_count
        assert log[0].turn == 0
        for index, record in enumerate(log):
            assert isinstance(record, MoveRecord)
            assert record.turn == index
            assert 0 <= record.player < CONFIG.num_players
        for current, following in zip(log, log[1:]):
            assert following.turn == current.turn + 1
            if current.is_extra_turn:
                assert following.player == current.player
            else:
                assert following.player == (current.player + 1) % CONFIG.num_players

    def test_game_no_errors_with_valid_bots(self) -> None:
        for factory in (_random_bots, _mixed_bots):
            result, log = run_simulation(factory(), CONFIG, seed=42)
            assert result.error_count == 0
            assert all(not record.error for record in log)

    def test_result_consistent_with_log_and_terminal_state(self) -> None:
        result, log = run_simulation(_mixed_bots(), CONFIG, seed=42)
        assert log[-1].player == result.winner
        assert log[-1].action is not None
        assert log[-1].error is False
        assert result.winner in (0, 1)