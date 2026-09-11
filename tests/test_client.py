import json
import logging
import urllib.error
import urllib.request
from unittest import mock

import pytest

from competition.client import CompetitionError, get_board, login, make_move
from competition.parsing import BoardState

BOARD_JSON = {
    "gameID": "game-room-1",
    "state": "WAIT_FOR_YOU",
    "timestamp": "12345ABCD",
    "dice": 6,
    "users": [
        {"name": "RayanBotTeam1", "begin": 1, "end": 40, "tokens": [14, 0, 41, 43]},
        {"name": "RayanBotTeam2", "begin": 21, "end": 20, "tokens": [0, 42, 20, 0]},
    ],
}

TOKEN = "ead0612d-6fb6-4043-a01a-b58a08638aa8"


class FakeResponse:
    def __init__(self, payload: bytes = b"", status: int = 200) -> None:
        self._payload = payload
        self.status = status

    def read(self) -> bytes:
        return self._payload


def _captured_request(mock_urlopen) -> urllib.request.Request:
    return mock_urlopen.call_args[0][0]


def _request_body(request: urllib.request.Request) -> dict:
    return json.loads(request.data.decode("utf-8"))


def _header(request: urllib.request.Request, name: str) -> str | None:
    for key, value in request.headers.items():
        if key.lower() == name.lower():
            return value
    return None


class TestLoginRequestFormat:
    def test_login_request_format(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(json.dumps({"token": TOKEN}).encode())
            result = login(
                "https://rbc.sysx.ir",
                "game-room-1",
                "RayanBotTeam",
                "123",
                callback_url="http://myBot.local/gamestatecallback?gamestate={0}",
            )
        request = _captured_request(mock_urlopen)
        assert request.full_url == "https://rbc.sysx.ir/api/v1/Login"
        assert request.get_method() == "POST"
        assert _header(request, "Content-Type") == "application/json"
        assert _header(request, "Accept") == "application/json"
        body = _request_body(request)
        assert body == {
            "gameID": "game-room-1",
            "engine": "ludo",
            "userName": "RayanBotTeam",
            "password": "123",
            "callbackUrl": "http://myBot.local/gamestatecallback?gamestate={0}",
        }
        assert result == TOKEN

    def test_login_callback_url_absent_when_none(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(json.dumps({"token": TOKEN}).encode())
            login("https://rbc.sysx.ir", "game-room-1", "RayanBotTeam", "123")
        body = _request_body(_captured_request(mock_urlopen))
        assert body == {
            "gameID": "game-room-1",
            "engine": "ludo",
            "userName": "RayanBotTeam",
            "password": "123",
        }
        assert "callbackUrl" not in body

    def test_login_response_parsing(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(json.dumps({"token": TOKEN}).encode())
            assert login("https://rbc.sysx.ir", "game-room-1", "team", "pw") == TOKEN


class TestBoardRequestFormat:
    def test_board_request_format(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(json.dumps(BOARD_JSON).encode())
            board = get_board("https://rbc.sysx.ir", TOKEN)
        request = _captured_request(mock_urlopen)
        assert request.full_url == "https://rbc.sysx.ir/api/v1/Board"
        assert request.get_method() == "POST"
        assert _header(request, "Content-Type") == "application/json"
        assert _header(request, "Accept") == "application/json"
        assert _request_body(request) == {"token": TOKEN, "model": "ludo"}
        assert isinstance(board, BoardState)
        assert board.game_id == "game-room-1"
        assert board.state == "WAIT_FOR_YOU"
        assert board.dice == 6
        assert board.users[0].tokens == (14, 0, 41, 43)

    def test_board_response_parsing_through_parse_board(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(json.dumps(BOARD_JSON).encode())
            board = get_board("https://rbc.sysx.ir", TOKEN)
        assert isinstance(board, BoardState)
        assert board.users[1].name == "RayanBotTeam2"
        assert board.users[1].tokens == (0, 42, 20, 0)


class TestMoveRequestFormat:
    def test_move_request_format_int_address(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(b"")
            make_move("https://rbc.sysx.ir", TOKEN, 14)
        request = _captured_request(mock_urlopen)
        assert request.full_url == "https://rbc.sysx.ir/api/v1/Move"
        assert request.get_method() == "POST"
        assert _header(request, "Content-Type") == "application/json"
        assert _header(request, "Accept") == "application/json"
        body = _request_body(request)
        assert body["token"] == TOKEN
        assert body["address"] == 14
        assert isinstance(body["address"], int)

    def test_move_0_for_no_valid_move(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(b"")
            make_move("https://rbc.sysx.ir", TOKEN, "0")
        body = _request_body(_captured_request(mock_urlopen))
        assert body["address"] == "0"
        assert isinstance(body["address"], str)

    def test_move_address_passed_through_unchanged(self) -> None:
        for address in (0, 40, "0"):
            with mock.patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.return_value = FakeResponse(b"")
                make_move("https://rbc.sysx.ir", TOKEN, address)
            assert _request_body(_captured_request(mock_urlopen))["address"] == address

    def test_move_success_on_204(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(b"", status=204)
            make_move("https://rbc.sysx.ir", TOKEN, 14)
        assert mock_urlopen.call_count == 1


class TestErrorHandling:
    def test_non_200_status_raises_competition_error(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(b"nope", status=401)
            with pytest.raises(CompetitionError):
                get_board("https://rbc.sysx.ir", TOKEN)

    def test_http_error_raises_competition_error(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                "https://rbc.sysx.ir/api/v1/Board", 500, "Server Error", {}, None
            )
            with pytest.raises(CompetitionError):
                get_board("https://rbc.sysx.ir", TOKEN)

    def test_url_error_raises_competition_error(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("connection refused")
            with pytest.raises(CompetitionError):
                login("https://rbc.sysx.ir", "game-room-1", "team", "pw")

    def test_empty_login_response_raises_competition_error(self) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(b"", status=204)
            with pytest.raises(CompetitionError):
                login("https://rbc.sysx.ir", "game-room-1", "team", "pw")


class TestRequestLogging:
    def test_post_logs_request_and_response_with_elapsed(self, caplog) -> None:
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = FakeResponse(json.dumps(BOARD_JSON).encode())
            with caplog.at_level(logging.INFO, logger="competition.client"):
                get_board("https://rbc.sysx.ir", TOKEN)
        messages = caplog.messages
        assert any(m.startswith("request: POST /api/v1/Board") for m in messages)
        assert any("response: /api/v1/Board status=200 elapsed=" in m for m in messages)