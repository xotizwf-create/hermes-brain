---
id: liniya-decisions
type: project
project: liniya
tags: [decisions, adr]
updated: 2026-08-22
secret_refs: []
---

# Линия — decisions

## 2026-08-22 — Register production routing
- **Context:** project and live access existed, but Hermes Brain had no route to find them.
- **Decision:** register `liniya`, its local repo, GitHub, host, immutable release layout, services and secret references without secret values.
- **Consequences:** future sessions route directly to this dossier and must use off-box builds plus the universal server preflight.

## 2026-08-21 — PostgreSQL-only self-hosting
- **Decision:** PostgreSQL is the only production source of truth; SQLite remains only for historical import support. Web admin uses `ADMIN_HASH`; Telegram is consumed by a resilient polling service.
