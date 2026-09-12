"""Run Ludo games locally with the example bots.

Usage:
    PYTHONPATH=src python3 scripts/play.py                    # one greedy vs random game
    PYTHONPATH=src python3 scripts/play.py --bot0 greedy --bot1 greedy
    PYTHONPATH=src python3 scripts/play.py --bot0 mcts --bot1 random
    PYTHONPATH=src python3 scripts/play.py --batch --games 50 --workers 4 --seed 0
"""

import argparse
import functools

from ludo.bots import make_greedy_bot, make_mcts_bot, make_random_bot
from ludo.model import GameConfig
from ludo.simulation import aggregate, run_batch, run_simulation


def random_factory(player: int):
    return make_random_bot(seed=1000 + player)


def greedy_factory(player: int):
    return make_greedy_bot()


def mcts_factory(player: int, iterations: int = 200):
    return make_mcts_bot(iterations=iterations, seed=1000 + player)


def _factory(name: str, iterations: int):
    if name == "random":
        return random_factory
    if name == "greedy":
        return greedy_factory
    return functools.partial(mcts_factory, iterations=iterations)


def play_one(config, bot0, bot1, iterations, seed):
    bots = (_factory(bot0, iterations)(0), _factory(bot1, iterations)(1))
    result, log = run_simulation(bots, config, seed=seed)
    print(
        f"game: winner=p{result.winner} turns={result.turn_count} "
        f"errors={result.error_count} moves={len(log)}"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bot0", choices=FACTORIES, default="greedy")
    parser.add_argument("--bot1", choices=FACTORIES, default="random")
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--players", type=int, default=2)
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--games", type=int, default=50)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    config = GameConfig(num_players=args.players)

    if not args.batch:
        play_one(config, args.bot0, args.bot1, args.iterations, args.seed)
        return

    factories = (_factory(args.bot0, args.iterations), _factory(args.bot1, args.iterations))
    seeds = tuple(range(args.seed, args.seed + args.games))
    results = run_batch(factories, config, seeds, num_workers=args.workers)
    stats = aggregate(results)
    print(f"games={stats['games']} draws={stats['draws']}")
    print(f"win_rate={stats['win_rate']}")
    print(f"avg_turns={stats['avg_turns']:.1f} avg_errors={stats['avg_errors']:.2f}")


FACTORIES = {"random": random_factory, "greedy": greedy_factory, "mcts": mcts_factory}


if __name__ == "__main__":
    main()
