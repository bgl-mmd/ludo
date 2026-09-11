# Requirements Coverage

Concise mapping between major specification requirements and tasks.

| Requirement (spec)                           | Tasks                                   |
| -------------------------------------------- | --------------------------------------- |
| Board layout & coordinate conversion (02)     | DOMAIN-002, COMP-001                    |
| Token states & movement rules (01 §4/§5.3)    | RULE-002, ENGINE-002                    |
| Entering the board on a 6 (01 §5.2)           | RULE-002, RULE-004                      |
| Dice values & extra-turn rules (01 §5.1)      | RULE-001, RULE-006, ENGINE-002          |
| Capturing / one token per cell (01 §5.4)      | RULE-003, ENGINE-002                    |
| Home stretch & winning (01 §5.5)              | RULE-002, RULE-005, ENGINE-002, ENGINE-003 |
| No valid move → Move(0) (01 §5.6)             | RULE-004, ENGINE-002, COMP-001          |
| Invalid actions & penalties (01 §6)           | ENGINE-002, COMP-002, COMP-003          |
| Game termination states (01 §7)               | RULE-005, ENGINE-003, COMP-001          |
| State machine (03)                            | RULE-006, ENGINE-002, OBS-001           |
| Action model (04)                             | RULE-004, ENGINE-002, COMP-001          |
| Functional engine API (05)                    | ENGINE-001…003, RULE-001…006            |
| Immutable state / pure transitions (05)       | DOMAIN-001, ENGINE-002, QUAL-001        |
| Bot interface & observation (06)              | OBS-001, BOT-001                        |
| Simulation runner (07 §1)                     | SIM-001                                 |
| Deterministic reproducibility (07 §4)         | RULE-001, SIM-001, QUAL-001             |
| Batch simulation (07 §3)                      | SIM-002                                 |
| Statistics collection (07 §5)                 | SIM-003                                 |
| Recording & replay (07 §6)                    | SIM-004                                 |
| Competition REST protocol (08)                | COMP-001, COMP-002, COMP-003            |
| Testing strategy (09)                         | every task; QUAL-001, QUAL-002          |
| RL environment (07 §7) — **future, not built** | boundary only; architecture §11        |