# DOMAIN-002 — Coordinate conversion

**ID:** DOMAIN-002
**Title:** Coordinate conversion (player-relative ↔ global)
**Phase:** 1
**Depends on:** DOMAIN-001

## Goal

Implement the centralized, pure coordinate conversion (spec 02 §4/§5).

## Scope

- `compute_begin_offsets(config)` → `(1, 21)` for 2 players.
- `player_to_global(player_pos, player, config)` and `global_to_player(global_pos, player, config)`.
- Special cases: `0` stays `0`; home-stretch positions `41–44` are private per player and are passed through unchanged (architecture §4).

## Out of scope

- Rules, occupancy, capture, legal actions, board topology/adjacency.

## Acceptance criteria

- All examples in spec 02 §4 hold exactly (identity, wraparound, begin/end offsets for both players, home yard `0`, home stretch unchanged).

## Tests

- `test_global_to_player_identity`, `test_player_to_global_identity`, `test_global_to_player_wraparound`, `test_player_to_global_wraparound`, `test_home_yard_always_zero`, `test_home_stretch_positions`, `test_begin_end_offsets_for_each_player` (spec 09 §2.2).