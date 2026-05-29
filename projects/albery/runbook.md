---
id: albery-runbook
type: project
project: albery
tags: [runbook, ops]
updated: 2026-05-29
secret_refs: []
---

# Albery — runbook

## Service
```bash
systemctl status albery --no-pager
systemctl restart albery
journalctl -u albery -n 120 --no-pager
```

## Webhooks (check without printing secrets)
```bash
cd /var/www/albery
bitrix_secret=$(awk -F= '$1=="BITRIX_EVENT_SECRET"{print $2; exit}' .env)
zoom_secret=$(awk -F= '$1=="ZOOM_EVENT_SECRET"{print $2; exit}' .env)
curl -sS "https://mcp.m4s.ru/bitrix/events/tasks/$bitrix_secret"
curl -sS "https://mcp.m4s.ru/zoom/events/$zoom_secret"
```
- Bitrix events: `OnTaskAdd/Update/Delete` → queue `bitrix_task_events`.
- Zoom events: `recording.transcript_completed`, `recording.completed` → queue `zoom_recording_events`.

## Cron
- Daily external sync 18:00 Europe/Moscow: `/etc/cron.d/albery-daily-sync`
- Logs: `/var/log/albery/daily-sync.log`, `daily-sync.cron.log`
- Postgres backup cron: `/etc/cron.d/albery-postgres-backup`

## Backups
- Location: `/var/backups/albery/postgres/`. Restore: see `engineering/database.md` + `postgres-production` skill.

## After syncing the brain
Brain mirror lives at `/root/.hermes/agent-knowledge`. See `skills/update-knowledge/`.
