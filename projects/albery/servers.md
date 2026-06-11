---
id: albery-servers
type: project
project: albery
tags: [servers, access]
updated: 2026-06-11
secret_refs: [proj/albery/ssh/root]
---

# Albery — servers & access

> Credentials by NAME only. Real values: local `.env.local` (`Host_IP`, `Host_User`,
> `Host_Password`) and server `.env`. Never print or commit secrets.

## Production — CORRECTED 2026-06-11 (host was wrong in the brain)
- Host alias: `prod-albery`
- **Host: `186.246.7.32`** (Timeweb cloud, hostname `7996094-hl701847.twc1.net`, 2 GB RAM, Ubuntu).
  `m4s.ru` / `www.m4s.ru` / `mcp.m4s.ru` all resolve here (verified by DNS 2026-06-11).
  ⚠ The earlier value `217.198.12.236 (andigital)` was WRONG — **217 is a DIFFERENT server**
  (the general-purpose Hermes Brain + andidigital site + Vault + MeshCentral). Albery and its
  dedicated Hermes live on **186**, not 217.
- User: `root`
- Working dir: `/var/www/albery`  (`albery.service` → `.venv/bin/python run_5002.py`, Flask on `127.0.0.1:5002`)
- Hermes home: `/root/.hermes`  (dedicated Albery Hermes, `hermes-gateway.service`, v0.14.0)
- **Access**: stored in the secure vault on 217 at `/opt/hermes/secure/projects/albery/.env`
  (`IP=186.246.7.32`, `USER`, `PASSWORD`). To run on 186 from 217: read those creds and
  `sshpass -f <pwfile> ssh root@186.246.7.32` (password never in argv/ps).

## Dedicated Albery Hermes agent (on 186.246.7.32)
- A separate Hermes agent runs on the Albery server (186), distinct from the general Hermes Brain (217).
- Scope: Albery-only work (zoom→tasks, owner-daily/weekly reports, Albery MCP). Do not mix its
  state/profile with Hermes Brain unless explicitly requested.
- Brain = ChatGPT `gpt-5.5` via `openai-codex`, **single account** `albery-dedicated-codex` +
  a Gemini API key present (unused as fallback — see incidents). No account failover → a codex
  `token_invalidated` 401 crashes the gateway (22 crashes 2026-06-08/09 before the account was re-added).

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
