# RULE-005 — Win detection

**ID:** RULE-005
**Title:** Win detection
**Phase:** 2
**Depends on:** DOMAIN-001

## Goal

Detect when a player has filled all four home-stretch cells (spec 01 §5.5, OQ-14/15).

## Scope

- `check_win(state, player, config)` — true iff all 4 of the player's tokens are in `41..44`.
- `is_game_over(state)` — true iff any player has won.

## Out of scope

- Result construction, turn transitions, applying moves.

## Acceptance criteria

- 4 tokens in `41..44` ⇒ win (each cell distinct is guaranteed by the one-token-per-cell invariant).
- 3 tokens at `44` is not a win.

## Tests

- `test_win_when_all_4_tokens_at_44`, `test_no_win_with_3_tokens_at_44`, `test_win_detected_after_move` (spec 09).