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


def check_win(state: GameState, player: int, config: GameConfig) -> bool:
    start = config.board_size + 1
    end = config.board_size + config.home_stretch_size
    return all(start <= pos <= end for pos in state.tokens[player])


def is_game_over(state: GameState) -> bool:
    if state.game_over:
        return True
    config = GameConfig(
        num_players=len(state.tokens),
        tokens_per_player=len(state.tokens[0]),
    )
    return any(check_win(state, player, config) for player in range(config.num_players))