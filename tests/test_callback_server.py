import http.client
import http.server
import threading
from unittest import mock

from competition.callback_server import _make_handler, process_callback
from competition.client import CompetitionError
from competition.parsing import parse_board
from ludo.model import GameResult

BASE_URL = "https://rbc.sysx.ir"
GAME_ID = "game-room-1"
TOKEN = "token-123"
USERNAME = "RayanBotTeam1"


def _board(state: str = "END_YOU_WIN"):
    return parse_board(
        {
            "gameID": GAME_ID,
            "state": state,
            "dice": 6,
            "users": [
                {"name": "RayanBotTeam1", "begin": 1, "end": 40, "tokens": [40, 41, 42, 43]},
                {"name": "RayanBotTeam2", "begin": 21, "end": 20, "tokens": [0, 0, 0, 0]},
            ],
        }
    )


def _bot(obs):
    return None


def _start_server(handler):
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    return httpd, thread, port


def _post(port: int, path: str) -> int:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request("POST", path)
        return conn.getresponse().status
    finally:
        conn.close()


class TestProcessCallback:
    def test_wait_for_you_calls_handle_callback_and_returns_200(self) -> None:
        with mock.patch("competition.callback_server.handle_callback") as mock_handle:
            status = process_callback(
                "WAIT_FOR_YOU", bot=_bot, base_url=BASE_URL, token=TOKEN, username=USERNAME
            )
        assert status == 200
        mock_handle.assert_called_once_with("WAIT_FOR_YOU", _bot, BASE_URL, TOKEN, USERNAME)

    def test_non_turn_state_acks_without_moving(self) -> None:
        with mock.patch("competition.callback_server.handle_callback") as mock_handle:
            for state in ("NONE", "WAIT_FOR_START", "WAIT_FOR_MOVE"):
                status = process_callback(
                    state, bot=_bot, base_url=BASE_URL, token=TOKEN, username=USERNAME
                )
                assert status == 200
        mock_handle.assert_not_called()

    def test_terminal_state_signals_game_over(self) -> None:
        result = GameResult(winner=0, turn_count=0, error_count=0)
        with mock.patch("competition.callback_server.get_board", return_value=_board()), mock.patch(
            "competition.callback_server.parse_result", return_value=result
        ) as mock_parse:
            box = {}
            status = process_callback(
                "END_YOU_WIN",
                bot=_bot,
                base_url=BASE_URL,
                token=TOKEN,
                username=USERNAME,
                on_game_over=lambda r: box.setdefault("result", r),
            )
        assert status == 200
        assert box["result"].winner == 0
        mock_parse.assert_called_once()

    def test_missing_gamestate_returns_400(self) -> None:
        status = process_callback(None, bot=_bot, base_url=BASE_URL, token=TOKEN, username=USERNAME)
        assert status == 400


class TestCallbackServer:
    def test_end_state_returns_200_and_signals_game_over(self) -> None:
        game_over = threading.Event()
        box = {}
        handler = _make_handler(
            _bot,
            BASE_URL,
            TOKEN,
            USERNAME,
            lambda r: (box.setdefault("result", r), game_over.set()),
            game_over,
        )
        with mock.patch("competition.callback_server.get_board", return_value=_board()):
            httpd, thread, port = _start_server(handler)
            try:
                status = _post(port, "/?gamestate=END_YOU_WIN")
            finally:
                httpd.shutdown()
                thread.join()
        assert status == 200
        assert game_over.is_set()
        assert box["result"].winner == 0

    def test_wait_for_you_returns_500_on_competition_error(self) -> None:
        game_over = threading.Event()
        handler = _make_handler(_bot, BASE_URL, TOKEN, USERNAME, lambda r: None, game_over)
        with mock.patch(
            "competition.callback_server.handle_callback",
            side_effect=CompetitionError("HTTP 500 from /api/v1/Move: Server Error"),
        ):
            httpd, thread, port = _start_server(handler)
            try:
                status = _post(port, "/?gamestate=WAIT_FOR_YOU")
            finally:
                httpd.shutdown()
                thread.join()
        assert status == 500
        assert not game_over.is_set()