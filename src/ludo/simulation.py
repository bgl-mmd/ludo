import functools
import multiprocessing
from typing import Callable

from dataclasses import asdict

from ludo.bots import BotFn
from ludo.dice import create_rng, roll_dice
from ludo.engine import apply_action, get_result, new_game
from ludo.model import GameConfig, GameResult, MoveRecord
from ludo.observation import get_observation
from ludo.rules import is_game_over


def run_simulation(
    bots: tuple[BotFn, ...],
    config: GameConfig,
    seed: int | None = None,
) -> tuple[GameResult, tuple[MoveRecord, ...]]:
    rng = create_rng(seed)
    names = tuple(getattr(b, "__name__", "bot") for b in bots)
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
    return result, log


def export_history(log: tuple[MoveRecord, ...]) -> dict:
    return {"records": [asdict(record) for record in log]}


def import_history(data: dict) -> tuple[MoveRecord, ...]:
    return tuple(MoveRecord(**record) for record in data["records"])


def step_through(log: tuple[MoveRecord, ...]):
    return iter(log)


def aggregate(results: tuple[GameResult, ...]) -> dict:
    n = len(results)
    wins: dict[int, int] = {}
    draws = 0
    total_turns = 0
    total_errors = 0

    for r in results:
        if r.winner is not None:
            wins[r.winner] = wins.get(r.winner, 0) + 1
        else:
            draws += 1
        total_turns += r.turn_count
        total_errors += r.error_count

    if n == 0:
        return {
            "games": 0,
            "win_rate": {},
            "draws": 0,
            "avg_turns": 0,
            "avg_errors": 0,
        }

    return {
        "games": n,
        "win_rate": {k: v / n for k, v in wins.items()},
        "draws": draws,
        "avg_turns": total_turns / n,
        "avg_errors": total_errors / n,
    }


def _run_one(
    bot_factories: tuple[Callable[[int], BotFn], ...],
    config: GameConfig,
    seed: int,
) -> GameResult:
    bots = tuple(factory(index) for index, factory in enumerate(bot_factories))
    return run_simulation(bots, config, seed)[0]


def run_batch(
    bot_factories: tuple[Callable[[int], BotFn], ...],
    config: GameConfig,
    seeds: tuple[int, ...],
    num_workers: int = 1,
) -> tuple[GameResult, ...]:
    if num_workers == 1:
        return tuple(_run_one(bot_factories, config, seed) for seed in seeds)
    with multiprocessing.Pool(num_workers) as pool:
        return tuple(
            pool.map(functools.partial(_run_one, bot_factories, config), seeds)
        )