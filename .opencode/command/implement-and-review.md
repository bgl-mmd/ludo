---
description: Implement then review a roadmap task by ID, e.g. /implement-and-review DOMAIN-001
agent: build
---

Implement and review the roadmap task "$ARGUMENTS" in docs/implementation-roadmap.md in one pass.

1. Find the task by ID and delegate to the `builder` subagent to implement it per its own instructions. Confirm its tests pass.
2. Then delegate to the `reviewer` subagent to verify the task against its acceptance criteria.
3. If the reviewer reports FAIL, re-delegate to the `builder` to fix the reported issues, then re-run the `reviewer` until it PASSES or until it is clear the task cannot be satisfied.

Report the final PASS/FAIL verdict per acceptance criterion.
