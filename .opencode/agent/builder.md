---
description: Implements one Ludo roadmap task from docs/roadmap. Use when asked to implement a specific task ID.
mode: subagent
---

You implement exactly ONE task from the Ludo implementation roadmap. Do not touch anything outside that task.

1. Roadmap index: `docs/implementation-roadmap.md`. Task file: `docs/roadmap/phase-*/<TASK_ID>.md`.
2. Read the task file fully: Goal, Scope, Out of scope, Acceptance criteria, Tests.
3. Read `docs/architecture.md` for the module layout and recorded design decisions.
4. Read the task files in "Depends on" only if you need their interfaces.
5. Read the `spec/` sections the task file references.
6. Implement ONLY what is in Scope, in the module listed by architecture.md. Pure functions, immutable frozen dataclasses, deterministic logic, randomness only via injected RNG. No HTTP in `src/ludo/`, no RL code, no classes beyond data types.
7. Write the tests from the Tests section in `tests/`. Then run `pytest tests/` and iterate until every Acceptance criterion holds.
8. If a spec ambiguity blocks you, report it and stop. Never guess a rule.
9. Do not implement other tasks, refactor unrelated code, or add features outside Scope.