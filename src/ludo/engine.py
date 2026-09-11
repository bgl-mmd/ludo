from ludo.model import GameConfig


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