---
id: liniya-deploy
type: project
project: liniya
tags: [deploy, releases, rollback]
updated: 2026-08-22
secret_refs: [proj/liniya/ssh/root, proj/liniya/server/env]
---

# Линия — deploy

## Mandatory gates
1. Preserve unrelated local changes and confirm the exact `main` commit.
2. Locally run `npm run lint` and `npm test` (`npm test` includes the production build).
3. Before touching production run `engineering/server-preflight.md`. This host has no swap and must be treated as constrained.
4. Never run the build/full suite or point tests/trial processes at the live database.

## Release flow
1. Prepare the tested artifact/repository off-server.
2. Confirm `liniya-backup.timer` and the previous release/DB rollback path.
3. Transfer the release (Git bundle is supported when the server has no deploy key) into a new immutable `/opt/liniya/releases/<id>` directory.
4. Install only lightweight locked runtime dependencies if required. Run PostgreSQL migrations before the symlink switch and verify ownership/access with the application role.
5. Smoke-check without exposing secrets, atomically point `/opt/liniya/current` to the new release, then restart only `liniya.service` and `liniya-telegram-poller.service`.
6. Verify both services, `https://liteexams.ru`, authenticated web admin, Telegram admin and recent journals.

## Rollback
Keep the previous release. On failure, repoint `/opt/liniya/current`, restart the two Liniya services, verify HTTP/Telegram, and restore the PostgreSQL backup only when a data/schema rollback is actually required.
