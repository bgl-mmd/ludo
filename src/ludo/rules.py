from ludo.coordinates import global_to_player, player_to_global
from ludo.model import GameConfig, GameState

SAME_PLAYER = "SAME_PLAYER"
OPPONENT = "OPPONENT"


def get_occupant(
    state: GameState, player: int, position: int, config: GameConfig
) -> str | None:
    if position == 0:
        return None
    if position in state.tokens[player]:
        return SAME_PLAYER
    if position > config.board_size:
        return None
    global_pos = player_to_global(position, player, config)
    for opponent in range(config.num_players):
        if opponent == player:
            continue
        opp_pos = global_to_player(global_pos, opponent, config)
        if opp_pos in state.tokens[opponent]:
            return OPPONENT
    return None


def check_capture(
    state: GameState, player: int, destination: int, config: GameConfig
) -> int | None:
    if destination == 0 or destination > config.board_size:
        return None
    if destination in state.tokens[player]:
        return None
    global_pos = player_to_global(destination, player, config)
    for opponent in range(config.num_players):
        if opponent == player:
            continue
        opp_pos = global_to_player(global_pos, opponent, config)
        if opp_pos in state.tokens[opponent]:
            return opponent
    return None


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


def get_legal_actions(state: GameState, config: GameConfig) -> tuple[int, ...]:
    """Generate all legal token indices for the current player and dice.

    Reads `state.current_player` and `state.dice_value`. An empty tuple
    means "no valid move" (`Move(0)` / action `None`).
    """
    player = state.current_player
    if state.dice_value is None:
        return ()
    actions = []
    for token_index in range(len(state.tokens[player])):
        dest = compute_destination(state, player, token_index, config)
        if dest is None:
            continue
        if get_occupant(state, player, dest, config) == SAME_PLAYER:
            continue
        actions.append(token_index)
    return tuple(actions)


def is_valid_action(
    state: GameState, action: int | None, config: GameConfig
) -> bool:
    """Check if an action (token index) is legal given the current state.

    `None` ("no valid move") is valid exactly when no legal moves exist.
    """
    legal = get_legal_actions(state, config)
    if action is None:
        return not legal
    return action in legal


def is_game_over(state: GameState) -> bool:
    if state.game_over:
        return True
    config = GameConfig(
        num_players=len(state.tokens),
        tokens_per_player=len(state.tokens[0]),
    )
    return any(check_win(state, player, config) for player in range(config.num_players))