import random
from dataclasses import replace

from ludo.bots import make_mcts_bot
from ludo.engine import new_game
from ludo.mcts import _observation_to_state, _score
from ludo.model import CompetitionState, GameConfig, GameState, Observation
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
    turn_number: int = 0,
) -> GameState:
    return GameState(
        tokens=tokens,
        current_player=current_player,
        dice_value=dice_value,
        consecutive_sixes=consecutive_sixes,
        game_over=game_over,
        winner=None,
        error_count=0,
        turn_number=turn_number,
        state=CompetitionState.NONE,
    )


def _obs(
    own_tokens: tuple[int, ...] = (0, 0, 0, 0),
    opponent_tokens: tuple[tuple[int, ...], ...] = ((0, 0, 0, 0),),
    dice_value: int = 6,
    legal_actions: tuple[int, ...] = (),
    num_players: int = 2,
) -> Observation:
    return Observation(
        game_id="game-1",
        turn_number=1,
        player_id=0,
        num_players=num_players,
        dice_value=dice_value,
        consecutive_sixes=0,
        own_tokens=own_tokens,
        opponent_tokens=opponent_tokens,
        game_state="WAIT_FOR_YOU",
        game_over=False,
        is_your_turn=True,
        legal_actions=legal_actions,
    )


class TestObservationToState:
    def test_round_trip_two_player(self) -> None:
        state = _state(
            tokens=((0, 5, 40, 42), (3, 25, 0, 44)),
            current_player=0,
            dice_value=4,
            turn_number=7,
        )
        reconstructed = _observation_to_state(
            get_observation(state, 0, CONFIG), CONFIG
        )
        assert reconstructed.tokens == state.tokens
        assert reconstructed.current_player == state.current_player
        assert reconstructed.dice_value == state.dice_value

    def test_round_trip_four_player(self) -> None:
        state = _state(
            tokens=(
                (0, 0, 0, 0),
                (5, 0, 0, 0),
                (7, 35, 0, 0),
                (3, 0, 0, 0),
            ),
            current_player=2,
            dice_value=3,
            turn_number=5,
        )
        reconstructed = _observation_to_state(
            get_observation(state, 2, CONFIG4), CONFIG4
        )
        assert reconstructed.tokens == state.tokens

    def test_legal_actions_preserved(self) -> None:
        state = _state(
            tokens=((0, 5, 40, 42), (3, 25, 0, 44)),
            current_player=0,
            dice_value=4,
        )
        obs = get_observation(state, 0, CONFIG)
        reconstructed = _observation_to_state(obs, CONFIG)
        assert obs.legal_actions == get_legal_actions(reconstructed, CONFIG)

    def test_round_trip_over_many_random_states(self) -> None:
        rng = random.Random(0)
        for seed in range(20):
            rng = random.Random(seed)
            config = CONFIG4 if seed % 2 else CONFIG
            tokens = tuple(
                tuple(rng.randint(0, 44) for _ in range(config.tokens_per_player))
                for _ in range(config.num_players)
            )
            player = rng.randrange(config.num_players)
            state = _state(
                tokens=tokens,
                current_player=player,
                dice_value=rng.randint(1, 6),
                turn_number=rng.randint(0, 30),
            )
            reconstructed = _observation_to_state(
                get_observation(state, player, config), config
            )
            assert reconstructed.tokens == state.tokens


class TestScore:
    def test_real_capture_is_detected(self) -> None:
        # p0 rel 5 -> dest 8 (global 8); p1 rel 28 = global 8.
        state = _state(tokens=((5, 0, 0, 0), (28, 0, 0, 0)), dice_value=3)
        assert _score(0, state, CONFIG)[0] == 1

    def test_numeric_coincidence_is_not_a_capture(self) -> None:
        # p1 rel 8 = global 28, not global 8; dest 8 is empty.
        state = _state(tokens=((5, 0, 0, 0), (8, 0, 0, 0)), dice_value=3)
        assert _score(0, state, CONFIG)[0] == 0

    def test_no_capture_on_home_stretch(self) -> None:
        state = _state(tokens=((40, 0, 0, 0), (0, 0, 0, 0)), dice_value=4)
        assert _score(0, state, CONFIG)[0] == 0

    def test_capture_is_symmetric_between_players(self) -> None:
        # p1 rel 5 -> dest 8 (global 28); p0 rel 28 = global 28.
        state = _state(
            tokens=((28, 0, 0, 0), (5, 0, 0, 0)),
            current_player=1,
            dice_value=3,
        )
        assert _score(0, state, CONFIG)[0] == 1

    def test_four_player_capture_is_detected(self) -> None:
        # p0 rel 5 -> dest 8 (global 8); p2 rel 28 = global 8.
        state = _state(
            tokens=((5, 0, 0, 0), (0, 0, 0, 0), (28, 0, 0, 0), (0, 0, 0, 0)),
            dice_value=3,
        )
        assert _score(0, state, CONFIG4)[0] == 1


class TestMctsBot:
    def test_mcts_bot_always_returns_legal_action(self) -> None:
        bot = make_mcts_bot(iterations=50, seed=42)
        rng = random.Random(0)
        for _ in range(20):
            legal = tuple(rng.sample(range(4), rng.randint(1, 4)))
            own = tuple(rng.randint(0, 44) for _ in range(4))
            obs = _obs(
                own_tokens=own, dice_value=rng.randint(1, 6), legal_actions=legal
            )
            assert bot(obs) in legal

    def test_returns_none_when_no_legal_actions(self) -> None:
        bot = make_mcts_bot(iterations=50)
        assert bot(_obs(legal_actions=())) is None

    def test_deterministic_with_same_seed(self) -> None:
        observations = [
            _obs(dice_value=3, legal_actions=(0, 1, 2)),
            _obs(dice_value=5, legal_actions=(1, 3)),
            _obs(dice_value=6, legal_actions=(0,)),
        ]
        bot_a = make_mcts_bot(iterations=50, seed=123)
        bot_b = make_mcts_bot(iterations=50, seed=123)
        assert [bot_a(obs) for obs in observations] == [
            bot_b(obs) for obs in observations
        ]

    def test_never_crashes_over_many_observations(self) -> None:
        bot = make_mcts_bot(iterations=30, seed=7)
        rng = random.Random(1)
        for seed in range(10):
            rng = random.Random(seed)
            tokens = tuple(
                tuple(rng.randint(0, 44) for _ in range(4))
                for _ in range(2)
            )
            state = _state(
                tokens=tokens,
                current_player=rng.randrange(2),
                dice_value=rng.randint(1, 6),
            )
            for player in range(2):
                obs = get_observation(state, player, CONFIG)
                action = bot(obs)
                if obs.legal_actions:
                    assert action in obs.legal_actions
                else:
                    assert action is None

    def test_mcts_bot_plays_full_game(self) -> None:
        from ludo.simulation import run_simulation

        bots = (make_mcts_bot(iterations=50, seed=3), make_mcts_bot(iterations=50, seed=4))
        result, _ = run_simulation(bots, CONFIG, seed=42)
        assert result.winner in (0, 1)


class TestMctsBotThroughObservationBuilder:
    def test_mcts_bot_returns_legal_action_on_real_observations(self) -> None:
        bot = make_mcts_bot(iterations=50, seed=42)
        states = [
            replace(new_game(CONFIG, ("A", "B")), dice_value=6),
            _state(tokens=((0, 5, 40, 42), (3, 25, 0, 44)), dice_value=4),
            _state(tokens=((1, 10, 20, 30), (2, 12, 22, 32)), dice_value=6),
            _state(tokens=((0, 41, 42, 43), (0, 0, 0, 0)), dice_value=1),
        ]
        for state in states:
            for player in range(2):
                obs = get_observation(state, player, CONFIG)
                action = bot(obs)
                if obs.legal_actions:
                    assert action in obs.legal_actions
                else:
                    assert action is None