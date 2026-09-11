---
description: Implement a roadmap task by ID, e.g. /implement DOMAIN-001
agent: build
---

Find the roadmap task "$ARGUMENTS" in docs/implementation-roadmap.md and delegate to the `builder` subagent with the task ID. Ask the builder to implement it per its own instructions and report the result, including the tests that were run.