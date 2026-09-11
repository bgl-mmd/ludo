# FOUND-001 — Project scaffold and test harness

**ID:** FOUND-001
**Title:** Project scaffold and test harness
**Phase:** 1
**Depends on:** —

## Goal

Create the `src/` package layout, packaging metadata, and a working pytest setup so every later task is testable.

## Scope

- `pyproject.toml` with `pytest` and `pytest-cov` dev dependencies.
- Package skeleton `src/ludo/__init__.py` and `src/competition/__init__.py`.
- `tests/` directory with `conftest.py` and one smoke test.
- Confirm `python -c "import ludo"` and `pytest tests/` work.

## Out of scope

- Any game logic, data types, CI configuration.

## Acceptance criteria

- `pytest tests/` runs and the smoke test passes.
- `import ludo` succeeds.
- `pytest tests/ --cov=ludo` executes without error.

## Tests

- Smoke test asserting the `ludo` package imports.