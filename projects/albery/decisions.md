---
id: albery-decisions
type: project
project: albery
tags: [decisions, adr]
updated: 2026-05-29
secret_refs: []
---

# Albery — decisions (ADR)

Append-only, newest on top.

## 2026-05-29 — Brain extracted to isolated repo
- **Context:** agent knowledge lived inside the website repo; needed a multi-project brain.
- **Decision:** moved knowledge to standalone `hermes-brain` repo; albery is the first project.
- **Consequences:** brain history decoupled from project; synced to `/root/.hermes/agent-knowledge`.

## (historical) Daily sync cron, not hourly
- Big external sync moved to daily 18:00 Europe/Moscow (`/etc/cron.d/albery-daily-sync`).

## (historical) Incremental Zoom sync + webhooks
- Skip unchanged recordings; added Zoom + Bitrix outgoing webhooks for near-realtime sync.
