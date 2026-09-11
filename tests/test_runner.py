import logging
from unittest import mock

import pytest

from competition.client import CompetitionError
from competition.parsing import (
    action_to_address,
    parse_board,
    parse_observation,
)
from competition.runner import handle_callback, replace_callback_state, run_competition
from ludo.bots import make_greedy_bot
from ludo.model import GameConfig, GameResult

BASE_URL = "https://rbc.sysx.ir"
GAME_ID = "game-room-1"
USERNAME = "RayanBotTeam1"
PASSWORD = "123"
TOKEN = "token-123"


def _board(
    state: str,
    dice: int = 6,
    tokens: tuple[tuple[int, ...], ...] = ((14, 0, 41, 43), (0, 42, 20, 0)),
):
    users = [
        {"name": "RayanBotTeam1", "begin": 1, "end": 40, "tokens": list(tokens[0])},
        {"name": "RayanBotTeam2", "begin": 21, "end": 20, "tokens": list(tokens[1])},
    ]
    return parse_board(
        {"gameID": GAME_ID, "state": state, "dice": dice, "users": users}
    )


class TestRunCompetition:
    def test_full_scripted_game(self) -> None:
        boards = [
            _board("WAIT_FOR_START"),
            _board("WAIT_FOR_YOU"),
            _board("WAIT_FOR_MOVE"),
            _board("WAIT_FOR_YOU"),
            _board("END_YOU_WIN"),
        ]
        bot = make_greedy_bot()
        with mock.patch("competition.runner.login", return_value=TOKEN) as mock_login, mock.patch(
            "competition.runner.get_board", side_effect=boards
        ) as mock_get_board, mock.patch("competition.runner.make_move") as mock_make_move:
            result = run_competition(
                bot, BASE_URL, GAME_ID, USERNAME, PASSWORD, GameConfig(), poll_interval=0
            )
        assert mock_login.call_count == 1
        assert mock_login.call_args == mock.call(
            BASE_URL, GAME_ID, USERNAME, PASSWORD, None
        )
        assert mock_get_board.call_count == 5
        obs = parse_observation(_board("WAIT_FOR_YOU"), player_id=0)
        address = action_to_address(obs.own_tokens, bot(obs))
        assert mock_make_move.call_args_list == [
            mock.call(BASE_URL, TOKEN, address),
            mock.call(BASE_URL, TOKEN, address),
        ]
        assert isinstance(result, GameResult)
        assert result.winner == 0

    def test_bot_none_when_no_legal_moves(self) -> None:
        boards = [
            _board("WAIT_FOR_YOU", dice=3, tokens=((0, 0, 0, 0), (0, 0, 0, 0))),
            _board("END_YOU_LOST", dice=3, tokens=((0, 0, 0, 0), (0, 0, 0, 0))),
        ]
        bot = make_greedy_bot()
        with mock.patch("competition.runner.login", return_value=TOKEN), mock.patch(
            "competition.runner.get_board", side_effect=boards
        ), mock.patch("competition.runner.make_move") as mock_make_move:
            result = run_competition(
                bot, BASE_URL, GAME_ID, USERNAME, PASSWORD, GameConfig(), poll_interval=0
            )
        assert mock_make_move.call_count == 1
        assert mock_make_move.call_args == mock.call(BASE_URL, TOKEN, "0")
        assert result.winner == 1

    def test_polls_with_interval(self) -> None:
        boards = [
            _board("NONE"),
            _board("WAIT_FOR_YOU"),
            _board("END_YOU_WIN"),
        ]
        bot = make_greedy_bot()
        with mock.patch("competition.runner.login", return_value=TOKEN), mock.patch(
            "competition.runner.get_board", side_effect=boards
        ), mock.patch("competition.runner.make_move"), mock.patch(
            "competition.runner.time.sleep"
        ) as mock_sleep:
            run_competition(
                bot,
                BASE_URL,
                GAME_ID,
                USERNAME,
                PASSWORD,
                GameConfig(),
                poll_interval=2.0,
            )
        assert mock_sleep.call_count == 2
        assert mock_sleep.call_args_list == [mock.call(2.0), mock.call(2.0)]

    def test_move_failure_logs_board_and_address_then_reraises(self, caplog) -> None:
        boards = [
            _board("WAIT_FOR_YOU"),
            _board("END_YOU_WIN"),
        ]
        bot = make_greedy_bot()
        obs = parse_observation(_board("WAIT_FOR_YOU"), player_id=0)
        address = action_to_address(obs.own_tokens, bot(obs))
        error = CompetitionError("HTTP 500 from /api/v1/Move: Server Error")
        with caplog.at_level(logging.ERROR, logger="competition.runner"):
            with mock.patch("competition.runner.login", return_value=TOKEN), mock.patch(
                "competition.runner.get_board", side_effect=boards
            ), mock.patch(
                "competition.runner.make_move", side_effect=error
            ):
                with pytest.raises(CompetitionError):
                    run_competition(
                        bot, BASE_URL, GAME_ID, USERNAME, PASSWORD, GameConfig(), poll_interval=0
                    )
        assert caplog.messages, "expected an error log record"
        record = caplog.records[0]
        assert record.getMessage().startswith("failed to make move:")
        assert "address=%s" % address in record.getMessage()
        assert "game-room-1" in record.getMessage()
        assert "WAIT_FOR_YOU" in record.getMessage()

    def test_board_poll_failure_logs_last_board_then_reraises(self, caplog) -> None:
        last_board = _board("WAIT_FOR_MOVE")
        bot = make_greedy_bot()
        error = CompetitionError("HTTP 500 from /api/v1/Board: Server Error")
        with caplog.at_level(logging.ERROR, logger="competition.runner"):
            with mock.patch("competition.runner.login", return_value=TOKEN), mock.patch(
                "competition.runner.get_board", side_effect=[last_board, error]
            ), mock.patch("competition.runner.make_move"):
                with pytest.raises(CompetitionError):
                    run_competition(
                        bot, BASE_URL, GAME_ID, USERNAME, PASSWORD, GameConfig(), poll_interval=0
                    )
        assert caplog.messages, "expected an error log record"
        record = caplog.records[0]
        assert record.getMessage().startswith("failed to poll board:")
        assert "game-room-1" in record.getMessage()
        assert "WAIT_FOR_MOVE" in record.getMessage()

    def test_logged_in_user_not_first_in_users_list(self) -> None:
        boards = [
            parse_board(
                {
                    "gameID": GAME_ID,
                    "state": "WAIT_FOR_YOU",
                    "dice": 1,
                    "users": [
                        {"name": "randombot1", "begin": 21, "end": 20, "tokens": [0, 0, 0, 0]},
                        {"name": "greedybot1", "begin": 1, "end": 40, "tokens": [1, 0, 0, 0]},
                    ],
                }
            ),
            parse_board(
                {
                    "gameID": GAME_ID,
                    "state": "END_YOU_WIN",
                    "dice": 1,
                    "users": [
                        {"name": "randombot1", "begin": 21, "end": 20, "tokens": [0, 0, 0, 0]},
                        {"name": "greedybot1", "begin": 1, "end": 40, "tokens": [2, 0, 0, 0]},
                    ],
                }
            ),
        ]
        bot = make_greedy_bot()
        with mock.patch("competition.runner.login", return_value=TOKEN), mock.patch(
            "competition.runner.get_board", side_effect=boards
        ), mock.patch("competition.runner.make_move") as mock_make_move:
            result = run_competition(
                bot, BASE_URL, GAME_ID, "greedybot1", PASSWORD, GameConfig(), poll_interval=0
            )
        assert mock_make_move.call_count == 1
        assert mock_make_move.call_args == mock.call(BASE_URL, TOKEN, 1)
        assert result.winner == 1

    def test_passes_callback_url_to_login(self) -> None:
        boards = [_board("END_YOU_WIN")]
        bot = make_greedy_bot()
        callback_url = "http://mybot.local/cb?state={0}"
        with mock.patch("competition.runner.login", return_value=TOKEN) as mock_login, mock.patch(
            "competition.runner.get_board", side_effect=boards
        ):
            run_competition(
                bot,
                BASE_URL,
                GAME_ID,
                USERNAME,
                PASSWORD,
                GameConfig(),
                poll_interval=0,
                callback_url=callback_url,
            )
        assert mock_login.call_args == mock.call(
            BASE_URL, GAME_ID, USERNAME, PASSWORD, callback_url
        )

    def test_logs_gamestate_and_move(self, caplog) -> None:
        boards = [
            _board("WAIT_FOR_YOU"),
            _board("END_YOU_WIN"),
        ]
        bot = make_greedy_bot()
        with caplog.at_level(logging.INFO, logger="competition.runner"):
            with mock.patch("competition.runner.login", return_value=TOKEN), mock.patch(
                "competition.runner.get_board", side_effect=boards
            ), mock.patch("competition.runner.make_move"):
                run_competition(
                    bot, BASE_URL, GAME_ID, USERNAME, PASSWORD, GameConfig(), poll_interval=0
                )
        messages = caplog.messages
        assert any(m.startswith("gamestate received:") for m in messages)
        assert any(m.startswith("making move: address=") for m in messages)


class TestHandleCallback:
    def test_callback_wait_for_you_moves(self) -> None:
        bot = make_greedy_bot()
        with mock.patch(
            "competition.runner.get_board", return_value=_board("WAIT_FOR_YOU")
        ) as mock_get_board, mock.patch("competition.runner.make_move") as mock_make_move:
            handle_callback("WAIT_FOR_YOU", bot, BASE_URL, TOKEN, USERNAME)
        assert mock_get_board.call_count == 1
        obs = parse_observation(_board("WAIT_FOR_YOU"), player_id=0)
        address = action_to_address(obs.own_tokens, bot(obs))
        assert mock_make_move.call_count == 1
        assert mock_make_move.call_args == mock.call(BASE_URL, TOKEN, address)

    def test_callback_end_state_passes(self) -> None:
        bot = make_greedy_bot()
        for state in ("END_YOU_WIN", "END_YOU_LOST", "END_EQUALS"):
            with mock.patch("competition.runner.get_board") as mock_get_board, mock.patch(
                "competition.runner.make_move"
            ) as mock_make_move:
                handle_callback(state, bot, BASE_URL, TOKEN, USERNAME)
            assert mock_get_board.call_count == 0
            assert mock_make_move.call_count == 0


class TestReplaceCallbackState:
    def test_callback_url_state_replacement(self) -> None:
        url = "http://myBot.local/gamestatecallback?gamestate={0}"
        assert (
            replace_callback_state(url, "WAIT_FOR_YOU")
            == "http://myBot.local/gamestatecallback?gamestate=WAIT_FOR_YOU"
        )
        assert (
            replace_callback_state(url, "END_YOU_WIN")
            == "http://myBot.local/gamestatecallback?gamestate=END_YOU_WIN"
        )