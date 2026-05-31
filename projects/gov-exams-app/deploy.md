---
id: gov-exams-app-deploy
type: project
project: gov-exams-app
tags: [deploy]
updated: 2026-05-31
secret_refs: []
---

# Лёгкие экзамены / LiteExams — deploy

## Current deploy principle
Because production is memory-constrained, prefer local/CI build + prebuilt release upload. Do not build on production unless a fresh preflight proves there is safe headroom and the step is capped.

## Safe flow draft
1. Inspect repo and make changes locally/off-server.
2. Run tests/typecheck/build off production.
3. Package a timestamped release artifact.
4. On production: run server preflight, verify backups/rollback, upload release, install only lightweight runtime dependencies if needed.
5. Atomically switch release / restart service.
6. Run lightweight smoke checks only.

## Post-deploy checks
- Web app responds.
- Login/subscription flows are not broken.
- Token/device-binding behavior is intact.
- Logs show no OOM, DB connection drops, or new application errors.

## Rollback
Use the previous timestamped release if available. Exact release directory and service names must be confirmed before the next deploy.
