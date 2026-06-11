---
id: testing
type: engineering
tags: [tests,ci,fixtures,regression]
updated: 2026-06-11
secret_refs: []
---

# Testing Standards

Use this guide when writing, changing, or running tests.

## Defaults

- Add tests where behavior changes, bug fixes, migrations, parsing, auth, billing, integrations, or user workflows are touched.
- Keep tests focused on the changed behavior.
- Prefer deterministic tests with explicit fixtures.
- Do not call live external services in normal test runs unless the project already has that convention.

## Test Types

- Unit tests: pure logic, validation, parsing, formatting, policy decisions.
- Integration tests: database queries, migrations, service boundaries, API clients with mocked providers.
- Smoke tests: production deploy checks, health endpoints, key CLI commands.
- Regression tests: reproduce the bug first, then prove the fix.

## Workflow

1. Inspect existing test framework and naming conventions.
2. Add or update the smallest meaningful tests.
3. Run targeted tests first.
4. Run broader suites when shared code or contracts changed.
5. Report exactly what was run and what could not be run.

## CI is the proof — a coding task isn't done until CI is green (2026-06-11)

A change is **not finished** when the code "looks right" — it's finished when an
automated check confirms it. For any project that has CI, the agent must:

1. Work on a **branch**, never push straight to `main` (open a PR with a diff summary).
2. **Wait for CI** and read the result via `gh pr checks <n>` / `gh run view`. Green = done; red = not done.
3. Never make CI green by **weakening the test** (deleting asserts, loosening to `assert True`,
   editing expected values to match buggy output). If a test fails, decide *honestly* whether the
   **code** or the **test** is wrong, and fix that. A test changed only to pass is worse than no test.
4. Heavy suites run **off the box** (GitHub Actions / CI), never against a fragile prod host or the
   live prod DB — CI spins its own throwaway services (e.g. a `postgres:16` service container).

### Reference pattern — `prostye-postavki` CI (the template to copy)
First CI added 2026-06-11 (`xotizwf-create/prostavki`, `.github/workflows/ci.yml`), proven green:
- **backend-smoke** (blocking): a `postgres:16` *service container* + `DATABASE_URL` env, then
  `pytest backend/tests`. The app imports against a real empty DB (it runs `ensure_*_schema()` at
  import — so a pure no-DB import is impossible), hits `/api/health`, and unit-tests the pure helpers
  (`parse_number`, `normalize_json`, …). This catches syntax/import/dep/helper regressions cheaply.
- **frontend-build** (blocking): `npm ci` + `npm run build` — `vite build` doubles as the typecheck.
- **frontend-unit-tests** (non-blocking): runs `vitest` with **step-level** `continue-on-error`
  + a `::warning` to `$GITHUB_STEP_SUMMARY`, so pre-existing broken legacy tests stay *visible* but
  don't block the pipeline or silently rot. (Two parsing tests here assert quantity-like `price`
  values — a real parser-vs-test discrepancy still needing triage; do not paper over it.)
- Cosmetics that paid off: `concurrency: cancel-in-progress` (saves minutes), `cache: pip`/`npm`.

When onboarding a new project, **add this CI shape early** — it's the single biggest lever on code
quality (verifiable goals, 12-factor), bigger than any model/prompt tweak.
