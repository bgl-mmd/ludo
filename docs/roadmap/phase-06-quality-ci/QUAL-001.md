# QUAL-001 — Property and invariant tests

**ID:** QUAL-001
**Title:** Property and invariant tests
**Phase:** 6
**Depends on:** SIM-001

## Goal

Enforce invariants across many seeded games (spec 09 §2.6).

## Scope

- Run many seeded games (deterministic bots) and assert: at most one token per cell; positions never decrease; illegal actions never mutate state; completed games reject moves; legal actions are a subset of all actions; each legal action produces a valid state; games always terminate.
- Plain pytest loops over seeds (no `hypothesis` dependency).

## Out of scope

- Fuzzing frameworks, coverage gating.

## Acceptance criteria

- All spec 09 §2.6 invariant tests pass over a fixed seed range.
- Suite runs in reasonable time (< 120 s per spec 09 §6).

## Tests

- `test_invariant_*` list from spec 09 §2.6.