import random

from ludo.bots import make_mcts_evasive_bot as _re_exported
from ludo.mcts import _classify_actions, make_mcts_evasive_bot
from ludo.model import GameConfig, Observation
from ludo.simulation import run_simulation


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


class TestClassifyActions:
    def test_capture_detected_on_player_relative_coords(self) -> None:
        captures, escapes = _classify_actions(
            _obs(
                own_tokens=(10, 0, 0, 0),
                opponent_tokens=((13, 5, 0, 0),),
                dice_value=3,
                legal_actions=(0,),
            ),
            4,
        )
        assert captures == (0,)
        assert escapes == ()

    def test_escape_detected_when_threatened(self) -> None:
        captures, escapes = _classify_actions(
            _obs(
                own_tokens=(10, 0, 0, 0),
                opponent_tokens=((8, 0, 0, 0),),
                dice_value=3,
                legal_actions=(0,),
            ),
            4,
        )
        assert captures == ()
        assert escapes == (0,)

    def test_no_escape_when_gap_stays_in_danger_window(self) -> None:
        _, escapes = _classify_actions(
            _obs(
                own_tokens=(10, 0, 0, 0),
                opponent_tokens=((9, 0, 0, 0),),
                dice_value=1,
                legal_actions=(0,),
            ),
            4,
        )
        assert escapes == ()

    def test_escape_into_home_stretch_counts(self) -> None:
        _, escapes = _classify_actions(
            _obs(
                own_tokens=(40, 0, 0, 0),
                opponent_tokens=((37, 0, 0, 0),),
                dice_value=4,
                legal_actions=(0,),
            ),
            4,
        )
        assert escapes == (0,)

    def test_opponent_in_home_yard_is_not_a_threat(self) -> None:
        _, escapes = _classify_actions(
            _obs(
                own_tokens=(10, 0, 0, 0),
                opponent_tokens=((0, 9, 0, 0),),
                dice_value=1,
                legal_actions=(0,),
            ),
            4,
        )
        assert escapes == ()


class TestMctsEvasiveBot:
    def test_reexported_from_bots(self) -> None:
        assert _re_exported is make_mcts_evasive_bot

    def test_capture_wins(self) -> None:
        bot = make_mcts_evasive_bot(iterations=50, seed=1)
        obs = _obs(
            own_tokens=(10, 20, 0, 0),
            opponent_tokens=((13, 5, 0, 0),),
            dice_value=3,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 0

    def test_capture_beats_escape(self) -> None:
        bot = make_mcts_evasive_bot(iterations=50, seed=1)
        obs = _obs(
            own_tokens=(10, 27, 0, 0),
            opponent_tokens=((13, 25, 0, 0),),
            dice_value=3,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 0

    def test_escape_wins_over_plain_move(self) -> None:
        bot = make_mcts_evasive_bot(iterations=50, seed=1)
        obs = _obs(
            own_tokens=(10, 20, 0, 0),
            opponent_tokens=((8, 40, 0, 0),),
            dice_value=3,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 0

    def test_escape_into_home_stretch(self) -> None:
        bot = make_mcts_evasive_bot(iterations=50, seed=1)
        obs = _obs(
            own_tokens=(40, 20, 0, 0),
            opponent_tokens=((37, 40, 0, 0),),
            dice_value=4,
            legal_actions=(0, 1),
        )
        assert bot(obs) == 0

    def test_returns_legal_action_when_no_priority(self) -> None:
        bot = make_mcts_evasive_bot(iterations=50, seed=1)
        obs = _obs(
            own_tokens=(10, 20, 0, 0),
            opponent_tokens=((40, 0, 0, 0),),
            dice_value=3,
            legal_actions=(0, 1),
        )
        assert bot(obs) in (0, 1)

    def test_returns_none_when_no_legal_actions(self) -> None:
        bot = make_mcts_evasive_bot(iterations=50)
        assert bot(_obs(legal_actions=())) is None

    def test_deterministic_with_same_seed(self) -> None:
        observations = [
            _obs(own_tokens=(10, 0, 0, 0), opponent_tokens=((8, 0, 0, 0),), dice_value=3, legal_actions=(0,)),
            _obs(own_tokens=(10, 20, 0, 0), opponent_tokens=((13, 5, 0, 0),), dice_value=3, legal_actions=(0, 1)),
            _obs(own_tokens=(1, 2, 3, 4), dice_value=2, legal_actions=(0, 1, 2, 3)),
        ]
        bot_a = make_mcts_evasive_bot(iterations=50, seed=123)
        bot_b = make_mcts_evasive_bot(iterations=50, seed=123)
        assert [bot_a(obs) for obs in observations] == [
            bot_b(obs) for obs in observations
        ]

    def test_always_returns_legal_action(self) -> None:
        bot = make_mcts_evasive_bot(iterations=40, seed=42)
        rng = random.Random(0)
        for _ in range(20):
            legal = tuple(rng.sample(range(4), rng.randint(1, 4)))
            own = tuple(rng.randint(0, 44) for _ in range(4))
            obs = _obs(
                own_tokens=own, dice_value=rng.randint(1, 6), legal_actions=legal
            )
            action = bot(obs)
            assert action in legal

    def test_plays_full_game(self) -> None:
        bots = (
            make_mcts_evasive_bot(iterations=50, seed=3),
            make_mcts_evasive_bot(iterations=50, seed=4),
        )
        result, _ = run_simulation(bots, GameConfig(), seed=42)
        assert result.winner in (0, 1)