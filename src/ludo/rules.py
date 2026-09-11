from ludo.model import GameConfig, GameState


def compute_destination(
    state: GameState, player: int, token_index: int, config: GameConfig
) -> int | None:
    pos = state.tokens[player][token_index]
    dice = state.dice_value
    if dice is None:
        return None
    if pos == 0:
        if dice == 6:
            return 1
        return None
    dest = pos + dice
    if dest > config.board_size + config.home_stretch_size:
        return None
    return dest