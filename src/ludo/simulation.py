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