# DOMAIN-001 — Core data types

**ID:** DOMAIN-001
**Title:** Core data types (GameConfig, GameState, MoveRecord, GameResult, Observation, CompetitionState)
**Phase:** 1
**Depends on:** FOUND-001

## Goal

Implement all frozen dataclasses and the competition state enum used throughout the engine (spec 05 §4/§5/§12, spec 06 §2).

## Scope

- `GameConfig` with defaults `num_players=2`, `tokens_per_player=4`, `board_size=40`, `home_stretch_size=4`, `dice_sides=6`, `max_consecutive_sixes=2`.
- `GameState` with the exact fields from spec 05 §4.
- `MoveRecord` (turn, player, action, dice_value, destination, captured, is_extra_turn, error).
- `GameResult` (winner index/name or None for draw, turn_count, error_count).
- `Observation` with the exact fields from spec 06 §2.
- `CompetitionState` enum (`NONE`, `WAIT_FOR_START`, `WAIT_FOR_YOU`, `WAIT_FOR_MOVE`, `END_YOU_WIN`, `END_YOU_LOST`, `END_EQUALS`).
- All types `@dataclass(frozen=True)`.

## Out of scope

- All behavior: coordinate conversion, rules, transitions, observation building.

## Acceptance criteria

- Every type is constructible with the documented defaults.
- Instances are immutable (attribute assignment raises `FrozenInstanceError`).
- Field types match the specs exactly.

## Tests

- Construction with defaults and with explicit values.
- Immutability: setting an attribute raises.
- `GameState` initial fields match spec 09 §2.1 initial-state expectations.