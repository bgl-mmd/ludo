# QUAL-002 — CI workflow

**ID:** QUAL-002
**Title:** CI workflow
**Phase:** 6
**Depends on:** FOUND-001

## Goal

Run the test suite automatically on every commit (spec 09 §6).

## Scope

- A minimal CI workflow (e.g. GitHub Actions) that installs dev deps and runs `pytest tests/` (optionally with coverage) on push.

## Out of scope

- Coverage thresholds, deployment, packaging/release.

## Acceptance criteria

- The workflow file exists and passes on a clean checkout.

## Tests

- Manual: run the workflow's command locally (`pytest tests/`).