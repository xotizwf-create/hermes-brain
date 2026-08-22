---
id: liniya-incidents
type: project
project: liniya
tags: [incidents, postmortem]
updated: 2026-08-22
secret_refs: []
---

# Линия — incidents

## 2026-08-21 — PostgreSQL admin/referral failures
- **Impact:** specialist/admin surfaces failed or returned empty 500 responses.
- **Root causes:** SQLite-only timestamp SQL, an invalid correlated aggregate, and tables manually created under the `postgres` owner.
- **Fix:** PostgreSQL-correct SQL, inner-alias aggregation, JSON-safe API clients, and correct ownership/grants.
- **Prevention:** execute database-sensitive verification with the application role and keep regression tests in the project.

## 2026-05-31 — Shared LiteExams host OOM precedent
- **Impact:** server-side Node/Vite work on the constrained host caused OOM and live DB connection failures.
- **Prevention:** build/test off-box, preflight every server operation, never run experiments against live data, and keep atomic rollback.
