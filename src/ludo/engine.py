from dataclasses import replace

from ludo import rules
from ludo.coordinates import global_to_player, player_to_global
from ludo.model import (
    CompetitionState,
    GameConfig,
    GameResult,
    GameState,
    MoveRecord,
)


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


def apply_action(
    state: GameState,
    action: int | None,
    config: GameConfig,
) -> tuple[GameState, MoveRecord]:
    """Apply an action (token index, or None for no valid move).

    Returns (new_state, move_record). Pure — never mutates the input.
    """
    player = state.current_player
    dice = state.dice_value if state.dice_value is not None else 0

    if state.game_over or not rules.is_valid_action(state, action, config):
        new_state = replace(
            state,
            current_player=next_player(player, config),
            dice_value=None,
            consecutive_sixes=0,
            error_count=state.error_count + 1,
            turn_number=state.turn_number + 1,
        )
        record = MoveRecord(
            turn=state.turn_number,
            player=player,
            action=action,
            dice_value=dice,
            destination=0,
            captured=None,
            is_extra_turn=False,
            error=True,
        )
        return new_state, record

    if action is None:
        new_state = replace(
            state,
            current_player=next_player(player, config),
            dice_value=None,
            consecutive_sixes=0,
            turn_number=state.turn_number + 1,
        )
        record = MoveRecord(
            turn=state.turn_number,
            player=player,
            action=None,
            dice_value=dice,
            destination=0,
            captured=None,
            is_extra_turn=False,
            error=False,
        )
        return new_state, record

    destination = rules.compute_destination(state, player, action, config)
    if destination is None:
        destination = 0
    captured = rules.check_capture(state, player, destination, config)

    new_tokens_list = list(state.tokens)
    player_tokens = list(state.tokens[player])
    player_tokens[action] = destination
    new_tokens_list[player] = tuple(player_tokens)

    if captured is not None:
        opponent_tokens = list(state.tokens[captured])
        global_pos = player_to_global(destination, player, config)
        opponent_rel = global_to_player(global_pos, captured, config)
        for index, pos in enumerate(opponent_tokens):
            if pos == opponent_rel:
                opponent_tokens[index] = 0
                break
        new_tokens_list[captured] = tuple(opponent_tokens)

    moved = replace(state, tokens=tuple(new_tokens_list))
    won = rules.check_win(moved, player, config)

    consecutive = state.consecutive_sixes
    if dice == 6:
        consecutive += 1

    if won:
        new_state = replace(
            moved,
            game_over=True,
            winner=player,
            dice_value=None,
            turn_number=state.turn_number + 1,
        )
        is_extra_turn = False
    elif should_grant_extra_turn(dice, consecutive, config):
        new_state = replace(
            moved,
            dice_value=None,
            consecutive_sixes=consecutive,
            turn_number=state.turn_number + 1,
        )
        is_extra_turn = True
    else:
        new_state = replace(
            moved,
            current_player=next_player(player, config),
            dice_value=None,
            consecutive_sixes=0,
            turn_number=state.turn_number + 1,
        )
        is_extra_turn = False

    record = MoveRecord(
        turn=state.turn_number,
        player=player,
        action=action,
        dice_value=dice,
        destination=destination,
        captured=captured,
        is_extra_turn=is_extra_turn,
        error=False,
    )
    return new_state, record


def get_result(state: GameState, player_names: tuple[str, ...]) -> GameResult:
    """Return the final result of a completed game. Pure."""
    return GameResult(
        winner=state.winner,
        turn_count=state.turn_number,
        error_count=state.error_count,
    )