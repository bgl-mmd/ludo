from ludo.engine import next_player, should_grant_extra_turn
from ludo.model import GameConfig


class TestNextPlayer:
    def test_two_player_alternation(self) -> None:
        config = GameConfig(num_players=2)
        assert next_player(0, config) == 1
        assert next_player(1, config) == 0

    def test_default_config_is_two_player_alternation(self) -> None:
        config = GameConfig()
        assert next_player(0, config) == 1
        assert next_player(1, config) == 0

    def test_four_player_wraps_around(self) -> None:
        config = GameConfig(num_players=4)
        assert next_player(0, config) == 1
        assert next_player(1, config) == 2
        assert next_player(2, config) == 3
        assert next_player(3, config) == 0


class TestShouldGrantExtraTurn:
    def test_dice_6_grants_extra_turn(self) -> None:
        config = GameConfig()
        assert should_grant_extra_turn(6, 1, config) is True

    def test_second_consecutive_6_no_extra_turn(self) -> None:
        config = GameConfig()
        assert should_grant_extra_turn(6, 2, config) is False

    def test_turn_ends_after_extra_turn(self) -> None:
        config = GameConfig()
        assert should_grant_extra_turn(6, 1, config) is True
        assert should_grant_extra_turn(6, 2, config) is False

    def test_regular_roll_no_extra_turn(self) -> None:
        config = GameConfig()
        for value in (1, 2, 3, 4, 5):
            assert should_grant_extra_turn(value, 0, config) is False

    def test_non_six_after_a_six_no_extra_turn(self) -> None:
        config = GameConfig()
        assert should_grant_extra_turn(5, 1, config) is False

    def test_custom_max_consecutive_sixes(self) -> None:
        config = GameConfig(max_consecutive_sixes=3)
        assert should_grant_extra_turn(6, 1, config) is True
        assert should_grant_extra_turn(6, 2, config) is True
        assert should_grant_extra_turn(6, 3, config) is False