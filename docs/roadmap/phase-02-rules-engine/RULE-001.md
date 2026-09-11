# RULE-001 — Dice module

**ID:** RULE-001
**Title:** Dice module (seeded RNG, roll_dice)
**Phase:** 2
**Depends on:** DOMAIN-001

## Goal

The engine's only source of randomness (spec 05 §7).

## Scope

- `create_rng(seed: int | None) -> random.Random`.
- `roll_dice(state, rng) -> tuple[GameState, int]` — sets `dice_value`, returns the value (1–6). Does not touch `consecutive_sixes`.

## Out of scope

- Turn logic, extra turns, actions.

## Acceptance criteria

- Same seed produces the same sequence; different seeds (usually) differ.
- Returned value is always in `1..dice_sides`.
- Returns a new `GameState`; input state is unchanged.
- Randomness is consumed only through the injected `rng`.

## Tests

- Seeded determinism (two RNGs with same seed yield same rolls).
- Value range across many rolls.
- Immutability: input state unchanged.
- A fixed-value dice source (e.g. `fixed_dice([6,3,1,5])`, spec 09 §3.2) drives `roll_dice` to verify returned values.