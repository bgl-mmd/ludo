import random
from dataclasses import replace

from ludo.bots import make_greedy_bot, make_random_bot
from ludo.coordinates import global_to_player, player_to_global
from ludo.engine import new_game
from ludo.model import CompetitionState, GameConfig, GameState
from ludo.observation import get_observation
from ludo.rules import get_legal_actions

CONFIG = GameConfig()
CONFIG4 = GameConfig(num_players=4)


def _state(
    tokens: tuple[tuple[int, ...], ...],
    current_player: int = 0,
    dice_value: int | None = 4,
    consecutive_sixes: int = 0,
    game_over: bool = False,
    winner: int | None = None,
    error_count: int = 0,
    turn_number: int = 0,
    state: CompetitionState = CompetitionState.NONE,
) -> GameState:
    return GameState(
        tokens=tokens,
        current_player=current_player,
        dice_value=dice_value,
        consecutive_sixes=consecutive_sixes,
        game_over=game_over,
        winner=winner,
        error_count=error_count,
        turn_number=turn_number,
        state=state,
    )


class TestFieldCorrectness:
    def test_all_fields_match_expected_values(self) -> None:
        state = _state(
            tokens=((0, 5, 40, 42), (3, 25, 0, 44)),
            current_player=0,
            dice_value=4,
            consecutive_sixes=1,
            turn_number=7,
        )
        obs = get_observation(state, 0, CONFIG)
        assert obs.game_id == ""
        assert obs.turn_number == 7
        assert obs.player_id == 0
        assert obs.num_players == 2
        assert obs.dice_value == 4
        assert obs.consecutive_sixes == 1
        assert obs.own_tokens == (0, 5, 40, 42)
        assert obs.opponent_tokens == ((23, 5, 0, 44),)
        assert obs.game_state == "WAIT_FOR_YOU"
        assert obs.game_over is False
        assert obs.is_your_turn is True
        assert obs.legal_actions == (1, 2)

    def test_game_id_default_and_custom(self) -> None:
        state = _state(tokens=((0, 0, 0, 0), (0, 0, 0, 0)))
        assert get_observation(state, 0, CONFIG).game_id == ""
        assert get_observation(state, 0, CONFIG, game_id="g-42").game_id == "g-42"

    def test_copied_fields_from_state(self) -> None:
        state = _state(
            tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
            dice_value=6,
            consecutive_sixes=2,
            turn_number=13,
        )
        obs = get_observation(state, 0, CONFIG)
        assert obs.dice_value == 6
        assert obs.consecutive_sixes == 2
        assert obs.turn_number == 13

    def test_own_tokens_copied_unmodified(self) -> None:
        state = _state(tokens=((0, 7, 40, 44), (1, 2, 3, 4)))
        assert get_observation(state, 0, CONFIG).own_tokens == (0, 7, 40, 44)
        assert get_observation(state, 1, CONFIG).own_tokens == (1, 2, 3, 4)

    def test_legal_actions_match_rules_module(self) -> None:
        state = _state(
            tokens=((0, 5, 40, 42), (3, 25, 0, 44)),
            current_player=0,
            dice_value=4,
        )
        obs = get_observation(state, 0, CONFIG)
        assert obs.legal_actions == get_legal_actions(state, CONFIG)

    def test_legal_actions_empty_means_no_move(self) -> None:
        state = _state(tokens=((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=3)
        obs = get_observation(state, 0, CONFIG)
        assert obs.legal_actions == ()

    def test_num_players_from_config(self) -> None:
        state = _state(tokens=((0,) * 4,) * 4)
        obs = get_observation(state, 0, CONFIG4)
        assert obs.num_players == 4
        assert len(obs.opponent_tokens) == 3

    def test_player_id_from_argument(self) -> None:
        state = _state(tokens=((0,) * 4,) * 4)
        for player in range(4):
            assert get_observation(state, player, CONFIG4).player_id == player

    def test_state_not_mutated(self) -> None:
        base = new_game(CONFIG, ("A", "B"))
        state = replace(base, dice_value=4, turn_number=3)
        get_observation(state, 0, CONFIG)
        assert state == replace(base, dice_value=4, turn_number=3)

    def test_built_from_new_game_via_replace(self) -> None:
        state = replace(new_game(CONFIG, ("A", "B")), dice_value=6)
        obs = get_observation(state, 0, CONFIG)
        assert obs.own_tokens == (0, 0, 0, 0)
        assert obs.opponent_tokens == ((0, 0, 0, 0),)
        assert obs.game_state == "WAIT_FOR_YOU"
        assert obs.is_your_turn is True
        assert obs.game_over is False


class TestGameStateString:
    def test_wait_for_you(self) -> None:
        state = _state(tokens=((0, 0, 0, 0), (0, 0, 0, 0)), current_player=1)
        assert get_observation(state, 1, CONFIG).game_state == "WAIT_FOR_YOU"

    def test_wait_for_move(self) -> None:
        state = _state(tokens=((0, 0, 0, 0), (0, 0, 0, 0)), current_player=1)
        assert get_observation(state, 0, CONFIG).game_state == "WAIT_FOR_MOVE"

    def test_end_you_win(self) -> None:
        state = _state(
            tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
            game_over=True,
            winner=0,
        )
        assert get_observation(state, 0, CONFIG).game_state == "END_YOU_WIN"

    def test_end_you_lost(self) -> None:
        state = _state(
            tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
            game_over=True,
            winner=1,
        )
        assert get_observation(state, 0, CONFIG).game_state == "END_YOU_LOST"
        assert get_observation(state, 1, CONFIG).game_state == "END_YOU_WIN"

    def test_end_equals(self) -> None:
        state = _state(
            tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
            game_over=True,
            winner=None,
        )
        assert get_observation(state, 0, CONFIG).game_state == "END_EQUALS"

    def test_end_state_overrides_turn(self) -> None:
        state = _state(
            tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
            current_player=0,
            game_over=True,
            winner=1,
        )
        assert get_observation(state, 0, CONFIG).game_state == "END_YOU_LOST"

    def test_competition_state_mapping_preferred(self) -> None:
        state = _state(
            tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
            state=CompetitionState.WAIT_FOR_START,
        )
        assert get_observation(state, 0, CONFIG).game_state == "WAIT_FOR_START"

    def test_competition_state_end_mapping(self) -> None:
        state = _state(
            tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
            game_over=True,
            winner=0,
            state=CompetitionState.END_YOU_LOST,
        )
        assert get_observation(state, 0, CONFIG).game_state == "END_YOU_LOST"


class TestOpponentCoordinateConversion:
    def test_two_player_home_yard_stays_zero(self) -> None:
        state = _state(tokens=((0, 0, 0, 0), (0, 0, 0, 0)))
        obs = get_observation(state, 0, CONFIG)
        assert obs.opponent_tokens == ((0, 0, 0, 0),)

    def test_two_player_track_conversion(self) -> None:
        state = _state(tokens=((0, 0, 0, 0), (1, 20, 3, 0)))
        obs = get_observation(state, 0, CONFIG)
        assert obs.opponent_tokens == ((21, 40, 23, 0),)
        assert obs.opponent_tokens == (
            tuple(
                global_to_player(player_to_global(pos, 1, CONFIG), 0, CONFIG)
                for pos in state.tokens[1]
            ),
        )

    def test_two_player_conversion_is_mutual(self) -> None:
        state = _state(tokens=((5, 40, 0, 0), (25, 20, 0, 0)))
        assert get_observation(state, 0, CONFIG).opponent_tokens == ((5, 40, 0, 0),)
        assert get_observation(state, 1, CONFIG).opponent_tokens == ((25, 20, 0, 0),)

    def test_four_player_non_trivial_conversion(self) -> None:
        state = _state(
            tokens=(
                (0, 0, 0, 0),
                (5, 0, 0, 0),
                (7, 35, 0, 0),
                (3, 0, 0, 0),
            )
        )
        obs = get_observation(state, 0, CONFIG4)
        assert obs.opponent_tokens == ((15, 0, 0, 0), (27, 15, 0, 0), (33, 0, 0, 0))

    def test_four_player_observer_is_not_first(self) -> None:
        state = _state(
            tokens=(
                (10, 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
            )
        )
        obs = get_observation(state, 2, CONFIG4)
        assert obs.opponent_tokens[0] == (30, 0, 0, 0)

    def test_home_stretch_and_home_yard_unchanged(self) -> None:
        state = _state(tokens=((0, 0, 0, 0), (0, 41, 44, 0)))
        obs = get_observation(state, 0, CONFIG)
        assert obs.opponent_tokens == ((0, 41, 44, 0),)

    def test_opponent_and_token_order_preserved(self) -> None:
        state = _state(
            tokens=(
                (0, 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
                (0, 0, 0, 0),
            )
        )
        obs = get_observation(state, 1, CONFIG4)
        assert len(obs.opponent_tokens) == 3
        for opponent, seen in zip((0, 2, 3), obs.opponent_tokens):
            assert seen == state.tokens[opponent]


class TestInvariantPlayerCannotSeeOtherPlayerCoordinates:
    def test_invariant_player_cannot_see_other_player_coordinates(self) -> None:
        for seed in range(20):
            for config in (CONFIG, CONFIG4):
                rng = random.Random(seed)
                tokens = tuple(
                    tuple(rng.randint(0, 44) for _ in range(config.tokens_per_player))
                    for _ in range(config.num_players)
                )
                state = _state(
                    tokens=tokens,
                    current_player=rng.randrange(config.num_players),
                    dice_value=rng.randint(1, 6),
                    consecutive_sixes=rng.randint(0, 2),
                    turn_number=rng.randint(0, 50),
                )
                for player in range(config.num_players):
                    self._check_player_view(state, config, player)

    def _check_player_view(
        self, state: GameState, config: GameConfig, player: int
    ) -> None:
        obs = get_observation(state, player, config)
        opponents = [o for o in range(config.num_players) if o != player]
        for opponent, seen_tokens in zip(opponents, obs.opponent_tokens):
            for raw, seen in zip(state.tokens[opponent], seen_tokens):
                assert 0 <= seen <= 44
                if seen == 0:
                    assert raw == 0
                elif seen > 40:
                    assert raw == seen
                else:
                    converted = global_to_player(
                        player_to_global(raw, opponent, config), player, config
                    )
                    assert seen == converted
                    assert player_to_global(
                        seen, player, config
                    ) == player_to_global(raw, opponent, config)
                    if converted != raw:
                        assert seen != raw


class TestBotReceivesValidObservation:
    def test_bots_return_legal_action_on_real_observations(self) -> None:
        random_bot = make_random_bot(seed=42)
        greedy_bot = make_greedy_bot()
        states = self._sample_states()
        for state in states:
            for player in range(len(state.tokens)):
                obs = get_observation(state, player, CONFIG)
                for bot in (random_bot, greedy_bot):
                    action = bot(obs)
                    if obs.legal_actions:
                        assert action in obs.legal_actions
                    else:
                        assert action is None

    def test_random_bot_never_crashes_over_many_observations(self) -> None:
        bot = make_random_bot(seed=7)
        for seed in range(50):
            state = self._random_state(seed)
            for player in range(len(state.tokens)):
                obs = get_observation(state, player, CONFIG)
                action = bot(obs)
                assert action is None or action in obs.legal_actions

    def test_greedy_bot_never_crashes_over_many_observations(self) -> None:
        bot = make_greedy_bot()
        for seed in range(50):
            state = self._random_state(seed)
            for player in range(len(state.tokens)):
                obs = get_observation(state, player, CONFIG)
                action = bot(obs)
                assert action is None or action in obs.legal_actions

    def _sample_states(self) -> list[GameState]:
        return [
            replace(new_game(CONFIG, ("A", "B")), dice_value=6),
            _state(tokens=((0, 5, 40, 42), (3, 25, 0, 44)), dice_value=4),
            _state(tokens=((0, 0, 0, 0), (0, 0, 0, 0)), dice_value=3),
            _state(tokens=((1, 10, 20, 30), (2, 12, 22, 32)), dice_value=6),
            _state(tokens=((0, 41, 42, 43), (0, 0, 0, 0)), dice_value=1),
            _state(
                tokens=((0, 0, 0, 0), (0, 0, 0, 0)),
                current_player=1,
                dice_value=5,
            ),
        ]

    def _random_state(self, seed: int) -> GameState:
        rng = random.Random(seed)
        tokens = tuple(
            tuple(rng.randint(0, 44) for _ in range(CONFIG.tokens_per_player))
            for _ in range(CONFIG.num_players)
        )
        return _state(
            tokens=tokens,
            current_player=rng.randrange(CONFIG.num_players),
            dice_value=rng.randint(1, 6),
            consecutive_sixes=rng.randint(0, 2),
            turn_number=rng.randint(0, 50),
        )