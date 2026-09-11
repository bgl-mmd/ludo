import logging
import time

from competition.client import CompetitionError, get_board, login, make_move
from competition.parsing import (
    action_to_address,
    parse_observation,
    parse_result,
)
from ludo.bots import BotFn
from ludo.model import GameConfig, GameResult

END_STATES = ("END_YOU_WIN", "END_YOU_LOST", "END_EQUALS")
POLL_INTERVAL = 1.0

logger = logging.getLogger(__name__)


def _player_id(board, username: str) -> int:
    for index, user in enumerate(board.users):
        if user.name == username:
            return index
    raise CompetitionError(
        f"username {username!r} not found among board users {[u.name for u in board.users]}"
    )


def _fetch_board(base_url: str, token: str):
    board = get_board(base_url, token)
    logger.info(
        "gamestate received: game_id=%s state=%s dice=%s users=%s",
        board.game_id,
        board.state,
        board.dice,
        [(user.name, user.tokens) for user in board.users],
    )
    return board


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
    try:
        board = _fetch_board(base_url, token)
    except CompetitionError as error:
        logger.error("failed to fetch initial board: game_id=%s error=%s", game_id, error)
        raise
    player_id = _player_id(board, username)
    while board.state in ("NONE", "WAIT_FOR_START"):
        time.sleep(poll_interval)
        try:
            board = _fetch_board(base_url, token)
        except CompetitionError as error:
            logger.error(
                "failed to poll board: game_id=%s last_board=%s error=%s",
                game_id,
                board,
                error,
            )
            raise
    while board.state not in END_STATES:
        if board.state == "WAIT_FOR_YOU":
            obs = parse_observation(board, player_id)
            action = bot(obs) if obs.legal_actions else None
            address = action_to_address(obs.own_tokens, action)
            logger.info("making move: address=%s", address)
            try:
                make_move(base_url, token, address)
            except CompetitionError as error:
                logger.error(
                    "failed to make move: address=%s last_board=%s error=%s",
                    address,
                    board,
                    error,
                )
                raise
        time.sleep(poll_interval)
        try:
            board = _fetch_board(base_url, token)
        except CompetitionError as error:
            logger.error(
                "failed to poll board: game_id=%s last_board=%s error=%s",
                game_id,
                board,
                error,
            )
            raise
    return parse_result(board, player_id)


def handle_callback(state: str, bot: BotFn, base_url: str, token: str, username: str) -> None:
    if state == "WAIT_FOR_YOU":
        try:
            board = _fetch_board(base_url, token)
        except CompetitionError as error:
            logger.error("callback failed to fetch board: error=%s", error)
            raise
        player_id = _player_id(board, username)
        obs = parse_observation(board, player_id)
        action = bot(obs) if obs.legal_actions else None
        address = action_to_address(obs.own_tokens, action)
        logger.info("making move: address=%s", address)
        try:
            make_move(base_url, token, address)
        except CompetitionError as error:
            logger.error(
                "callback failed to make move: address=%s last_board=%s error=%s",
                address,
                board,
                error,
            )
            raise
    elif state in END_STATES:
        pass


def replace_callback_state(callback_url: str, state: str) -> str:
    return callback_url.replace("{0}", state)