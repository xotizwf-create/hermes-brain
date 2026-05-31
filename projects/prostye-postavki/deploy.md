---
id: prostye-postavki-deploy
type: project
project: prostye-postavki
tags: [deploy]
updated: 2026-05-31
secret_refs: []
---

# Простые поставки — deploy

> Project-specific deploy flow is not fully documented yet. Treat production as critical.

## Current rule
Do not deploy blindly. First collect server details from secure access, inspect current service layout, and run the universal server preflight.

## Flow draft
1. Confirm scope and rollback plan.
2. Inspect resources and live services with `engineering/server-preflight.md`.
3. Build/test off production when possible.
4. Upload or pull only a verified release.
5. Restart/switch atomically if the service layout supports it.
6. Run a read-only smoke check: web availability, MCP availability, database connectivity without exposing secrets.

## Post-deploy checks
- Application opens.
- MCP server responds to safe/read-only tool discovery.
- Contract/product/КП flows are not broken.
- Logs show no new errors.

## Rollback
Уточнить после документирования текущего способа деплоя и расположения релизов.
