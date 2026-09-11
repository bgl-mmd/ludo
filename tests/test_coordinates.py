from ludo.coordinates import compute_begin_offsets, global_to_player, player_to_global
from ludo.model import GameConfig

PLAYER_A_BEGIN = 1
PLAYER_B_BEGIN = 21


def _config() -> GameConfig:
    return GameConfig()


class TestCoordinateConversion:
    def test_global_to_player_identity(self) -> None:
        config = _config()
        assert global_to_player(1, 0, config) == 1
        assert global_to_player(20, 0, config) == 20
        assert global_to_player(40, 0, config) == 40
        assert global_to_player(21, 1, config) == 1
        assert global_to_player(40, 1, config) == 20

    def test_player_to_global_identity(self) -> None:
        config = _config()
        assert player_to_global(1, 0, config) == 1
        assert player_to_global(20, 0, config) == 20
        assert player_to_global(40, 0, config) == 40
        assert player_to_global(1, 1, config) == 21
        assert player_to_global(40, 1, config) == 20

    def test_global_to_player_wraparound(self) -> None:
        config = _config()
        assert global_to_player(1, 1, config) == 21
        assert global_to_player(20, 1, config) == 40

    def test_player_to_global_wraparound(self) -> None:
        config = _config()
        assert player_to_global(21, 1, config) == 1
        assert player_to_global(40, 1, config) == 20

    def test_home_yard_always_zero(self) -> None:
        config = _config()
        for player in range(config.num_players):
            assert global_to_player(0, player, config) == 0
            assert player_to_global(0, player, config) == 0

    def test_home_stretch_positions(self) -> None:
        config = _config()
        for player in range(config.num_players):
            for pos in range(41, 45):
                assert global_to_player(pos, player, config) == pos
                assert player_to_global(pos, player, config) == pos

    def test_begin_end_offsets_for_each_player(self) -> None:
        config = _config()
        assert compute_begin_offsets(config) == (PLAYER_A_BEGIN, PLAYER_B_BEGIN)
        for player, begin, end in (
            (0, PLAYER_A_BEGIN, 40),
            (1, PLAYER_B_BEGIN, 20),
        ):
            assert player_to_global(1, player, config) == begin
            assert player_to_global(40, player, config) == end
            assert global_to_player(begin, player, config) == 1
            assert global_to_player(end, player, config) == 40