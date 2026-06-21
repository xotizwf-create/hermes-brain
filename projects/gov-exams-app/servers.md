---
id: gov-exams-app-servers
type: project
project: gov-exams-app
tags: [servers, access]
updated: 2026-05-31
secret_refs: [proj/gov-exams-app/server/env, proj/gov-exams-app/ssh/root, proj/gov-exams-app/database/url]
---

# Лёгкие экзамены / LiteExams — servers & access

> Credentials are referenced by NAME only. Real values live in the secure zone. Never print or commit secrets.

## Production
- Host alias: `prod-liteexams`
- Public host/domain: `liteexams.ru`
- Working dir/services: уточнить через secure-доступ перед работами.
- Access: secrets are present in the secure project folder; use the secure-access workflow and never expose values.

## Critical constraints
- Production host is memory-constrained; previous server-side Node/Vite work caused OOM.
- Do not run full builds, full tests, migrations, or experimental instances on the production box.
- Build and run full checks off-server; upload prebuilt release artifacts; do only lightweight smoke checks on production.
- Never run tests, trial/dev instances, or migrations against the live production database.

## MCP / admin operations
- Archived project: do not read or start `gov_exams_tokens` during routine project digests or background checks.
- Use `gov_exams_tokens` only when the owner explicitly asks to check or change LiteExams/Gov Exams tokens.
- If a user asks to reset/rotate a token and does not specify mobile/PC/both, clarify first.
- When rotating mobile, rotate only mobile; do not touch desktop unless explicitly requested.
- New token values must be shown only once.

## Mandatory preflight
Before any server work, read and follow `engineering/server-preflight.md`.
