import http.server
import logging
import threading
from urllib.parse import parse_qs, urlparse

from competition.client import CompetitionError, get_board
from competition.parsing import parse_result
from competition.runner import END_STATES, _player_id, handle_callback
from ludo.bots import BotFn
from ludo.model import GameResult

logger = logging.getLogger(__name__)


def process_callback(
    state_value: str | None,
    *,
    bot: BotFn,
    base_url: str,
    token: str,
    username: str,
    on_game_over=None,
) -> int:
    """Handle a single callback state and return the HTTP status code.

    WAIT_FOR_YOU fetches the board, computes and sends the move, then
    acknowledges (move-then-respond). Terminal states signal game over via
    on_game_over(result). Other states are acknowledged without action.
    """
    if state_value is None:
        return 400
    if state_value == "WAIT_FOR_YOU":
        handle_callback(state_value, bot, base_url, token, username)
        return 200
    if state_value in END_STATES:
        board = get_board(base_url, token)
        player_id = _player_id(board, username)
        result = parse_result(board, player_id)
        logger.info("game over: winner=p%s", result.winner)
        if on_game_over is not None:
            on_game_over(result)
        return 200
    logger.info("ignoring callback state: %s", state_value)
    return 200


def _make_handler(bot: BotFn, base_url: str, token: str, username: str, on_game_over, game_over):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length:
                self.rfile.read(length)
            state_value = parse_qs(urlparse(self.path).query).get("gamestate", [None])[0]
            logger.info("callback received: state=%s", state_value)
            try:
                status = process_callback(
                    state_value,
                    bot=bot,
                    base_url=base_url,
                    token=token,
                    username=username,
                    on_game_over=on_game_over,
                )
            except CompetitionError as error:
                logger.error("callback handling failed: state=%s error=%s", state_value, error)
                status = 500
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()
            if status == 200 and game_over.is_set():
                threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, fmt: str, *args) -> None:
            logger.info("callback: %s", fmt % args)

    return Handler


def run_callback_server(
    host: str,
    port: int,
    bot: BotFn,
    base_url: str,
    token: str,
    username: str,
) -> GameResult:
    """Serve the callback endpoint until the game ends, then return the result."""
    box: dict = {"result": None}
    game_over = threading.Event()

    def on_game_over(result) -> None:
        box["result"] = result
        game_over.set()

    handler = _make_handler(bot, base_url, token, username, on_game_over, game_over)
    httpd = http.server.ThreadingHTTPServer((host, port), handler)
    logger.info("callback server listening on %s:%s", host, port)
    httpd.serve_forever()
    httpd.server_close()
    return box["result"]