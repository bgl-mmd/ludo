from ludo.model import CompetitionState, GameConfig, GameState


def new_game(config: GameConfig, player_names: tuple[str, ...]) -> GameState:
    """Create a fresh game with given player names. Pure."""
    tokens = tuple(
        (0,) * config.tokens_per_player for _ in range(config.num_players)
    )
    return GameState(
        tokens=tokens,
        current_player=0,
        dice_value=None,
        consecutive_sixes=0,
        game_over=False,
        winner=None,
        error_count=0,
        turn_number=0,
        state=CompetitionState.NONE,
    )


def next_player(current: int, config: GameConfig) -> int:
    """Return the next player index (simple alternation). Pure."""
    return (current + 1) % config.num_players


def should_grant_extra_turn(
    dice_value: int,
    consecutive_sixes: int,
    config: GameConfig,
) -> bool:
    """Determine if the current player gets another turn. Pure.

    `consecutive_sixes` must already include the current 6.
    """
    return dice_value == 6 and consecutive_sixes < config.max_consecutive_sixes