import random
from typing import Callable

from ludo.model import Observation

BotFn = Callable[[Observation], int | None]


def make_random_bot(seed: int | None = None) -> BotFn:
    rng = random.Random(seed)

    def bot(obs: Observation) -> int | None:
        if not obs.legal_actions:
            return None
        return rng.choice(obs.legal_actions)

    return bot


def _score(action: int, obs: Observation) -> tuple[int, int, int]:
    pos = obs.own_tokens[action]
    dest = 1 if pos == 0 else pos + obs.dice_value
    captures = int(
        1 <= dest <= 40
        and any(dest == token for opponent in obs.opponent_tokens for token in opponent)
    )
    enters = int(pos == 0)
    return (captures, enters, pos)


def make_greedy_bot() -> BotFn:
    def bot(obs: Observation) -> int | None:
        legal = obs.legal_actions
        if not legal:
            return None
        return max(legal, key=lambda action: _score(action, obs))

    return bot