---
id: liniya-runbook
type: project
project: liniya
tags: [runbook, ops]
updated: 2026-08-22
secret_refs: []
---

# Линия — runbook

## Routine checks
```bash
systemctl is-active liniya.service liniya-telegram-poller.service caddy.service postgresql.service
readlink -f /opt/liniya/current
curl -fsS -o /dev/null -w '%{http_code}\n' https://liteexams.ru/
journalctl -u liniya.service -u liniya-telegram-poller.service -n 100 --no-pager
```

## Backups
- Daily timer: `liniya-backup.timer` / `liniya-backup.service`.
- Before schema/data migrations, confirm the timer's last result and create/verify a PostgreSQL rollback backup.

## Local validation
```powershell
npm run lint
npm test
```

## Troubleshooting
- Site 502/503 → check `liniya.service`, port 3000 and Caddy, then recent journals.
- Telegram silent → check `liniya-telegram-poller.service`, its offset state and Telegram API errors; never print the token.
- Admin JSON/UI failure → inspect `/api/telegram/admin` and `/api/admin/analytics`; every path must return JSON and clients must tolerate non-JSON proxy failures.
- Database permission errors after migration → verify table/sequence owner or grants using the runtime application role.
