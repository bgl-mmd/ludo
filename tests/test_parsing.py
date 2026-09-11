from competition.parsing import (
    BoardState,
    action_to_address,
    parse_board,
    parse_observation,
    parse_result,
)

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


def _board(
    state: str,
    dice: int = 6,
    tokens: tuple[tuple[int, ...], ...] = ((14, 0, 41, 43), (0, 42, 20, 0)),
) -> BoardState:
    users = [
        {"name": "RayanBotTeam1", "begin": 1, "end": 40, "tokens": list(tokens[0])},
        {"name": "RayanBotTeam2", "begin": 21, "end": 20, "tokens": list(tokens[1])},
    ]
    return parse_board(
        {"gameID": "game-room-1", "state": state, "dice": dice, "users": users}
    )


class TestBoardResponseParsing:
    def test_board_response_parsing(self) -> None:
        board = parse_board(BOARD_JSON)
        assert isinstance(board, BoardState)
        assert board.game_id == "game-room-1"
        assert board.state == "WAIT_FOR_YOU"
        assert board.dice == 6
        assert len(board.users) == 2
        first, second = board.users
        assert first.name == "RayanBotTeam1"
        assert first.begin == 1
        assert first.end == 40
        assert first.tokens == (14, 0, 41, 43)
        assert second.name == "RayanBotTeam2"
        assert second.begin == 21
        assert second.end == 20
        assert second.tokens == (0, 42, 20, 0)

    def test_tokens_remain_player_relative(self) -> None:
        board = parse_board(BOARD_JSON)
        assert board.users[0].tokens == (14, 0, 41, 43)
        assert board.users[1].tokens == (0, 42, 20, 0)

    def test_dice_zero_is_not_rolled(self) -> None:
        board = parse_board(dict(BOARD_JSON, state="WAIT_FOR_MOVE", dice=0))
        assert board.dice == 0


class TestStateMappingCompetitionToEngine:
    def test_state_mapping_competition_to_engine(self) -> None:
        cases = {
            "NONE": (False, False, "NONE"),
            "WAIT_FOR_START": (False, False, "WAIT_FOR_START"),
            "WAIT_FOR_YOU": (True, False, "WAIT_FOR_YOU"),
            "WAIT_FOR_MOVE": (False, False, "WAIT_FOR_MOVE"),
            "END_YOU_WIN": (False, True, "END_YOU_WIN"),
            "END_YOU_LOST": (False, True, "END_YOU_LOST"),
            "END_EQUALS": (False, True, "END_EQUALS"),
        }
        for state, (is_your_turn, game_over, game_state) in cases.items():
            obs = parse_observation(_board(state), player_id=0)
            assert obs.is_your_turn is is_your_turn
            assert obs.game_over is game_over
            assert obs.game_state == game_state

    def test_end_winner_mapping(self) -> None:
        assert parse_result(_board("END_YOU_WIN"), player_id=0).winner == 0
        assert parse_result(_board("END_YOU_LOST"), player_id=0).winner == 1
        assert parse_result(_board("END_YOU_LOST"), player_id=1).winner == 0
        assert parse_result(_board("END_YOU_WIN"), player_id=1).winner == 1
        assert parse_result(_board("END_EQUALS"), player_id=0).winner is None

    def test_observation_fields_from_example(self) -> None:
        obs = parse_observation(parse_board(BOARD_JSON), player_id=0)
        assert obs.game_id == "game-room-1"
        assert obs.turn_number == 0
        assert obs.player_id == 0
        assert obs.num_players == 2
        assert obs.dice_value == 6
        assert obs.consecutive_sixes == 0
        assert obs.own_tokens == (14, 0, 41, 43)
        assert obs.opponent_tokens == ((0, 42, 40, 0),)
        assert obs.game_state == "WAIT_FOR_YOU"
        assert obs.game_over is False
        assert obs.is_your_turn is True

    def test_pre_game_states_have_no_legal_actions(self) -> None:
        for state in ("NONE", "WAIT_FOR_START", "WAIT_FOR_MOVE"):
            obs = parse_observation(_board(state), player_id=0)
            assert obs.legal_actions == ()

    def test_end_states_have_no_legal_actions(self) -> None:
        for state in ("END_YOU_WIN", "END_YOU_LOST", "END_EQUALS"):
            obs = parse_observation(_board(state), player_id=0)
            assert obs.legal_actions == ()


class TestLegalActions:
    def test_legal_actions_non_empty_when_move_exists(self) -> None:
        obs = parse_observation(_board("WAIT_FOR_YOU"), player_id=0)
        assert obs.legal_actions == (0, 1)

    def test_legal_actions_empty_when_no_move(self) -> None:
        board = _board("WAIT_FOR_YOU", dice=3, tokens=((0, 0, 0, 0), (0, 0, 0, 0)))
        obs = parse_observation(board, player_id=0)
        assert obs.legal_actions == ()

    def test_dice_zero_means_not_rolled(self) -> None:
        board = _board(
            "WAIT_FOR_YOU",
            dice=0,
            tokens=((14, 0, 41, 43), (0, 42, 20, 0)),
        )
        obs = parse_observation(board, player_id=0)
        assert obs.dice_value == 0
        assert obs.legal_actions == ()

    def test_second_player_legal_actions(self) -> None:
        obs = parse_observation(_board("WAIT_FOR_YOU"), player_id=1)
        assert obs.own_tokens == (0, 42, 20, 0)
        assert obs.player_id == 1
        assert obs.is_your_turn is True


class TestMoveAddressConversion:
    def test_action_maps_to_source_cell_address(self) -> None:
        own_tokens = (14, 0, 41, 43)
        assert action_to_address(own_tokens, 0) == 14
        assert action_to_address(own_tokens, 1) == 0
        assert action_to_address(own_tokens, 2) == 41
        assert action_to_address(own_tokens, 3) == 43

    def test_move_0_for_no_valid_move(self) -> None:
        assert action_to_address((0, 0, 0, 0), None) == "0"
        assert isinstance(action_to_address((0, 0, 0, 0), None), str)

    def test_int_and_string_addresses_handled(self) -> None:
        assert isinstance(action_to_address((14, 0, 41, 43), 0), int)
        assert action_to_address((14, 0, 41, 43), None) == "0"


class TestParseResult:
    def test_default_counts(self) -> None:
        result = parse_result(_board("END_YOU_WIN"), player_id=0)
        assert result.turn_count == 0
        assert result.error_count == 0

    def test_non_terminal_state_winner_none(self) -> None:
        assert parse_result(_board("WAIT_FOR_YOU"), player_id=0).winner is None
        assert parse_result(_board("NONE"), player_id=0).winner is None