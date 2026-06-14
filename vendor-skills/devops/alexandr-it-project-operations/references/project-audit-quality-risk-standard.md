# Project Audit Quality/Risk Stage Pattern

Use this reference when Александр asks to continue a project audit after component/data-flow/MCP boundary mapping. This captures the reusable Stage C pattern from the Albery audit without preserving one-off task progress.

## Goal

Produce a read-only quality and standardization audit that tells the owner what is technically fragile, what should be standardized first, and what must not be touched yet. Do not jump directly into refactoring.

## Safety boundaries

- Treat Stage C as read-only unless the user explicitly asks for patches.
- Do not touch production, secrets, live databases, migrations, or external integrations.
- Lightweight local/static checks are OK; heavy builds, live syncs, real DB tests, and migrations require a separate decision.
- If tests fail because the audit environment lacks dependencies, record it as an audit-environment limitation, not as proof the project is broken.

## Inventory to collect

1. Largest files and central modules by line count.
2. Route/API counts and which routes are legacy vs active.
3. Test layout: unit, integration, MCP/API, DB, smoke, frontend.
4. CI workflows: dependency install, DB service containers, frontend build/typecheck, security audit.
5. Dependency manifests and dev/runtime split.
6. Database model: base schema, migrations, migration runner, hot/always-applied migrations.
7. Documentation set: root README, domain docs, MCP/API docs, agent/runbook docs, deployment docs.
8. Import/package risks such as project folders named like installed packages.
9. Duplicate control surfaces: UI, HTTP API, MCP, CLI/scripts, cron, webhooks.

## Analysis heuristics

- Flag god-object files when one file carries unrelated domains such as routes, auth, DB, integrations, reports, AI workflows, and sends.
- Separate “project is broken” from “project is growing faster than its standards.”
- Compare docs against code behavior; stale read-only claims are high risk when tools can write/send.
- For migrations, distinguish a valid “base schema + numbered migrations” pattern from a missing migration; document the intended standard.
- Treat AI instruction/prompt writes as runtime behavior mutations, not simple content edits.
- Treat external-send/delete/create actions as requiring preview + explicit owner approval + code-level confirm gates.

## Recommended output shape

Create a stage-specific markdown artifact, e.g. `audit-stage-c-quality-risks.md`, with:

- mode/safety statement;
- linked previous audit artifacts;
- short executive summary;
- component inventory;
- complexity metrics;
- tests/CI assessment;
- database/migration assessment;
- documentation drift;
- duplicated control surfaces;
- prioritized risks: critical / important / later;
- staged stabilization plan;
- first safe patch set;
- explicit “do not do yet” list.

## First safe patch set after Stage C

Prefer small, reversible changes before any large refactor:

1. Fix package/import hygiene (for example add missing `__init__.py` when a local package conflicts with an installed package name).
2. Add or enforce confirm-gates for the most obvious external action.
3. Add regression tests around the new safety gate.
4. Update docs that falsely describe write/action surfaces as read-only.
5. Update the root project overview so future agents/operators know the current system shape.

## Pitfalls

- Do not propose a big rewrite just because central files are huge; first add safety gates and tests.
- Do not delete or disable legacy API/UI solely from static evidence; verify production mode and user needs separately.
- Do not run live DB migrations as part of an audit.
- Do not store exact line counts or one-session artifact filenames in memory; they belong in the audit report, not persistent memory.
