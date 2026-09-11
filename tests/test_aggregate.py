from ludo.model import GameResult
from ludo.simulation import aggregate


def _result(winner: int | None, turn_count: int, error_count: int) -> GameResult:
    return GameResult(winner=winner, turn_count=turn_count, error_count=error_count)


class TestAggregate:
    def test_statistics_correctly_aggregate(self) -> None:
        results = (
            _result(0, 50, 0),
            _result(0, 60, 1),
            _result(0, 40, 2),
            _result(0, 70, 0),
            _result(0, 55, 1),
            _result(0, 65, 0),
            _result(1, 80, 1),
            _result(1, 45, 2),
            _result(1, 75, 0),
            _result(None, 100, 5),
        )
        stats = aggregate(results)
        assert stats["games"] == 10
        assert stats["win_rate"] == {0: 0.6, 1: 0.3}
        assert stats["draws"] == 1
        assert stats["avg_turns"] == 64.0
        assert stats["avg_errors"] == 1.2

    def test_empty_input_returns_zero_values(self) -> None:
        stats = aggregate(())
        assert stats["games"] == 0
        assert stats["win_rate"] == {}
        assert stats["draws"] == 0
        assert stats["avg_turns"] == 0
        assert stats["avg_errors"] == 0

    def test_single_result_win_rate_one(self) -> None:
        stats = aggregate((_result(1, 30, 0),))
        assert stats["games"] == 1
        assert stats["win_rate"] == {1: 1.0}
        assert stats["draws"] == 0
        assert stats["avg_turns"] == 30.0
        assert stats["avg_errors"] == 0.0

    def test_all_draws_empty_win_rate(self) -> None:
        results = (_result(None, 50, 1), _result(None, 60, 2), _result(None, 70, 3))
        stats = aggregate(results)
        assert stats["games"] == 3
        assert stats["win_rate"] == {}
        assert stats["draws"] == 3
        assert stats["avg_turns"] == 60.0
        assert stats["avg_errors"] == 2.0