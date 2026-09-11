import random

from ludo.bots import make_greedy_bot, make_random_bot
from ludo.model import Observation


def _obs(
    own_tokens: tuple[int, ...] = (0, 0, 0, 0),
    opponent_tokens: tuple[tuple[int, ...], ...] = ((0, 0, 0, 0),),
    dice_value: int = 6,
    legal_actions: tuple[int, ...] = (),
) -> Observation:
    return Observation(
        game_id="game-1",
        turn_number=1,
        player_id=0,
        num_players=2,
        dice_value=dice_value,
        consecutive_sixes=0,
        own_tokens=own_tokens,
        opponent_tokens=opponent_tokens,
        game_state="WAIT_FOR_YOU",
        game_over=False,
        is_your_turn=True,
        legal_actions=legal_actions,
    )


class TestRandomBot:
    def test_random_bot_always_returns_legal_action(self) -> None:
        bot = make_random_bot(seed=42)
        rng = random.Random(0)
        for _ in range(200):
            legal = tuple(rng.sample(range(4), rng.randint(1, 4)))
            obs = _obs(dice_value=rng.randint(1, 6), legal_actions=legal)
            assert bot(obs) in legal

    def test_returns_none_when_no_legal_actions(self) -> None:
        bot = make_random_bot(seed=42)
        assert bot(_obs(legal_actions=())) is None

    def test_deterministic_with_same_seed(self) -> None:
        observations = [
            _obs(dice_value=3, legal_actions=(0, 1, 2)),
            _obs(dice_value=5, legal_actions=(1, 3)),
            _obs(dice_value=6, legal_actions=(0,)),
        ]
        bot_a = make_random_bot(seed=123)
        bot_b = make_random_bot(seed=123)
        assert [bot_a(obs) for obs in observations] == [
            bot_b(obs) for obs in observations
        ]


class TestGreedyBot:
    def test_greedy_bot_always_returns_legal_action(self) -> None:
        bot = make_greedy_bot()
        rng = random.Random(0)
        for _ in range(200):
            legal = tuple(rng.sample(range(4), rng.randint(1, 4)))
            own = tuple(rng.randint(0, 44) for _ in range(4))
            obs = _obs(
                own_tokens=own, dice_value=rng.randint(1, 6), legal_actions=legal
            )
            assert bot(obs) in legal

    def test_returns_none_when_no_legal_actions(self) -> None:
        bot = make_greedy_bot()
        assert bot(_obs(legal_actions=())) is None

    def test_capture_wins(self) -> None:
        bot = make_greedy_bot()
        obs = _obs(
            own_tokens=(10, 20, 0, 0),
            opponent_tokens=((13, 5, 0, 0),),
            dice_value=3,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 0

    def test_capture_beats_enter_on_six(self) -> None:
        bot = make_greedy_bot()
        obs = _obs(
            own_tokens=(0, 5, 0, 0),
            opponent_tokens=((11, 0, 0, 0),),
            dice_value=6,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 1

    def test_capture_when_entering(self) -> None:
        bot = make_greedy_bot()
        obs = _obs(
            own_tokens=(0, 10, 0, 0),
            opponent_tokens=((1, 0, 0, 0),),
            dice_value=6,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 0

    def test_enter_on_six_beats_plain_move(self) -> None:
        bot = make_greedy_bot()
        obs = _obs(
            own_tokens=(0, 30, 0, 0),
            dice_value=6,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 0

    def test_highest_position_wins_as_tiebreak(self) -> None:
        bot = make_greedy_bot()
        obs = _obs(
            own_tokens=(10, 25, 5, 0),
            dice_value=2,
            legal_actions=(0, 1, 2),
        )
        assert bot(obs) == 1

    def test_no_capture_in_home_stretch(self) -> None:
        bot = make_greedy_bot()
        obs = _obs(
            own_tokens=(38, 40, 0, 0),
            opponent_tokens=((42, 0, 0, 0),),
            dice_value=4,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 1

    def test_deterministic(self) -> None:
        obs = _obs(own_tokens=(1, 2, 3, 4), dice_value=1, legal_actions=(0, 1, 2, 3))
        assert make_greedy_bot()(obs) == make_greedy_bot()(obs) == 3


class TestBotContracts:
    def test_bot_cannot_return_action_not_in_legal_actions(self) -> None:
        bots = (make_random_bot(seed=7), make_greedy_bot())
        rng = random.Random(1)
        for bot in bots:
            for _ in range(200):
                legal = tuple(rng.sample(range(4), rng.randint(0, 4)))
                obs = _obs(dice_value=rng.randint(1, 6), legal_actions=legal)
                action = bot(obs)
                if legal:
                    assert action in legal
                else:
                    assert action is None

    def test_bot_reset_between_games(self) -> None:
        obs = _obs(dice_value=4, legal_actions=(0, 1, 2, 3))
        first_game = make_random_bot(seed=7)
        second_game = make_random_bot(seed=7)
        first_sequence = [first_game(obs) for _ in range(20)]
        second_sequence = [second_game(obs) for _ in range(20)]
        assert first_sequence == second_sequence