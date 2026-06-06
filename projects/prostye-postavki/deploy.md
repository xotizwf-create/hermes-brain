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
Do not deploy blindly. Production code lives in `/var/www/prostye-postavki/app` and must stay synchronized with GitHub repo `xotizwf-create/prostavki`. First run the universal server preflight, inspect the working tree, commit/push source changes, then verify service health.

## Flow draft
1. Confirm scope and rollback plan.
2. Inspect resources and live services with `engineering/server-preflight.md`.
3. Build/test off production when possible.
4. Upload or pull only a verified release.
5. Restart/switch atomically if the service layout supports it.
6. Run a read-only smoke check: web availability, MCP availability, database connectivity without exposing secrets.

## Git synchronization rule
- The production working tree must be clean after any change: no uncommitted edits and no stray temporary backup files.
- Commit production code changes to `xotizwf-create/prostavki` and keep `main` fast-forwarded to the production commit.
- Never leave a hotfix only on the server. If a change is deployed or tested in production, finish by pushing the exact tracked code to GitHub and verifying GitHub `main` points to the same commit as the production checkout.

## Post-deploy checks
- Application opens.
- MCP server responds to safe/read-only tool discovery.
- Contract/product/КП flows are not broken.
- Logs show no new errors.

## Rollback
Уточнить после документирования текущего способа деплоя и расположения релизов.
