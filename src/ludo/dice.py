import random
from dataclasses import replace

from ludo.model import GameState


def create_rng(seed: int | None = None) -> random.Random:
    return random.Random(seed)


def roll_dice(state: GameState, rng: random.Random) -> tuple[GameState, int]:
    value = rng.randint(1, 6)
    return replace(state, dice_value=value), value