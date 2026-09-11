# ENGINE-003 — Game result extraction

**ID:** ENGINE-003
**Title:** Game result extraction
**Phase:** 3
**Depends on:** ENGINE-002

## Goal

Convert a finished game into a `GameResult` (spec 05 §3, spec 07 §5).

## Scope

- `get_result(state, player_names) -> GameResult` — winner index/name, `turn_count`, `error_count`; winner `None` for a draw.

## Out of scope

- Win detection itself (RULE-005), statistics aggregation (SIM-003).

## Acceptance criteria

- Winner, turn count, and error count reflect the finished state.
- A finished game without a winner yields `winner=None` (draw).

## Tests

- Win/loss result fields; turn count; error count.