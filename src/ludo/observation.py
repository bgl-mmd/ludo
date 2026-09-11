from ludo.coordinates import global_to_player, player_to_global
from ludo.model import CompetitionState, GameConfig, GameState, Observation
from ludo.rules import get_legal_actions


def get_observation(
    state: GameState, player: int, config: GameConfig, game_id: str = ""
) -> Observation:
    own_tokens = state.tokens[player]
    opponent_tokens = tuple(
        tuple(
            global_to_player(player_to_global(pos, opponent, config), player, config)
            for pos in state.tokens[opponent]
        )
        for opponent in range(config.num_players)
        if opponent != player
    )
    if state.state is not CompetitionState.NONE:
        game_state = state.state.value
    elif state.game_over:
        if state.winner == player:
            game_state = "END_YOU_WIN"
        elif state.winner is None:
            game_state = "END_EQUALS"
        else:
            game_state = "END_YOU_LOST"
    elif state.current_player == player:
        game_state = "WAIT_FOR_YOU"
    else:
        game_state = "WAIT_FOR_MOVE"
    return Observation(
        game_id=game_id,
        turn_number=state.turn_number,
        player_id=player,
        num_players=config.num_players,
        dice_value=state.dice_value,
        consecutive_sixes=state.consecutive_sixes,
        own_tokens=own_tokens,
        opponent_tokens=opponent_tokens,
        game_state=game_state,
        game_over=state.game_over,
        is_your_turn=state.current_player == player,
        legal_actions=get_legal_actions(state, config),
    )