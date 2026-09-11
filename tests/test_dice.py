import random

from ludo import CompetitionState, GameState
from ludo.dice import create_rng, roll_dice

INITIAL_TOKENS = ((0, 0, 0, 0), (0, 0, 0, 0))


def _initial_state(state: CompetitionState = CompetitionState.NONE) -> GameState:
    return GameState(
        tokens=INITIAL_TOKENS,
        current_player=0,
        dice_value=None,
        consecutive_sixes=0,
        game_over=False,
        winner=None,
        error_count=0,
        turn_number=0,
        state=state,
    )


class FixedDice:
    def __init__(self, values: list[int]) -> None:
        self._values = values
        self._index = 0

    def randint(self, a: int, b: int) -> int:
        value = self._values[self._index % len(self._values)]
        self._index += 1
        return value


class TestCreateRng:
    def test_returns_random_instance(self) -> None:
        rng = create_rng(42)
        assert isinstance(rng, random.Random)

    def test_none_seed_allowed(self) -> None:
        rng = create_rng()
        assert isinstance(rng, random.Random)

    def test_same_seed_same_sequence(self) -> None:
        rng1 = create_rng(42)
        rng2 = create_rng(42)
        assert [rng1.randint(1, 6) for _ in range(20)] == [
            rng2.randint(1, 6) for _ in range(20)
        ]


class TestRollDice:
    def test_seeded_determinism(self) -> None:
        state1 = _initial_state()
        state2 = _initial_state()
        rng1 = create_rng(7)
        rng2 = create_rng(7)
        rolls1 = []
        rolls2 = []
        for _ in range(20):
            state1, value1 = roll_dice(state1, rng1)
            state2, value2 = roll_dice(state2, rng2)
            rolls1.append(value1)
            rolls2.append(value2)
        assert rolls1 == rolls2

    def test_value_range_across_many_rolls(self) -> None:
        state = _initial_state()
        rng = create_rng(123)
        for _ in range(1000):
            state, value = roll_dice(state, rng)
            assert 1 <= value <= 6

    def test_sets_dice_value_on_new_state(self) -> None:
        state = _initial_state()
        new_state, value = roll_dice(state, create_rng(0))
        assert new_state is not state
        assert new_state.dice_value == value

    def test_input_state_unchanged(self) -> None:
        state = _initial_state()
        roll_dice(state, create_rng(0))
        assert state == _initial_state()

    def test_consecutive_sixes_untouched(self) -> None:
        state = _initial_state()
        state = GameState(**{**state.__dict__, "consecutive_sixes": 2})
        new_state, _ = roll_dice(state, create_rng(0))
        assert new_state.consecutive_sixes == 2
        assert state.consecutive_sixes == 2

    def test_fixed_dice_cycle(self) -> None:
        state = _initial_state()
        dice = FixedDice([6, 3, 1, 5])
        values = []
        for _ in range(8):
            state, value = roll_dice(state, dice)
            values.append(value)
        assert values == [6, 3, 1, 5, 6, 3, 1, 5]

    def test_fixed_dice_sets_dice_value(self) -> None:
        state = _initial_state()
        new_state, value = roll_dice(state, FixedDice([6]))
        assert value == 6
        assert new_state.dice_value == 6