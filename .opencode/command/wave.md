---
description: Implement and review one wave of the roadmap, e.g. /wave 1
agent: build
---

Implement and review wave "$ARGUMENTS" of the Ludo implementation roadmap.

1. Read `docs/implementation-roadmap.md`. Find the task IDs listed in the wave table for wave "$ARGUMENTS" (wave 0 is already complete; start at wave 1).
2. Verify every task in the previous wave is complete and its tests pass before starting; if not, stop and report which tasks are blocking.
3. For each task in this wave, run the implement-then-review flow in a single pass: delegate to the `builder` subagent, then to the `reviewer` subagent, and re-delegate any task that does not PASS. Run the task's own tests and then the full `pytest tests/` suite after the wave.
4. Where possible, delegate the tasks of the wave to parallel subagents in a single message (concurrent calls) as the roadmap recommends. If parallel execution is not possible, run the tasks in phases of multiple tasks, still re-delegating any task that does not PASS before moving on.
5. Never start wave *n* until all tasks in wave *n-1* are done and their tests pass.

Report a per-task table with the task IDs, their PASS/FAIL verdict, and the final full-suite test result.
