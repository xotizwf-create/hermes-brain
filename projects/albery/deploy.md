---
id: albery-deploy
type: project
project: albery
tags: [deploy]
updated: 2026-05-29
secret_refs: []
---

# Albery — deploy

> General principles: `engineering/deployment.md`.

## Flow
1. Work in a branch off `main` (`feature/...`, `bugfix/...`, `codex/...`), one task per branch.
2. Push to GitHub. Do not push directly to `main` without explicit ask.
3. On server: pull, apply migrations, restart service.

## Commands (on server / via _deploy_helper.py)
```bash
cd /var/www/albery
git status --short && git rev-parse --short HEAD
.venv/bin/python scripts/ensure_postgres.py    # apply migrations
systemctl restart albery
```

## Post-deploy checks
```bash
systemctl status albery --no-pager
journalctl -u albery -n 120 --no-pager
tail -n 120 /var/log/albery/daily-sync.log
nginx -t && systemctl reload nginx
```

## Notes
- Backend listens only on `127.0.0.1:5002`; public access via Nginx.
- Local watcher `scripts/watch_github_updates.ps1` fast-forwards only `main`.
- Push to GitHub before/after server deploy so `update_server.sh` won't overwrite manual edits.
