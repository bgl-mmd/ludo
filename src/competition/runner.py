import time

from competition.client import get_board, login, make_move
from competition.parsing import (
    action_to_address,
    parse_board,
    parse_observation,
    parse_result,
)
from ludo.bots import BotFn
from ludo.model import GameConfig, GameResult

END_STATES = ("END_YOU_WIN", "END_YOU_LOST", "END_EQUALS")
POLL_INTERVAL = 1.0


def run_competition(
    bot: BotFn,
    base_url: str,
    game_id: str,
    username: str,
    password: str,
    config: GameConfig,
    poll_interval: float = POLL_INTERVAL,
) -> GameResult:
    """Run a complete game against the server.

    The config parameter is kept for API compatibility with
    run_simulation but is unused: the server owns the game rules.
    Polls the board every poll_interval seconds to limit server traffic.
    """
    token = login(base_url, game_id, username, password)
    board = get_board(base_url, token)
    while board.state in ("NONE", "WAIT_FOR_START"):
        time.sleep(poll_interval)
        board = get_board(base_url, token)
    while board.state not in END_STATES:
        if board.state == "WAIT_FOR_YOU":
            obs = parse_observation(board)
            action = bot(obs) if obs.legal_actions else None
            address = action_to_address(obs.own_tokens, action)
            make_move(base_url, token, address)
        time.sleep(poll_interval)
        board = get_board(base_url, token)
    return parse_result(board)


def handle_callback(state: str, bot: BotFn, base_url: str, token: str) -> None:
    if state == "WAIT_FOR_YOU":
        board = get_board(base_url, token)
        obs = parse_observation(board)
        action = bot(obs) if obs.legal_actions else None
        address = action_to_address(obs.own_tokens, action)
        make_move(base_url, token, address)
    elif state in END_STATES:
        pass


def replace_callback_state(callback_url: str, state: str) -> str:
    return callback_url.replace("{0}", state)