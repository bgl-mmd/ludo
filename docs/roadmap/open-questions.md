# Open Questions

Only issues that genuinely require clarification or a recorded resolution.
Each has a chosen resolution; none block implementation.

1. **GameState coordinate system (global vs player-relative).**
   Spec 02 says global is the "internal engine representation"; the rule/legal
   action pseudocode (spec 04/05) operates on player-relative positions, and the
   global home-stretch mapping is undefined (OQ-1/OQ-2).
   **Resolution:** tokens stored per player in player-relative coordinates; the
   global frame is used only for cross-player capture checks; home stretch is
   private (no global mapping needed). Re-verify against real server responses.

2. **`max_consecutive_sixes` semantics (contradiction).**
   Spec 05 §5 default `max_consecutive_sixes = 2` with the check in spec 05 §10
   appears to grant two extra turns for a `6,6` sequence, contradicting
   "second consecutive 6 has no reward" (spec 01 §5.1, spec 03 §3.3).
   **Resolution:** `consecutive_sixes` is incremented for the current 6 before
   the check, so with default `2` the first 6 grants an extra turn and the
   second ends the turn.

3. **Illegal-action recovery (OQ-11).**
   Spec 03 §6 allows re-prompt or forced `Move(0)`; server behavior unspecified.
   **Resolution:** record error + force a pass (terminating, safe). Re-prompting
   is a possible later enhancement.

4. **First player determination (OQ-6).**
   Unspecified. **Resolution:** random from the seed.

5. **Random bot determinism (design note).**
   Spec 06's module-level `random_bot` uses global `random`, breaking simulation
   determinism. **Resolution:** bots are factory closures;
   `make_random_bot(seed)` owns a seeded RNG.

6. **Competition `Borad` spelling and `address` type (OQ-7/OQ-8).**
   Follow the spec literally (literal `Borad`; int for moves, string `"0"` for
   no-move), configurable if the live server differs.