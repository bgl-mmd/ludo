# Ludo — Implementation Roadmap

Dependency-ordered plan. Each task is one focused coding-agent session.

- **Architecture:** `docs/architecture.md`
- **Open questions:** `docs/roadmap/open-questions.md`
- **Requirements coverage:** `docs/roadmap/requirements-coverage.md`

## How to use

1. Read this index to find the current task (first ready task: `FOUND-001`).
2. Open that task's file (linked in the table below). It is self-contained:
   Goal, Scope, Out of scope, Acceptance criteria, Tests.
3. A task is ready when all tasks in its `Depends on` are complete.
4. After each task, run its tests (`pytest tests/`). See `docs/architecture.md` §10.

## Vertical slice

Validate the architecture early:

```
new_game → roll_dice (RULE-001) → get_legal_actions (RULE-004)
        → apply_action (ENGINE-002) → is_game_over
```

After `ENGINE-002` a game can be driven by hand ("first legal action").
`SIM-001` completes the slice with a full two-bot loop.

## Phases

| Phase | Name                                   |
| ----- | -------------------------------------- |
| 1     | Foundation & Domain                    |
| 2     | Rules Engine                           |
| 3     | Core Engine                            |
| 4     | Observation, Bots & Simulation         |
| 5     | Competition Protocol                   |
| 6     | Quality & CI                           |

## Task index (dependency order)

Critical path: `FOUND-001 → DOMAIN-001 → RULE-002/003 → RULE-004 → ENGINE-002 →
OBS-001 → BOT-001 → SIM-001`.

| ID          | Title                                       | File                                                    |
| ----------- | ------------------------------------------- | ------------------------------------------------------- |
| FOUND-001   | Project scaffold and test harness           | `phase-01-foundation/FOUND-001.md`                     |
| DOMAIN-001  | Core data types                             | `phase-01-foundation/DOMAIN-001.md`                     |
| DOMAIN-002  | Coordinate conversion                       | `phase-01-foundation/DOMAIN-002.md`                     |
| RULE-001    | Dice module                                 | `phase-02-rules-engine/RULE-001.md`                     |
| RULE-002    | Destination computation                     | `phase-02-rules-engine/RULE-002.md`                     |
| RULE-003    | Occupancy and capture                       | `phase-02-rules-engine/RULE-003.md`                     |
| RULE-004    | Legal action generation and validation      | `phase-02-rules-engine/RULE-004.md`                     |
| RULE-005    | Win detection                               | `phase-02-rules-engine/RULE-005.md`                     |
| RULE-006    | Turn management                             | `phase-02-rules-engine/RULE-006.md`                     |
| ENGINE-001  | new_game                                    | `phase-03-core-engine/ENGINE-001.md`                    |
| ENGINE-002  | apply_action (state reducer)                | `phase-03-core-engine/ENGINE-002.md`                    |
| ENGINE-003  | Game result extraction                      | `phase-03-core-engine/ENGINE-003.md`                    |
| OBS-001     | Observation builder                         | `phase-04-observation-bots-simulation/OBS-001.md`       |
| BOT-001     | Example bots (random, greedy)               | `phase-04-observation-bots-simulation/BOT-001.md`       |
| SIM-001     | Simulation runner (vertical slice)          | `phase-04-observation-bots-simulation/SIM-001.md`       |
| SIM-002     | Batch simulation                            | `phase-04-observation-bots-simulation/SIM-002.md`       |
| SIM-003     | Statistics aggregation                      | `phase-04-observation-bots-simulation/SIM-003.md`       |
| SIM-004     | History export, import, replay              | `phase-04-observation-bots-simulation/SIM-004.md`       |
| COMP-001    | Board parsing and observation mapping       | `phase-05-competition-protocol/COMP-001.md`             |
| COMP-002    | Competition HTTP client                     | `phase-05-competition-protocol/COMP-002.md`             |
| COMP-003    | Competition runner and callback handler     | `phase-05-competition-protocol/COMP-003.md`             |
| QUAL-001    | Property and invariant tests                | `phase-06-quality-ci/QUAL-001.md`                       |
| QUAL-002    | CI workflow                                 | `phase-06-quality-ci/QUAL-002.md`                       |

All paths are relative to `docs/roadmap/`.