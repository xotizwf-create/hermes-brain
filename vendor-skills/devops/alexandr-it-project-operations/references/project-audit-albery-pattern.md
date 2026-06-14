# Project Audit Kickoff Pattern — Albery Example

This reference captures a reusable project-audit kickoff pattern from the Albery session. Keep it as an example for future messy multi-component projects, not as a live state record.

## Context pattern

Use this when a project has several intertwined parts, for example:

- web backend and frontend
- database and migrations
- MCP server or AI-agent tooling
- external integrations
- scheduled sync jobs
- manual recommendation/approval flows
- scattered or stale documentation

## Safe first-pass workflow

1. Start with read-only repository inspection.
2. Avoid production, live databases, external writes, and secret disclosure.
3. Identify the real shape of the project from files, docs, tests, and CI.
4. Run only low-risk verification such as syntax checks or tests that do not need live credentials.
5. Compare documentation claims with code reality.
6. Report mismatches as audit findings, not as immediate refactor tasks.
7. End with the next phase: data-flow mapping before standardization.

## Useful audit dimensions

- Component map: backend, frontend, database, MCP, agents, cron/sync scripts, integrations, manual processes.
- Documentation drift: outdated root README, template leftovers, conflicting server/deploy descriptions, missing current overview.
- Architecture risk: very large monolith files, god-object UI/backend/MCP files, mixed legacy API and MCP-first paths.
- Safety posture: tests, migrations, CI, env examples, security workflows, secret handling, production separation.
- Operational clarity: what is automatic vs manual, where recommendations are generated, who approves/sends them, what writes to external systems.

## Reporting style that worked

- Tell Александр explicitly that production and secrets were not touched.
- Summarize concrete findings, separating “what exists”, “what is inconsistent”, and “what is good”.
- Keep the next step focused: build a data-flow map in the format `source → processor → tables/state → MCP/API/UI → manual/automatic action`.
- Finish with a short Russian summary in a natural voice, without the `Готово:` prefix.
