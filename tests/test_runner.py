from unittest import mock

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
USERNAME = "RayanBotTeam"
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
        assert mock_login.call_args == mock.call(BASE_URL, GAME_ID, USERNAME, PASSWORD)
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


class TestHandleCallback:
    def test_callback_wait_for_you_moves(self) -> None:
        bot = make_greedy_bot()
        with mock.patch(
            "competition.runner.get_board", return_value=_board("WAIT_FOR_YOU")
        ) as mock_get_board, mock.patch("competition.runner.make_move") as mock_make_move:
            handle_callback("WAIT_FOR_YOU", bot, BASE_URL, TOKEN)
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
                handle_callback(state, bot, BASE_URL, TOKEN)
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