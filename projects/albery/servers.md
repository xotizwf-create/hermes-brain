---
id: albery-servers
type: project
project: albery
tags: [servers, access]
updated: 2026-05-30
secret_refs: [proj/albery/ssh/root]
---

# Albery — servers & access

> Credentials by NAME only. Real values: local `.env.local` (`Host_IP`, `Host_User`,
> `Host_Password`) and server `.env`. Never print or commit secrets.

## Production
- Host alias: `prod-albery`
- Host: `217.198.12.236` (label `andigital`)
- User: `root`
- OS: Ubuntu
- Working dir: `/var/www/albery`
- Hermes home: `/root/.hermes`  (brain: `/root/.hermes/agent-knowledge`, secrets: `/root/.hermes/secure`)
- Connection: prefer `python _deploy_helper.py new "<command>"` (reads secrets locally via Paramiko).
  If already inside the server shell, run commands directly without `ssh root@...`.
- 2026-05-30: legacy `andidigital.service` is stopped and disabled to free RAM for Hermes. Nginx still keeps the `andigital.ru` certificate and `/andigital/secret/` Vault proxy to `127.0.0.1:8787`; normal site root returns `503`.

## Layout on server
```
/var/www/albery/             project
/var/www/albery/.env         production env (NOT in git)
/var/www/albery/.venv/       Python venv
/var/www/albery/run_5002.py  Flask on 127.0.0.1:5002
/etc/systemd/system/albery.service
/etc/nginx/sites-available/albery
/var/backups/albery/postgres/
```

## Connectivity check (no secrets printed)
```bash
python _deploy_helper.py new "systemctl is-active albery; git -C /var/www/albery rev-parse --short HEAD"
```

## Forbidden
- Не печатать `Host_Password`/токены; не передавать в аргументах.
- Не коммитить `.env*`. Секреты только в локальном/серверном env.
