---
id: testing
type: engineering
tags: [tests,ci,fixtures,regression]
updated: 2026-05-29
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
