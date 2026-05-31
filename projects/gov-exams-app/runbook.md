---
id: gov-exams-app-runbook
type: project
project: gov-exams-app
tags: [runbook, ops]
updated: 2026-05-31
secret_refs: []
---

# Лёгкие экзамены / LiteExams — runbook

## Token operations
Use the connected `gov_exams_tokens` MCP tools:
- Check user token status safely without revealing token values.
- Rotate desktop token only when PC/desktop is requested.
- Rotate mobile token only when mobile is requested.
- Ask for clarification if token type is not specified.
- After rotation, verify safe status and show the newly generated token only once.

## Backups
Before risky operations, verify backups and identify the restore path. Do not mutate live data without a backup/rollback plan.

## Troubleshooting
- Users see device-binding/“another device” problems → check token/device binding state via MCP first.
- Server memory pressure → do not start builds; check resources and consider off-server release preparation.
- DB errors after deploy → stop, preserve logs, verify service health and DB connectivity without printing secrets.
