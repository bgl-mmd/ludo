from ludo.bots import BotFn, make_greedy_bot, make_random_bot
from ludo.model import GameConfig, GameResult
from ludo.simulation import run_batch

CONFIG = GameConfig()
SEEDS = (1, 2, 3, 4)


def _random_factory(player: int) -> BotFn:
    return make_random_bot(seed=100 + player)


def _greedy_factory(player: int) -> BotFn:
    return make_greedy_bot()


class TestBatchSimulation:
    def test_batch_simulation_completes(self) -> None:
        factories = (_random_factory, _greedy_factory)
        results = run_batch(factories, CONFIG, SEEDS, num_workers=1)
        assert isinstance(results, tuple)
        assert len(results) == len(SEEDS)
        for result in results:
            assert isinstance(result, GameResult)
            assert result.winner in (0, 1)

    def test_parallel_simulation_same_results(self) -> None:
        factories = (_random_factory, _greedy_factory)
        serial = run_batch(factories, CONFIG, SEEDS, num_workers=1)
        parallel = run_batch(factories, CONFIG, SEEDS, num_workers=2)
        assert serial == parallel