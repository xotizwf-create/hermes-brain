---
id: albery-server-context
type: project
project: albery
tags: [albery, server, hermes, vpn, nginx, systemd, postgres, reference]
updated: 2026-05-29
secret_refs: []
---

> Imported from the legacy `agent.md` (site repo). Complete operational reference for the
> albery prod server, VPN gateway (AmneziaWG), Hermes agent, Codex, and MCP tools.
> The curated docs (overview/servers/deploy/runbook) are the summary; pull sections out of
> here into clean focused docs over time. Note: older sections reference the historical server
> `186.246.7.32`; current prod is `217.198.12.236`.
# Albery Server Context

## Current Operating Rules / РђРєС‚СѓР°Р»СЊРЅС‹Р№ РљРѕРЅС‚РµРєСЃС‚

This file is the first place to read in every new chat. It contains the current server context, deployment commands, webhook endpoints, cron schedule, and operational rules.

Server access (current project):

- Active server: `root@217.198.12.236` (`andigital`).
- Server project: `/var/www/albery`
- Hermes home: `/root/.hermes`
- Local project: `G:\OneDrive\Р Р°Р±РѕС‡РёР№ СЃС‚РѕР»\РњРѕРё РїСЂРѕРµРєС‚С‹\РЎР°Р№С‚ РјРѕР№`
- SSH credentials are stored only in local `.env.local` as `Host_IP`, `Host_User`, `Host_Password`.
- Do not print, quote, commit, or pass passwords/tokens through command-line arguments.
- For automated server work from Codex, prefer Python/Paramiko or `python _deploy_helper.py new "<command>"`; it reads secrets locally and connects to `217.198.12.236`.
- If already inside the server shell, run commands directly without `ssh root@...`.
- Never commit `.env*`; secrets stay only in local/server env files.
- Older sections may mention historical server `186.246.7.32`; for this current project/Hermes setup use `217.198.12.236` unless explicitly asked otherwise.

## Agent Knowledge And Skills Store

This project uses an external knowledge base instead of long-term agent memory for engineering rules, reusable workflows, and access instructions.

Current locations:

- Local knowledge base: `agent-knowledge/INDEX.md`.
- Local instructions: `agent-knowledge/instructions/`.
- Local reusable skills: `agent-knowledge/skills/`.
- Local templates: `agent-knowledge/templates/`.
- Server knowledge base: `/root/.hermes/agent-knowledge/INDEX.md`.
- Server secure store: `/root/.hermes/secure/`.

Installed instruction files:

- `agent-knowledge/instructions/secrets-access.md`: safe credential usage, GitHub/SSH/API token handling, rotation rules, and secret redaction.
- `agent-knowledge/instructions/database.md`: schema design, migrations, backups, and production database safety.
- `agent-knowledge/instructions/server-deploy.md`: server setup, deploy flow, systemd, nginx, logs, and production checks.
- `agent-knowledge/instructions/optimization.md`: performance workflow for database/backend/frontend/infrastructure.
- `agent-knowledge/instructions/security.md`: auth, webhooks, dependency risk, server hardening, and sensitive data rules.
- `agent-knowledge/instructions/testing.md`: test strategy, regression tests, fixtures, CI, and verification reporting.

Installed skills:

- `agent-knowledge/skills/secure-access/SKILL.md`: use for credentials, SSH keys, GitHub access, API tokens, service logins, database URLs, webhook secrets, and production access.
- `agent-knowledge/skills/postgres-production/SKILL.md`: use for PostgreSQL install, hardening, backups, restores, migrations, operations, and slow-query work.

Installed templates:

- `agent-knowledge/templates/access-map.template.yaml`: template for non-secret project/service/credential routing metadata.
- `agent-knowledge/templates/secrets.template.yaml`: template for root-only secret values or paths to secret files.

How the agent must use this store:

1. Start from `agent-knowledge/INDEX.md` or `/root/.hermes/agent-knowledge/INDEX.md`.
2. Load only the instruction or skill files relevant to the current task.
3. Before database, deploy, optimization, security, testing, or credential-heavy work, read the matching file from `agent-knowledge/instructions/`.
4. Use `secure-access` before touching credentials or protected services.
5. Use `postgres-production` before production PostgreSQL setup, backup, restore, or migration work.
6. Keep detailed instructions outside memory; use memory only for tiny routing pointers.

Secrets policy:

- Do not store real passwords, tokens, private keys, cookies, recovery codes, or database URLs in `agent-knowledge`, `agent.md`, git, chat, logs, command arguments, screenshots, PRs, or issues.
- Real server-side secrets belong only in `/root/.hermes/secure/` with owner `root:root`.
- `/root/.hermes/secure` must be mode `700`.
- `/root/.hermes/secure/access-map.yaml` must be mode `600`; it stores non-secret routing metadata, project names, repository URLs, credential names, scopes, and allowed actions.
- `/root/.hermes/secure/secrets.yaml` must be mode `600`; it stores secret values or `value_path` references when the agent needs real credentials.
- Local secret scratch space is `agent-secrets/`, `.env.local`, or an external password manager only; these paths must never be committed.
- `.gitignore` includes `agent-secrets/`, `*.secret.*`, `*.secrets.*`, and `*.vault.*`.

Hermes server integration:

- `/root/.hermes/agent-knowledge/` is installed on `217.198.12.236`.
- `/root/.hermes/secure/access-map.yaml` and `/root/.hermes/secure/secrets.yaml` were created on `217.198.12.236` with root-only permissions.
- Hermes `agent.system_prompt` contains only a short pointer to `/root/.hermes/agent-knowledge/INDEX.md` and `/root/.hermes/secure/`; detailed standards stay in external files.
- After changing local `agent-knowledge/`, sync it to the server before expecting Hermes to use the new instructions.

Safe sync pattern:

```powershell
tar -cf tmp_agent_knowledge.tar agent-knowledge
python _deploy_helper.py new --put tmp_agent_knowledge.tar /tmp/agent-knowledge.tar
python _deploy_helper.py new "tar -xf /tmp/agent-knowledge.tar -C /root/.hermes && rm -f /tmp/agent-knowledge.tar"
Remove-Item -LiteralPath tmp_agent_knowledge.tar
```

Validation:

```powershell
python C:/Users/hotiz/.codex/skills/.system/skill-creator/scripts/quick_validate.py agent-knowledge/skills/secure-access
python C:/Users/hotiz/.codex/skills/.system/skill-creator/scripts/quick_validate.py agent-knowledge/skills/postgres-production
python _deploy_helper.py new "stat -c '%a %U:%G %n' /root/.hermes/secure /root/.hermes/secure/access-map.yaml /root/.hermes/secure/secrets.yaml"
```

Recent production changes:

- Bitrix task comments are now exposed through the main MCP connector:
  - new tool `get_task_comments(bitrix_task_id, include_service?, order?, limit?, offset?)` reads `bitrix_tasks.raw_json -> 'comments' -> 'items'`, strips Bitrix BB-codes, resolves author names from `users`, and hides auto-generated notifications (overdue reminders, status cards, completion notices) unless `include_service=true`;
  - `search_tasks` rows now also return `comments_total_count` and `comments_human_count` so the agent knows which tasks have real discussion;
  - no DB migration; lives in `mcp/context_server.py` (MCP server version `0.3.0`); not exposed on the FAQ endpoint.
- Bitrix tasks now support near-realtime sync through outgoing Bitrix webhook:
  - endpoint: `https://mcp.m4s.ru/bitrix/events/tasks/<BITRIX_EVENT_SECRET>`
  - events: `OnTaskAdd`, `OnTaskUpdate`, `OnTaskDelete`
  - queue table: `bitrix_task_events`
  - migration: `database/migrations/018_bitrix_task_events.sql`
  - unsupported Bitrix task comment events are accepted with `200 OK` and ignored.
- Zoom recordings now use incremental sync:
  - existing Zoom calls are skipped if the set of transcript files has not changed;
  - old transcript segments are not deleted/recreated for unchanged recordings;
  - manual/API/cron sync downloads only new or changed transcript files.
- Zoom webhook support was added:
  - endpoint: `https://mcp.m4s.ru/zoom/events/<ZOOM_EVENT_SECRET>`
  - events: `recording.transcript_completed`, `recording.completed`
  - validation event: `endpoint.url_validation`
  - queue table: `zoom_recording_events`
  - migration: `database/migrations/019_zoom_recording_events.sql`
  - `ZOOM_WEBHOOK_SECRET_TOKEN` must be copied from Zoom Marketplace Event Subscriptions Secret Token.
- Big external sync cron is daily at `18:00 Europe/Moscow`, not hourly:
  - file: `/etc/cron.d/albery-daily-sync`
  - logs: `/var/log/albery/daily-sync.log`, `/var/log/albery/daily-sync.cron.log`
- Latest relevant commits:
  - `90833c5 Expose Bitrix task comments via MCP`
  - `096c85f Add Bitrix task event sync`
  - `1f8c45d Add incremental Zoom recording sync`

Important env keys:

```env
BITRIX_EVENT_SECRET=...
BITRIX_TASK_EVENT_PROCESS_INLINE=1
ZOOM_EVENT_SECRET=...
ZOOM_WEBHOOK_SECRET_TOKEN=...
ZOOM_EVENT_PROCESS_INLINE=1
```

Operational checks:

```bash
cd /var/www/albery
git status --short
git rev-parse --short HEAD
systemctl status albery --no-pager
tail -n 120 /var/log/albery/daily-sync.log
tail -n 120 /var/log/albery/daily-sync.cron.log
```

Apply migrations/restart after deploy:

```bash
cd /var/www/albery && .venv/bin/python scripts/ensure_postgres.py && systemctl restart albery
```

Check webhook endpoints without printing secrets:

```bash
cd /var/www/albery
bitrix_secret=$(awk -F= '$1=="BITRIX_EVENT_SECRET"{print $2; exit}' .env)
zoom_secret=$(awk -F= '$1=="ZOOM_EVENT_SECRET"{print $2; exit}' .env)
curl -sS "https://mcp.m4s.ru/bitrix/events/tasks/$bitrix_secret"
curl -sS "https://mcp.m4s.ru/zoom/events/$zoom_secret"
```

Current GitHub branch: `main`. Push code changes to GitHub before or after server deployment so that future `./scripts/update_server.sh` does not overwrite manual server edits.

Р­С‚РѕС‚ С„Р°Р№Р» С„РёРєСЃРёСЂСѓРµС‚ СЂР°Р±РѕС‡РёР№ РєРѕРЅС‚РµРєСЃС‚ РїСЂРѕРµРєС‚Р°, С‡С‚РѕР±С‹ РІ РЅРѕРІРѕРј С‡Р°С‚Рµ СЃСЂР°Р·Сѓ Р±С‹Р»Рѕ РїРѕРЅСЏС‚РЅРѕ, РіРґРµ С‡С‚Рѕ Р»РµР¶РёС‚ Рё РєР°РєРёРјРё РєРѕРјР°РЅРґР°РјРё РѕР±СЃР»СѓР¶РёРІР°С‚СЊ СЃРµСЂРІРµСЂ.

## Git Branch Workflow / РџСЂР°РІРёР»Р° Р Р°Р±РѕС‚С‹ РЎ Р’РµС‚РєР°РјРё

`main` is the stable working branch. Do not make risky or experimental changes directly in `main`.

Default workflow:

```powershell
git checkout main
git pull origin main
git checkout -b feature/my-change
```

Work in a separate branch for every task:

- `feature/...` for new features;
- `bugfix/...` for fixes;
- `codex/...` for Cloud Codex work;
- one branch should contain one logical task.

Before committing:

```powershell
git status
git diff
```

Commit and push the branch:

```powershell
git add .
git commit -m "Describe the change"
git push -u origin feature/my-change
```

Cloud Codex rule:

- Cloud Codex should create a separate branch from the latest `main`;
- Cloud Codex must not push directly to `main` unless explicitly asked;
- after finishing, Cloud Codex should push the branch and show a diff summary;
- merge into `main` only after review/confirmation.

Recommended Cloud Codex prompt:

```text
Work in a new branch feature/my-change from the latest main.
Do not push directly to main.
After changes, show a diff summary and wait for confirmation before merge.
```

To inspect a remote branch created by Cloud Codex:

```powershell
git fetch origin
git branch --track codex/some-branch origin/codex/some-branch
git diff --stat main..origin/codex/some-branch
git diff main..origin/codex/some-branch
```

To merge a checked branch into `main` locally:

```powershell
git checkout main
git pull origin main
git merge feature/my-change
git push origin main
```

If Git reports conflicts, resolve the marked files manually, then:

```powershell
git add <resolved-files>
git commit
git push origin main
```

After a branch has been merged and is no longer needed:

```powershell
git branch -d feature/my-change
git push origin --delete feature/my-change
```

Local PC auto-update rule:

- the watcher script `scripts/watch_github_updates.ps1` checks `origin/main` and fast-forwards only `main`;
- it does not automatically merge feature/codex branches into `main`;
- if a new remote branch appears, inspect it first, then merge intentionally.

## Р РµРїРѕР·РёС‚РѕСЂРёР№

- GitHub: `https://github.com/xotizwf-create/Albery.git`
- РћСЃРЅРѕРІРЅР°СЏ РІРµС‚РєР°: `main`
- Р›РѕРєР°Р»СЊРЅС‹Р№ РїСЂРѕРµРєС‚ Windows: `G:\OneDrive\Р Р°Р±РѕС‡РёР№ СЃС‚РѕР»\РњРѕРё РїСЂРѕРµРєС‚С‹\Р•РІРіРµРЅРёР№. Р Р°Р·СЂР°Р±РѕС‚РєР°`
- РЎРµСЂРІРµСЂРЅС‹Р№ РїСЂРѕРµРєС‚: `/var/www/albery`

## РЎРµСЂРІРµСЂ

- IP: `186.246.7.32`
- РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ: `root`
- РћРЎ: Ubuntu 22.04
- РћСЃРЅРѕРІРЅРѕР№ РґРѕРјРµРЅ: `m4s.ru`
- РљР°РЅРѕРЅРёС‡РµСЃРєРёР№ web-РґРѕРјРµРЅ: `www.m4s.ru`
- MCP-РґРѕРјРµРЅ: `mcp.m4s.ru`

DNS-Р·Р°РїРёСЃРё:

```text
A  @    186.246.7.32
A  www  186.246.7.32
A  mcp  186.246.7.32
```

РџСЂРѕРІРµСЂРєР° DNS:

```bash
dig +short m4s.ru
dig +short www.m4s.ru
dig +short mcp.m4s.ru
```

## РЎС‚СЂСѓРєС‚СѓСЂР° РќР° РЎРµСЂРІРµСЂРµ

```text
/var/www/albery/                  РїСЂРѕРµРєС‚
/var/www/albery/.env              production env, РЅРµ С…СЂР°РЅРёС‚СЃСЏ РІ git
/var/www/albery/.venv/            Python venv
/var/www/albery/run_5002.py       Р·Р°РїСѓСЃРє Flask РЅР° 127.0.0.1:5002
/var/www/albery/РРЅС‚РµСЂС„РµР№СЃ/        React/Vite frontend
/var/www/albery/РРЅС‚РµСЂС„РµР№СЃ/dist/   СЃРѕР±СЂР°РЅРЅС‹Р№ frontend
/var/www/albery/scripts/          СЃР»СѓР¶РµР±РЅС‹Рµ СЃРєСЂРёРїС‚С‹
/var/backups/albery/postgres/     Р±СЌРєР°РїС‹ PostgreSQL
/etc/systemd/system/albery.service systemd service
/etc/nginx/sites-available/albery Nginx site config
/etc/cron.d/albery-postgres-backup cron Р°РІС‚РѕР±СЌРєР°РїР° Р‘Р”
```

## Р—Р°РїСѓСЃРє РџСЂРёР»РѕР¶РµРЅРёСЏ

Backend СЃР»СѓС€Р°РµС‚ С‚РѕР»СЊРєРѕ Р»РѕРєР°Р»СЊРЅРѕ:

```text
127.0.0.1:5002
```

РџСѓР±Р»РёС‡РЅС‹Р№ РґРѕСЃС‚СѓРї РёРґРµС‚ С‡РµСЂРµР· Nginx reverse proxy:

```text
https://www.m4s.ru -> http://127.0.0.1:5002
https://mcp.m4s.ru -> http://127.0.0.1:5002
```

Р“Р»Р°РІРЅР°СЏ СЃС‚СЂР°РЅРёС†Р° РїСЂРёР»РѕР¶РµРЅРёСЏ:

```text
https://www.m4s.ru/main
```

MCP endpoint:

```text
https://mcp.m4s.ru/mcp/<MCP_SHARED_SECRET>
```

FAQ MCP endpoint for external assistants with limited rights:

```text
https://mcp.m4s.ru/mcp-faq/<MCP_FAQ_SHARED_SECRET>
```

The FAQ endpoint exposes only company knowledge/regulations, Zoom calls/transcripts (including stored Zoom call reports via `get_zoom_call_transcript`), org structure, AI instructions, source list, context guide, and health check tools. It does not expose Bitrix tasks, chats, report generation, report saving/deleting, OCR processing, compact exports, or instruction editing tools.

## Systemd

РЎРµСЂРІРёСЃ:

```bash
systemctl status albery --no-pager
systemctl restart albery
journalctl -u albery -n 120 --no-pager
```

РЎРѕРґРµСЂР¶РёРјРѕРµ `/etc/systemd/system/albery.service`:

```ini
[Unit]
Description=Albery Flask App
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/var/www/albery
EnvironmentFile=/var/www/albery/.env
ExecStart=/var/www/albery/.venv/bin/python /var/www/albery/run_5002.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

РџРѕСЃР»Рµ РёР·РјРµРЅРµРЅРёСЏ:

```bash
systemctl daemon-reload
systemctl enable --now albery
systemctl restart albery
```

## Nginx

РџСЂРѕРІРµСЂРєР°:

```bash
nginx -t
systemctl reload nginx
tail -n 120 /var/log/nginx/error.log
```

Р’Р°Р¶РЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё:

- HTTP Рё IP РґРѕР»Р¶РЅС‹ СЂРµРґРёСЂРµРєС‚РёС‚СЊ РЅР° `https://www.m4s.ru`
- `m4s.ru` РґРѕР»Р¶РµРЅ СЂРµРґРёСЂРµРєС‚РёС‚СЊ РЅР° `www.m4s.ru`
- `mcp.m4s.ru` РѕСЃС‚Р°РµС‚СЃСЏ РѕС‚РґРµР»СЊРЅС‹Рј С…РѕСЃС‚РѕРј РґР»СЏ MCP
- Р”Р»СЏ РґРѕР»РіРёС… Google Drive sync РЅСѓР¶РЅС‹ proxy timeout `600s`

Р РµРєРѕРјРµРЅРґСѓРµРјС‹Р№ `/etc/nginx/sites-available/albery`:

```nginx
server {
    listen 80 default_server;
    server_name _;
    return 301 https://www.m4s.ru$request_uri;
}

server {
    listen 80;
    server_name m4s.ru www.m4s.ru mcp.m4s.ru;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name m4s.ru;

    ssl_certificate /etc/letsencrypt/live/m4s.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/m4s.ru/privkey.pem;

    return 301 https://www.m4s.ru$request_uri;
}

server {
    listen 443 ssl default_server;
    server_name _;

    ssl_certificate /etc/letsencrypt/live/m4s.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/m4s.ru/privkey.pem;

    return 301 https://www.m4s.ru$request_uri;
}

server {
    listen 443 ssl;
    server_name www.m4s.ru;

    ssl_certificate /etc/letsencrypt/live/m4s.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/m4s.ru/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
    }
}

server {
    listen 443 ssl;
    server_name mcp.m4s.ru;

    ssl_certificate /etc/letsencrypt/live/m4s.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/m4s.ru/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
    }
}
```

РџСЂРёРјРµРЅРµРЅРёРµ:

```bash
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/albery /etc/nginx/sites-enabled/albery
nginx -t && systemctl reload nginx
```

## HTTPS

РЎРµСЂС‚РёС„РёРєР°С‚ Let's Encrypt РІС‹РїСѓС‰РµРЅ РЅР°:

```text
m4s.ru
www.m4s.ru
mcp.m4s.ru
```

РљРѕРјР°РЅРґС‹:

```bash
certbot certificates
certbot renew --dry-run
```

Р•СЃР»Рё РЅСѓР¶РЅРѕ РїРµСЂРµРІС‹РїСѓСЃС‚РёС‚СЊ:

```bash
certbot --nginx -d m4s.ru -d www.m4s.ru -d mcp.m4s.ru
```

## PostgreSQL

- Р‘Р”: `albery`
- РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ Р‘Р”: `albery_app`
- РџР°СЂРѕР»СЊ С…СЂР°РЅРёС‚СЃСЏ С‚РѕР»СЊРєРѕ РІ `/var/www/albery/.env`

РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ:

```bash
cd /var/www/albery
source .venv/bin/activate
python - <<'PY'
from dotenv import load_dotenv
load_dotenv("/var/www/albery/.env")
import app
with app.pg_connect() as conn:
    with conn.cursor() as cur:
        cur.execute("select current_database(), current_user")
        print(cur.fetchone())
PY
```

РџСЂРёРјРµРЅРёС‚СЊ СЃС…РµРјСѓ/РјРёРіСЂР°С†РёРё:

```bash
cd /var/www/albery
.venv/bin/python scripts/ensure_postgres.py
```

## Env

РћС‚РєСЂС‹С‚СЊ production env:

```bash
nano /var/www/albery/.env
```

Р’Р°Р¶РЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ:

```env
DATABASE_URL=postgresql://...
DATABASE_ADMIN_URL=postgresql://...
FLASK_SECRET_KEY=...
ADMIN_PASSWORD_HASH=...
AUTH_SESSION_DAYS=30
AUTH_RATE_LIMIT_ATTEMPTS=6
AUTH_RATE_LIMIT_WINDOW_SECONDS=900
CANONICAL_WEB_HOST=www.m4s.ru
MCP_HOST=mcp.m4s.ru

BITRIX_WEBHOOK_BASE=...
BITRIX_EXPORT_MODE=audit
BITRIX_REQUEST_DELAY=0.05
BITRIX_LOOKBACK_DAYS=30
AUTO_SYNC_BITRIX_LOOKBACK_DAYS=30
AUTO_SYNC_CHAT_LOOKBACK_DAYS=1
AUTO_SYNC_CHAT_GENERATE_REPORTS=0
AUTO_SYNC_ZOOM_FROM=2026-01-01
AUTO_SYNC_ZOOM_TO=
AUTO_SYNC_GOOGLE_DRIVE_ZOOM_TRANSCRIPTS=1

MCP_SHARED_SECRET=...
MCP_ALLOW_UNAUTHENTICATED=0
MCP_FAQ_SHARED_SECRET=...

OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_MODE=responses
OPENAI_TIMEOUT_SECONDS=120

GOOGLE_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-2.0-flash

GOOGLE_APPS_SCRIPT_SYNC_URL=...
GOOGLE_APPS_SCRIPT_SYNC_TOKEN=...
GOOGLE_DRIVE_COMPANY_ROOT_NAME=Google Drive
GOOGLE_DRIVE_SYNC_TIMEOUT_SECONDS=600
GOOGLE_CALLS_APPS_SCRIPT_SYNC_URL=
GOOGLE_CALLS_APPS_SCRIPT_SYNC_TOKEN=...

ZOOM_ACC2_ACCOUNT_ID=...
ZOOM_ACC2_CLIENT_ID=...
ZOOM_ACC2_CLIENT_SECRET=...
ZOOM_OAUTH_URL=https://zoom.us/oauth/token
ZOOM_API_BASE_URL=https://api.zoom.us/v2
```

РќРµ РІСЃС‚Р°РІР»СЏС‚СЊ СЂРµР°Р»СЊРЅС‹Рµ СЃРµРєСЂРµС‚С‹ РІ git РёР»Рё С‡Р°С‚. `.env` РёСЃРєР»СЋС‡РµРЅ С‡РµСЂРµР· `.gitignore`.

РЎРіРµРЅРµСЂРёСЂРѕРІР°С‚СЊ hash РїР°СЂРѕР»СЏ Р°РґРјРёРЅРєРё:

```bash
cd /var/www/albery
source .venv/bin/activate
python - <<'PY'
from getpass import getpass
from werkzeug.security import generate_password_hash
password = getpass("Admin password: ")
print("ADMIN_PASSWORD_HASH=" + generate_password_hash(password))
PY
```

## РђРІС‚РѕРјР°С‚РёС‡РµСЃРєР°СЏ РџРѕС‡Р°СЃРѕРІР°СЏ РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ

РџРѕС‡Р°СЃРѕРІР°СЏ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЃС‚Р°РІРёС‚СЃСЏ РѕС‚РґРµР»СЊРЅС‹Рј cron-С„Р°Р№Р»РѕРј:

```text
/etc/cron.d/albery-daily-sync
```

Р’СЂРµРјСЏ Р·Р°РїСѓСЃРєР°:

```text
РєР°Р¶РґС‹Р№ С‡Р°СЃ РІ 00 РјРёРЅСѓС‚ РїРѕ Europe/Moscow
```

РЈСЃС‚Р°РЅРѕРІРёС‚СЊ РёР»Рё РѕР±РЅРѕРІРёС‚СЊ cron:

```bash
cd /var/www/albery && ./scripts/install_daily_sync_cron.sh
```

Р—Р°РїСѓСЃС‚РёС‚СЊ РІСЂСѓС‡РЅСѓСЋ:

```bash
cd /var/www/albery
ALBERY_LOG_DIR=/var/log/albery ALBERY_DAILY_SYNC_LOG=/var/log/albery/daily-sync.log .venv/bin/python scripts/run_daily_sync.py
```

Р§С‚Рѕ Р·Р°РїСѓСЃРєР°РµС‚ `scripts/run_daily_sync.py`:

- `bitrix_team` - СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ Bitrix
- `bitrix_tasks` - СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Bitrix-Р·Р°РґР°С‡ Р·Р° РїРµСЂРёРѕРґ
- `bitrix_chat_messages` - СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЃРїРёСЃРєР° С‡Р°С‚РѕРІ Рё СЃРѕРѕР±С‰РµРЅРёР№
- `zoom_api_calls` - СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ Zoom-СЃРѕР·РІРѕРЅРѕРІ С‡РµСЂРµР· Zoom API
- `google_drive_company_instructions` - РїРѕРґС‚СЏРіРёРІР°РЅРёРµ Google Drive РґРѕРєСѓРјРµРЅС‚РѕРІ/РёРЅСЃС‚СЂСѓРєС†РёР№ РІ СЂР°Р·РґРµР» "Рћ РєРѕРјРїР°РЅРёРё"
- `google_drive_zoom_transcripts` - РїРѕРґС‚СЏРіРёРІР°РЅРёРµ `transcript.txt` РёР· Google Drive РґР»СЏ Zoom, РµСЃР»Рё РІРєР»СЋС‡РµРЅРѕ

Р›РѕРіРё:

```text
/var/log/albery/daily-sync.log       СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅС‹Р№ JSONL-Р»РѕРі РєР°Р¶РґРѕРіРѕ С€Р°РіР°
/var/log/albery/daily-sync.cron.log  stdout/stderr cron-РѕР±РµСЂС‚РєРё
```

РЎРјРѕС‚СЂРµС‚СЊ Р»РѕРіРё:

```bash
tail -n 200 /var/log/albery/daily-sync.log
tail -n 200 /var/log/albery/daily-sync.cron.log
grep '"status": "failed"' /var/log/albery/daily-sync.log
```

РќР°СЃС‚СЂРѕР№РєРё РІ `.env`:

```env
AUTO_SYNC_BITRIX_LOOKBACK_DAYS=30
AUTO_SYNC_CHAT_LOOKBACK_DAYS=1
AUTO_SYNC_CHAT_GENERATE_REPORTS=0
AUTO_SYNC_ZOOM_FROM=2026-01-01
AUTO_SYNC_ZOOM_TO=
AUTO_SYNC_GOOGLE_DRIVE_ZOOM_TRANSCRIPTS=1
```

Р•СЃР»Рё РЅСѓР¶РЅРѕ, С‡С‚РѕР±С‹ РїСЂРё РІРµС‡РµСЂРЅРµР№ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё СЃСЂР°Р·Сѓ С„РѕСЂРјРёСЂРѕРІР°Р»РёСЃСЊ РґРЅРµРІРЅС‹Рµ РѕС‚С‡РµС‚С‹ РїРѕ С‡Р°С‚Р°Рј:

```env
AUTO_SYNC_CHAT_GENERATE_REPORTS=1
```

## Р”РµРїР»РѕР№ Р РћР±РЅРѕРІР»РµРЅРёРµ

РћСЃРЅРѕРІРЅР°СЏ РєРѕРјР°РЅРґР° РѕР±РЅРѕРІР»РµРЅРёСЏ СЃРµСЂРІРµСЂР°:

```bash
cd /var/www/albery && ./scripts/update_server.sh
```

## FAQ MCP

Use this URL for the limited FAQ MCP server:

```text
https://mcp.m4s.ru/mcp-faq/<MCP_FAQ_SHARED_SECRET>
```

Set the secret in `/var/www/albery/.env`:

```env
MCP_FAQ_SHARED_SECRET=...
```

Allowed tools: `start_here_always_read_ai_instructions`, `health`, `get_context_guide`, `get_ai_instructions`, `list_available_sources`, `get_company_profile`, `list_company_files`, `get_company_file`, `search_company_knowledge`, `get_org_structure`, `list_zoom_calls`, `get_zoom_call_transcript`, `search_zoom_transcripts`.

Scope: org structure, regulations/company knowledge, AI instructions, and Zoom calls (transcripts + stored Zoom call reports exposed via `get_zoom_call_transcript.analytical_note`).

Unavailable there: Bitrix tasks, chats/messages, OCR processing, chat/owner report reading/generation/saving/deleting, compact export, Bitrix refresh, AI instruction editing, and Zoom report saving/deleting.

Р§С‚Рѕ РґРµР»Р°РµС‚ `scripts/update_server.sh`:

- `git fetch` Рё `git pull --ff-only origin main`
- СЃРѕР·РґР°РµС‚ `.venv`, РµСЃР»Рё РµРіРѕ РЅРµС‚
- РѕР±РЅРѕРІР»СЏРµС‚ `pip`
- СЃС‚Р°РІРёС‚ `requirements.txt`
- РїСЂРёРјРµРЅСЏРµС‚ PostgreSQL migrations С‡РµСЂРµР· `scripts/ensure_postgres.py`
- РЅР°С…РѕРґРёС‚ frontend `package.json`
- РґРµР»Р°РµС‚ `npm ci`
- РґРµР»Р°РµС‚ `npm run build`
- РїРµСЂРµР·Р°РїСѓСЃРєР°РµС‚ `albery`
- Р¶РґРµС‚ РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё `http://127.0.0.1:5002`

Р•СЃР»Рё РїРѕСЃР»Рµ РґРµРїР»РѕСЏ РїСЂРѕР±Р»РµРјР°:

```bash
systemctl status albery --no-pager
journalctl -u albery -n 120 --no-pager
curl -I http://127.0.0.1:5002
```

## Google Apps Script (Google Drive company sync)

РљРѕРґ Apps Script, РєРѕС‚РѕСЂС‹Р№ РѕС‚РґР°С‘С‚ РґРѕРєСѓРјРµРЅС‚С‹ Рё РґРµСЂРµРІРѕ РїР°РїРѕРє РёР· Google Drive,
Р»РµР¶РёС‚ РІ СЂРµРїРѕР·РёС‚РѕСЂРёРё Рё РґРµРїР»РѕРёС‚СЃСЏ С‡РµСЂРµР· `clasp` (Р° РќР• С‡РµСЂРµР· `update_server.sh`).

- РџСЂРѕРµРєС‚: `scripts/google_drive_company_sync_project/` (`Code.gs`, `appsscript.json`)
- `.clasp.json` РІ РєРѕСЂРЅРµ: `scriptId = 1ga97W3bs386A00JokAHZyiQffEC1fFFjOoyzJm5GXUYkKjd3aXiRUoO9`
- Р›РѕРіРёРЅ clasp: РІР»Р°РґРµР»РµС† СЃРєСЂРёРїС‚Р° `xotizwf@gmail.com` (`clasp show-authorized-user`)
- РџСЂРѕРґ web app deployment (СЌС‚Рѕ Рё РµСЃС‚СЊ `/exec` РІ `GOOGLE_APPS_SCRIPT_SYNC_URL`):
  - deploymentId = `AKfycbwsEL8z_HAoNmLP9utV4HCtkNDAcgbaAxnWsZ1Njs7h4L6DcrmRzcehzxB1y070CarBgA`
  - `/exec` URL = `https://script.google.com/macros/s/<deploymentId>/exec`

РћР±РЅРѕРІР»РµРЅРёРµ РєРѕРґР° Apps Script (РѕР±РЅРѕРІР»СЏРµС‚ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ `/exec`, URL РЅРµ РјРµРЅСЏРµС‚СЃСЏ):

```bash
clasp push --force
clasp redeploy AKfycbwsEL8z_HAoNmLP9utV4HCtkNDAcgbaAxnWsZ1Njs7h4L6DcrmRzcehzxB1y070CarBgA -d "С‡С‚Рѕ РёР·РјРµРЅРёР»РѕСЃСЊ"
clasp deployments   # РїСЂРѕРІРµСЂРёС‚СЊ Р°РєС‚РёРІРЅСѓСЋ РІРµСЂСЃРёСЋ
```

Р’РђР–РќРћ вЂ” РїРѕС‡РµРјСѓ СЂР°РЅСЊС€Рµ `/exec` РѕС‚РґР°РІР°Р» 404 РїРѕСЃР»Рµ CLI-РґРµРїР»РѕСЏ:

- РСЃРїРѕР»СЊР·СѓР№С‚Рµ `clasp redeploy <deploymentId>` (РѕР±РЅРѕРІР»РµРЅРёРµ РЅР° РјРµСЃС‚Рµ), Р° РЅРµ
  `clasp deploy` (СЃРѕР·РґР°С‘С‚ РќРћР’Р«Р™ deployment СЃ РґСЂСѓРіРёРј URL).
- Р’ `appsscript.json` РѕР±СЏР·Р°РЅ Р±С‹С‚СЊ Р±Р»РѕРє `webapp`, РёРЅР°С‡Рµ clasp СЃРѕР·РґР°С‘С‚ РІРµСЂСЃРёСЋ
  Р±РµР· web app entry point Рё `/exec` РѕС‚РґР°С‘С‚ 404:

  ```json
  "webapp": { "executeAs": "USER_DEPLOYING", "access": "ANYONE_ANONYMOUS" }
  ```

РџСЂРѕРІРµСЂРєР°, С‡С‚Рѕ `/exec` Р¶РёРІРѕР№ (РґРѕР»Р¶РµРЅ РІРµСЂРЅСѓС‚СЊ JSON `{"ok": true, ...}`, РЅРµ HTML):

```bash
token=$(awk -F= '$1=="GOOGLE_APPS_SCRIPT_SYNC_TOKEN"{print $2; exit}' .env)
url=$(awk -F= '$1=="GOOGLE_APPS_SCRIPT_SYNC_URL"{sub(/^[^=]*=/,""); print; exit}' .env)
curl -sS -L "$url?token=$token" | head -c 200
```

Р›РѕРіРёРєР° СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёРё (РёРЅРєСЂРµРјРµРЅС‚Р°Р»СЊРЅРѕ, Р±РµР· РїРµСЂРµР·Р°РїРёСЃРё РЅРµРёР·РјРµРЅРЅС‹С… С„Р°Р№Р»РѕРІ):

- СЃРµСЂРІРµСЂ С€Р»С‘С‚ РІ Apps Script `known_files`/`known_folders` (id, РёРјСЏ, `updated_at`,
  `parent_folder_id`, `path`); СЃРєСЂРёРїС‚ РїРѕ РЅРёРј РїРѕРјРµС‡Р°РµС‚ РЅРµРёР·РјРµРЅРЅС‹Рµ С„Р°Р№Р»С‹
  `unchanged: true` Рё РќР• РІС‹РіСЂСѓР¶Р°РµС‚ РёС… РєРѕРЅС‚РµРЅС‚ (DOC/XLS РЅРµ РєРѕРЅРІРµСЂС‚РёСЂСѓСЋС‚СЃСЏ Р·Р°РЅРѕРІРѕ);
- СЃРµСЂРІРµСЂ РѕР±РЅРѕРІР»СЏРµС‚ `company_folders` С‚РѕР»СЊРєРѕ РїСЂРё СЂРµР°Р»СЊРЅРѕРј РёР·РјРµРЅРµРЅРёРё
  (СЃСЂР°РІРЅРµРЅРёРµ `content_hash`, РїСѓС‚Рё, СЂРѕРґРёС‚РµР»СЏ), РёРЅР°С‡Рµ С‚РѕР»СЊРєРѕ `last_seen_at`;
- СЃС‚СЂСѓРєС‚СѓСЂР° Google Drive Р·РµСЂРєР°Р»РёС‚СЃСЏ: РїР°РїРєРё -> `company_drive_folders` +
  `company_folders`, РґРѕРєСѓРјРµРЅС‚С‹ РєР»Р°РґСѓС‚СЃСЏ РІРЅСѓС‚СЂСЊ СЃРІРѕРёС… РїР°РїРѕРє;
- РІСЂРµРјРµРЅРЅС‹Р№ СЃР±РѕР№ РєРѕРЅРІРµСЂС‚Р°С†РёРё (`document_errors`, РЅР°РїСЂ. Drive rate limit) РќР•
  СѓРґР°Р»СЏРµС‚ СѓР¶Рµ СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРЅС‹Р№ РґРѕРєСѓРјРµРЅС‚ вЂ” РѕРЅ РїРѕРґС‚СЏРЅРµС‚СЃСЏ РЅР° СЃР»РµРґСѓСЋС‰РµРј РїСЂРѕРіРѕРЅРµ.

Р—Р°РїСѓСЃС‚РёС‚СЊ СЃРµСЂРІРµСЂРЅСѓСЋ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЋ РІСЂСѓС‡РЅСѓСЋ:

```bash
cd /var/www/albery
.venv/bin/python - <<'PY'
from dotenv import load_dotenv; load_dotenv("/var/www/albery/.env")
import app, json
print(json.dumps(app.sync_google_drive_company_documents(), ensure_ascii=False, default=str)[:600])
PY
```

РђРІС‚Рѕ-РѕР±РЅРѕРІР»РµРЅРёРµ РїРѕ С‚СЂРёРіРіРµСЂСѓ (near-realtime, ~1 РјРёРЅСѓС‚Р°):

- Р’ Apps Script СЃС‚РѕРёС‚ time-driven С‚СЂРёРіРіРµСЂ `checkDriveChangesAndNotify`
  (СЂР°Р· РІ РјРёРЅСѓС‚Сѓ). РћРЅ СЃС‡РёС‚Р°РµС‚ Р»С‘РіРєСѓСЋ СЃРёРіРЅР°С‚СѓСЂСѓ РґРµСЂРµРІР° РїР°РїРєРё (id, РІСЂРµРјСЏ РїСЂР°РІРєРё,
  РёРјРµРЅР°, СЂРѕРґРёС‚РµР»Рё; Р‘Р•Р— РєРѕРЅС‚РµРЅС‚Р°) Рё РїРёРЅРіСѓРµС‚ СЃРµСЂРІРµСЂ РўРћР›Р¬РљРћ РїСЂРё СЂРµР°Р»СЊРЅРѕРј РёР·РјРµРЅРµРЅРёРё.
- РЎРµСЂРІРµСЂ: РІРµР±С…СѓРє `POST /google-drive/events/<GOOGLE_DRIVE_EVENT_SECRET>` Р·Р°РїСѓСЃРєР°РµС‚
  С‚Сѓ Р¶Рµ РёРЅРєСЂРµРјРµРЅС‚Р°Р»СЊРЅСѓСЋ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЋ РїРѕРґ Postgres advisory-lock (РЅРµ РїРµСЂРµСЃРµРєР°РµС‚СЃСЏ
  СЃ РїРѕС‡Р°СЃРѕРІС‹Рј cron / СЂСѓС‡РЅРѕР№ РєРЅРѕРїРєРѕР№; РµСЃР»Рё Р·Р°РЅСЏС‚Рѕ вЂ” 409, С‚СЂРёРіРіРµСЂ РїРѕРІС‚РѕСЂРёС‚).
- РЎРµРєСЂРµС‚: `.env` `GOOGLE_DRIVE_EVENT_SECRET` == `CHANGE_NOTIFY_URL` РІ `Code.gs`.
- РўСЂРёРіРіРµСЂ СЃРѕР·РґР°С‘С‚СЃСЏ РћР”РРќ СЂР°Р· РІСЂСѓС‡РЅСѓСЋ: РѕС‚РєСЂС‹С‚СЊ СЂРµРґР°РєС‚РѕСЂ СЃРєСЂРёРїС‚Р°, РІС‹Р±СЂР°С‚СЊ С„СѓРЅРєС†РёСЋ
  `setupDriveChangeTrigger`, РЅР°Р¶Р°С‚СЊ Run, РїСЂРѕР№С‚Рё Р°РІС‚РѕСЂРёР·Р°С†РёСЋ (РЅСѓР¶РЅС‹ scope
  `script.scriptapp` Рё `drive`). РџРѕРІС‚РѕСЂРЅС‹Р№ Р·Р°РїСѓСЃРє Р±РµР·РѕРїР°СЃРµРЅ (СЃС‚Р°СЂС‹Рµ С‚СЂРёРіРіРµСЂС‹
  СѓРґР°Р»СЏСЋС‚СЃСЏ). РЎРЅСЏС‚СЊ С‚СЂРёРіРіРµСЂ: Р·Р°РїСѓСЃС‚РёС‚СЊ `removeDriveChangeTriggers`.
- РџСЂРѕРІРµСЂРєР° РІРµР±С…СѓРєР°: `curl https://mcp.m4s.ru/google-drive/events/<secret>` -> JSON
  `{"ok": true, ...}`; `POST` С‚СѓРґР° Р¶Рµ Р·Р°РїСѓСЃРєР°РµС‚ СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЋ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ result.
- РўСЂРёРіРіРµСЂС‹ РІ Apps Script: https://script.google.com/home/triggers

## Frontend

РџР°РїРєР°:

```bash
/var/www/albery/РРЅС‚РµСЂС„РµР№СЃ
```

РљРѕРјР°РЅРґС‹:

```bash
cd /var/www/albery/РРЅС‚РµСЂС„РµР№СЃ
npm ci
npm run build
```

Node.js РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ СЃРѕРІСЂРµРјРµРЅРЅС‹Р№. РќР° СЃРµСЂРІРµСЂРµ СЃС‚Р°РІРёР»СЃСЏ Node 20 С‡РµСЂРµР· NodeSource, РїРѕС‚РѕРјСѓ С‡С‚Рѕ Ubuntu apt РґР°РІР°Р» Node 12, Р° Vite С‚СЂРµР±СѓРµС‚ Node >=18.

## Р‘СЌРєР°РїС‹ Р‘Р”

РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРёР№ РµР¶РµРґРЅРµРІРЅС‹Р№ Р±СЌРєР°Рї СѓСЃС‚Р°РЅРѕРІР»РµРЅ:

```text
/etc/cron.d/albery-postgres-backup
```

РЎРєСЂРёРїС‚С‹:

```text
scripts/backup_postgres.sh
scripts/restore_postgres.sh
scripts/install_backup_cron.sh
```

РџР°РїРєР° Р±СЌРєР°РїРѕРІ:

```bash
/var/backups/albery/postgres/
```

Р СѓС‡РЅРѕР№ Р±СЌРєР°Рї:

```bash
cd /var/www/albery && ./scripts/backup_postgres.sh
```

РЈСЃС‚Р°РЅРѕРІРёС‚СЊ/РѕР±РЅРѕРІРёС‚СЊ cron:

```bash
cd /var/www/albery && ./scripts/install_backup_cron.sh
```

Р’РѕСЃСЃС‚Р°РЅРѕРІРёС‚СЊ custom dump:

```bash
cd /var/www/albery
./scripts/restore_postgres.sh /var/backups/albery/postgres/file.dump
systemctl restart albery
```

Р’РѕСЃСЃС‚Р°РЅРѕРІРёС‚СЊ plain SQL:

```bash
cd /var/www/albery
./scripts/backup_postgres.sh
DATABASE_URL=$(awk -F= '$1=="DATABASE_URL"{sub(/^[^=]*=/,""); print; exit}' .env)
psql "$DATABASE_URL" < /var/backups/albery/postgres/file.sql
.venv/bin/python scripts/ensure_postgres.py
systemctl restart albery
```

РЎРґРµР»Р°С‚СЊ Р»РѕРєР°Р»СЊРЅС‹Р№ SQL-Р±СЌРєР°Рї РЅР° Windows:

```powershell
cd "G:\OneDrive\Р Р°Р±РѕС‡РёР№ СЃС‚РѕР»\РњРѕРё РїСЂРѕРµРєС‚С‹\Р•РІРіРµРЅРёР№. Р Р°Р·СЂР°Р±РѕС‚РєР°"
$envLine = Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
$DATABASE_URL = $envLine -replace '^DATABASE_URL=', ''
& 'C:\Program Files\PostgreSQL\18\bin\pg_dump.exe' --format=plain --no-owner --no-acl --clean --if-exists --file .\backups\albery_local.sql $DATABASE_URL
```

Р—Р°РіСЂСѓР·РёС‚СЊ Р»РѕРєР°Р»СЊРЅС‹Р№ SQL РЅР° СЃРµСЂРІРµСЂ:

```powershell
scp .\backups\albery_local.sql root@186.246.7.32:/var/backups/albery/postgres/albery_local.sql
```

## РР·РІРµСЃС‚РЅС‹Рµ РСЃРїСЂР°РІР»РµРЅРёСЏ

- Flask РѕС‚РґР°РµС‚ frontend РёР· `РРЅС‚РµСЂС„РµР№СЃ/dist`.
- `/` СЂРµРґРёСЂРµРєС‚РёС‚ РЅР° `/main`.
- `/main` Р·Р°С‰РёС‰РµРЅ РїР°СЂРѕР»РµРј.
- РЎРµСЃСЃРёСЏ Р°РґРјРёРЅРєРё С…СЂР°РЅРёС‚СЃСЏ РІ signed cookie Flask.
- РџР°СЂРѕР»СЊ Р°РґРјРёРЅРєРё С…СЂР°РЅРёС‚СЃСЏ hash-СЃС‚СЂРѕРєРѕР№ `ADMIN_PASSWORD_HASH`.
- `CANONICAL_WEB_HOST=www.m4s.ru` СЂРµРґРёСЂРµРєС‚РёС‚ web-С‚СЂР°С„РёРє РЅР° `www`.
- MCP РѕСЃС‚Р°РµС‚СЃСЏ РґРѕСЃС‚СѓРїРµРЅ С‡РµСЂРµР· `mcp.m4s.ru` Рё `MCP_SHARED_SECRET`.
- Google Drive sync С‚СЂРµР±СѓРµС‚ СѓРІРµР»РёС‡РµРЅРЅС‹С… С‚Р°Р№РјР°СѓС‚РѕРІ: frontend/backend/Nginx РїРѕ 600 СЃРµРєСѓРЅРґ.
- PDF-РѕС‚С‡РµС‚С‹ Bitrix РЅР° Linux С‚СЂРµР±СѓСЋС‚ С€СЂРёС„С‚С‹:

```bash
apt install -y fonts-dejavu-core fonts-liberation
```

## Р§Р°СЃС‚С‹Рµ РљРѕРјР°РЅРґС‹

РћР±РЅРѕРІРёС‚СЊ РєРѕРґ Рё РїРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ:

```bash
cd /var/www/albery && ./scripts/update_server.sh
```

РћС‚РєСЂС‹С‚СЊ env:

```bash
nano /var/www/albery/.env
```

РџСЂРѕРІРµСЂРёС‚СЊ backend:

```bash
curl -I http://127.0.0.1:5002
```

РџСЂРѕРІРµСЂРёС‚СЊ РїСѓР±Р»РёС‡РЅС‹Рµ РґРѕРјРµРЅС‹:

```bash
curl -I https://www.m4s.ru
curl -I https://mcp.m4s.ru
```

РџСЂРѕРІРµСЂРёС‚СЊ Р»РѕРіРё:

```bash
journalctl -u albery -n 120 --no-pager
tail -n 120 /var/log/nginx/error.log
```

РџРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ СЃРµСЂРІРёСЃС‹:

```bash
systemctl restart albery
nginx -t && systemctl reload nginx
```

## VPN-С€Р»СЋР·: РІРµСЃСЊ РёСЃС…РѕРґСЏС‰РёР№ С‚СЂР°С„РёРє РїСЂРѕРґ-СЃРµСЂРІРµСЂР° С‡РµСЂРµР· Р­СЃС‚РѕРЅРёСЋ (AmneziaWG)

РќР°СЃС‚СЂРѕРµРЅРѕ 2026-05-27.

### Р—Р°С‡РµРј

РџСЂРѕРґ-СЃРµСЂРІРµСЂ `186.246.7.32` вЂ” СЂРѕСЃСЃРёР№СЃРєРёР№. РќРµРєРѕС‚РѕСЂС‹Рµ РёРЅРѕСЃС‚СЂР°РЅРЅС‹Рµ СЃРµСЂРІРёСЃС‹ СЂРµР¶СѓС‚
СЂРѕСЃСЃРёР№СЃРєРёРµ IP (РЅР°РїСЂРёРјРµСЂ, OpenAI/Codex РѕС‚РґР°СЋС‚ `HTTP 403`). Р§С‚РѕР±С‹ С‚Р°РєРёРµ СЃРµСЂРІРёСЃС‹
РѕС‚РєСЂС‹РІР°Р»РёСЃСЊ, **РІРµСЃСЊ РёСЃС…РѕРґСЏС‰РёР№ С‚СЂР°С„РёРє СЃРµСЂРІРµСЂР° Р·Р°РІРѕСЂР°С‡РёРІР°РµС‚СЃСЏ С‡РµСЂРµР· СЌСЃС‚РѕРЅСЃРєРёР№
AmneziaWG-VPN** Рё РІС‹С…РѕРґРёС‚ РІ РёРЅС‚РµСЂРЅРµС‚ СЃ СЌСЃС‚РѕРЅСЃРєРѕРіРѕ IP `95.85.243.43`.
РџСЂРё СЌС‚РѕРј **СЃР°Р№С‚ `m4s.ru`/`mcp.m4s.ru` Рё SSH РѕСЃС‚Р°СЋС‚СЃСЏ РЅР° РїСЂСЏРјРѕРј СЂРѕСЃСЃРёР№СЃРєРѕРј IP** вЂ”
РІС…РѕРґСЏС‰РёРµ РїРѕСЃРµС‚РёС‚РµР»Рё РЅРµ СЃС‚СЂР°РґР°СЋС‚.

РџСЂРѕРІРµСЂРєР° СЌС„С„РµРєС‚Р°: СЃ СЃРµСЂРІРµСЂР° `curl https://api.openai.com/v1/models` РѕС‚РґР°С‘С‚ `403`
РЅР°РїСЂСЏРјСѓСЋ Рё `401` (С‚.Рµ. РґРѕС€Р»Рё, РЅСѓР¶РµРЅ С‚РѕР»СЊРєРѕ РєР»СЋС‡) С‡РµСЂРµР· VPN. Gemini/googleapis
РґРѕСЃС‚СѓРїРµРЅ РёР· Р Р¤ Рё Р±РµР· VPN.

### РЎРµСЂРІРµСЂС‹ Рё РєР»СЋС‡Рё (.env)

```env
# Р­СЃС‚РѕРЅСЃРєРёР№ VPN-СЃРµСЂРІРµСЂ (С‚Р°Рј СЃС‚РѕРёС‚ Amnezia/AmneziaWG)
VPN_SERVER_HOST=IP: 95.85.243.43
VPN_SERVER_USER=root
VPN_SERVER_PASSWORD=...
# Р РѕСЃСЃРёР№СЃРєРёР№ РїСЂРѕРґ-СЃРµСЂРІРµСЂ
root_password=...
```

- Р­СЃС‚РѕРЅСЃРєРёР№ СЃРµСЂРІРµСЂ `95.85.243.43`: Amnezia РІ Docker. РџСЂРѕС„РёР»СЊ **1234** (UDP 1234,
  РєРѕРЅС‚РµР№РЅРµСЂ `amnezia-awg-1234`, РєР»РёРµРЅС‚ `10.8.2.2`) Р·Р°РєСЂРµРїР»С‘РЅ Р·Р° РїСЂРѕРґ-СЃРµСЂРІРµСЂРѕРј.
  РўР°Рј Р¶Рµ РµСЃС‚СЊ СЃС‚Р°СЂС‹Р№ РїСЂРѕС„РёР»СЊ РЅР° UDP 47138 СЃ Р»РёС‡РЅС‹РјРё СѓСЃС‚СЂРѕР№СЃС‚РІР°РјРё РІР»Р°РґРµР»СЊС†Р° вЂ”
  **РµРіРѕ РЅРµ С‚СЂРѕРіР°С‚СЊ**. РљР»РёРµРЅС‚СЃРєРёР№ РєРѕРЅС„РёРі РїСЂРѕС„РёР»СЏ 1234:
  `C:\Users\hotiz\Desktop\amnezia-estonia-1234.conf` вЂ” РќР• РёРјРїРѕСЂС‚РёСЂРѕРІР°С‚СЊ РЅР° РџРљ
  (Р°РґСЂРµСЃ `10.8.2.2` СѓР¶Рµ Р·Р°РЅСЏС‚ РїСЂРѕРґ-СЃРµСЂРІРµСЂРѕРј, Р±СѓРґРµС‚ РєРѕРЅС„Р»РёРєС‚).
- Р РѕСЃСЃРёР№СЃРєРёР№ РїСЂРѕРґ-СЃРµСЂРІРµСЂ `186.246.7.32`: РЅР° РЅС‘Рј СЃС‚РѕРёС‚ **РєР»РёРµРЅС‚ AmneziaWG** (`awg0`).

### РљР°Рє РїРѕРґРєР»СЋС‡Р°С‚СЊСЃСЏ Рє СЃРµСЂРІРµСЂР°Рј (Р±РµР· SSH-РєР»СЋС‡РµР№, РїР°СЂРѕР»СЊ РёР· .env)

Р’С…РѕРґ РїРѕ РїР°СЂРѕР»СЋ root С‡РµСЂРµР· Python/Paramiko (РєР°Рє Рё РґР»СЏ РІСЃРµРіРѕ РѕСЃС‚Р°Р»СЊРЅРѕРіРѕ РІ СЌС‚РѕРј РїСЂРѕРµРєС‚Рµ):

```python
import re, paramiko
env = {...}  # РїСЂРѕС‡РёС‚Р°С‚СЊ .env
host = re.search(r"\d+\.\d+\.\d+\.\d+", env["VPN_SERVER_HOST"]).group(0)  # 95.85.243.43
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(host, username="root", password=env["VPN_SERVER_PASSWORD"],
          look_for_keys=False, allow_agent=False)
# РґР»СЏ РїСЂРѕРґ-СЃРµСЂРІРµСЂР°: host="186.246.7.32", password=env["root_password"]
```

РџР°СЂРѕР»Рё Рё РїСЂРёРІР°С‚РЅС‹Рµ РєР»СЋС‡Рё РІ С‡Р°С‚/Р»РѕРіРё РЅРµ РІС‹РІРѕРґРёС‚СЊ.

### РљР°Рє СЌС‚Рѕ СЂР°Р±РѕС‚Р°РµС‚ (Р°СЂС…РёС‚РµРєС‚СѓСЂР°)

- РќР° РїСЂРѕРґ-СЃРµСЂРІРµСЂРµ РїРѕРґРЅСЏС‚ РёРЅС‚РµСЂС„РµР№СЃ `awg0` (AmneziaWG) СЃ `Table = off` вЂ” С‚СѓРЅРЅРµР»СЊ
  СЃР°Рј РїРѕ СЃРµР±Рµ РќР• РјРµРЅСЏРµС‚ РјР°СЂС€СЂСѓС‚С‹. РњР°СЂС€СЂСѓС‚РёР·Р°С†РёРµР№ СѓРїСЂР°РІР»СЏРµС‚ РѕС‚РґРµР»СЊРЅС‹Р№ СЃРєСЂРёРїС‚.
- **Policy-routing** (`/root/vpn_apply.sh`, Р·Р°РїСѓСЃРєР°РµС‚СЃСЏ РєР°Рє `PostUp` С‚СѓРЅРЅРµР»СЏ):
  - С‚Р°Р±Р»РёС†Р° `200`: РјР°СЂС€СЂСѓС‚ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ С‡РµСЂРµР· `awg0` (в†’ Р­СЃС‚РѕРЅРёСЏ);
  - `ip rule` РґР»СЏ `sport 22/443/80 в†’ main` Рё РїРѕРјРµС‚РєР° connmark РІС…РѕРґСЏС‰РёС… РЅР° `eth0`
    СЃРѕРµРґРёРЅРµРЅРёР№ (`fwmark 0x1 в†’ main`) вЂ” РѕС‚РІРµС‚С‹ СЃРµСЂРІРµСЂР° РєР°Рє СЃР°Р№С‚Р°/SSH СѓС…РѕРґСЏС‚ РїСЂСЏРјРѕ
    С‡РµСЂРµР· `eth0` РЅР° СЂРѕСЃСЃРёР№СЃРєРёР№ IP;
  - РІСЃС‘ РѕСЃС‚Р°Р»СЊРЅРѕРµ (РёСЃС…РѕРґСЏС‰РµРµ, РёРЅРёС†РёРёСЂРѕРІР°РЅРЅРѕРµ СЃРµСЂРІРµСЂРѕРј) в†’ С‚Р°Р±Р»РёС†Р° `200` в†’ С‚СѓРЅРЅРµР»СЊ;
  - endpoint VPN, Р»РѕРєР°Р»СЊРЅР°СЏ РїРѕРґСЃРµС‚СЊ Рё DNS-Р°РїСЃС‚СЂРёРјС‹ (85.193.93.193/194) РїСЂРёР±РёС‚С‹
    РїСЂСЏРјС‹Рј РјР°СЂС€СЂСѓС‚РѕРј С‡РµСЂРµР· `eth0`, С‡С‚РѕР±С‹ РЅРµ Р·Р°С†РёРєР»РёРІР°С‚СЊ С‚СѓРЅРЅРµР»СЊ Рё РЅРµ Р»РѕРјР°С‚СЊ DNS;
  - С‚СѓРЅРЅРµР»СЊ С‚РѕР»СЊРєРѕ IPv4, РїРѕСЌС‚РѕРјСѓ РёСЃС…РѕРґСЏС‰РёР№ IPv6 РІ РёРЅС‚РµСЂРЅРµС‚ **Р·Р°Р±Р»РѕРєРёСЂРѕРІР°РЅ**
    (`ip6tables` REJECT РґР»СЏ NEW РЅР° `2000::/3`, РІС…РѕРґСЏС‰РёР№ РЅР° СЃР°Р№С‚ РїРѕ IPv6 СЃРѕС…СЂР°РЅС‘РЅ),
    РїР»СЋСЃ `/etc/gai.conf` РїСЂРµРґРїРѕС‡РёС‚Р°РµС‚ IPv4. Р‘РµР· СЌС‚РѕРіРѕ РїСЂРёР»РѕР¶РµРЅРёСЏ (РЅР°РїСЂРёРјРµСЂ Codex)
    СѓС…РѕРґСЏС‚ РїРѕ СЂРѕСЃСЃРёР№СЃРєРѕРјСѓ IPv6 РІ РѕР±С…РѕРґ VPN Рё РїРѕР»СѓС‡Р°СЋС‚ Р±Р»РѕРє.
- `PreDown` (`/root/vpn_rollback.sh`) СЃРЅРёРјР°РµС‚ РІСЃСЋ СЌС‚Сѓ РјР°СЂС€СЂСѓС‚РёР·Р°С†РёСЋ РїСЂРё РѕСЃС‚Р°РЅРѕРІРєРµ
  С‚СѓРЅРЅРµР»СЏ, РІРѕР·РІСЂР°С‰Р°СЏ СЃРµСЂРІРµСЂ РЅР° РїСЂСЏРјРѕР№ РјР°СЂС€СЂСѓС‚ (СЃР°Р№С‚ РїСЂРё СЌС‚РѕРј РїСЂРѕРґРѕР»Р¶Р°РµС‚ СЂР°Р±РѕС‚Р°С‚СЊ).

### Р¤Р°Р№Р»С‹ РЅР° РїСЂРѕРґ-СЃРµСЂРІРµСЂРµ

```text
/etc/amnezia/amneziawg/awg0.conf                 РєРѕРЅС„РёРі С‚СѓРЅРЅРµР»СЏ (Table=off, PostUp/PreDown, MTU=1280)
/root/vpn_apply.sh                               РІРєР»СЋС‡Р°РµС‚ policy-routing (endpoint РѕРїСЂРµРґРµР»СЏРµС‚СЃСЏ СЃР°Рј)
/root/vpn_rollback.sh                            СЃРЅРёРјР°РµС‚ policy-routing
/root/vpn_apply.log                              Р»РѕРі apply/rollback
/usr/local/sbin/vpn-healthcheck.sh               С‚РµСЃС‚ СЃРѕСЃС‚РѕСЏРЅРёСЏ VPN (exit 0 = OK)
/usr/local/sbin/vpn-watchdog.sh                  Р°РІС‚Рѕ-РїРµСЂРµР·Р°РїСѓСЃРє С‚СѓРЅРЅРµР»СЏ, РµСЃР»Рё РѕРЅ СЂРµР°Р»СЊРЅРѕ СѓРїР°Р»
/usr/local/sbin/amneziawg-ensure-module.sh       РїРµСЂРµСЃР±РѕСЂРєР° РјРѕРґСѓР»СЏ СЏРґСЂР° РїСЂРё Р°РїРіСЂРµР№РґРµ СЏРґСЂР°
/etc/systemd/system/awg-quick@awg0.service.d/override.conf   ExecStartPre=ensure-module
/etc/systemd/system/vpn-watchdog.{service,timer}
/etc/modules-load.d/amneziawg.conf
/usr/src/amneziawg-linux-kernel-module, /usr/src/amneziawg-tools   РёСЃС…РѕРґРЅРёРєРё
```

### РЈСЃС‚Р°РЅРѕРІРєР° СЃ РЅСѓР»СЏ (С‡С‚Рѕ Р±С‹Р»Рѕ СЃРґРµР»Р°РЅРѕ РЅР° РїСЂРѕРґ-СЃРµСЂРІРµСЂРµ)

PPA `ppa:amnezia/amneziawg` Р±РѕР»СЊС€Рµ РЅРµС‚ вЂ” СЃС‚Р°РІРёС‚СЃСЏ РёР· РёСЃС…РѕРґРЅРёРєРѕРІ СЃ GitHub
(GitHub СЃ СЃРµСЂРІРµСЂР° РґРѕСЃС‚СѓРїРµРЅ):

```bash
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential dkms git "linux-headers-$(uname -r)"
# РјРѕРґСѓР»СЊ СЏРґСЂР°
cd /usr/src && git clone --depth=1 https://github.com/amnezia-vpn/amneziawg-linux-kernel-module
cd amneziawg-linux-kernel-module/src && make -j"$(nproc)" && make install && depmod -a && modprobe amneziawg
# СѓС‚РёР»РёС‚С‹ awg / awg-quick
cd /usr/src && git clone --depth=1 https://github.com/amnezia-vpn/amneziawg-tools
cd amneziawg-tools/src && make -j"$(nproc)" && make install
```

РљРѕРЅС„РёРі `/etc/amnezia/amneziawg/awg0.conf` = РєР»РёРµРЅС‚СЃРєРёР№ РєРѕРЅС„РёРі РїСЂРѕС„РёР»СЏ 1234, РЅРѕ:
РґРѕР±Р°РІР»РµРЅРѕ `Table = off`, `MTU = 1280`, `PostUp = /root/vpn_apply.sh`,
`PreDown = /root/vpn_rollback.sh`; СЃС‚СЂРѕРєР° `DNS = ...` СѓРґР°Р»РµРЅР° (С‡С‚РѕР±С‹ awg-quick
РЅРµ С‚СЂРѕРіР°Р» СЃРёСЃС‚РµРјРЅС‹Р№ DNS). Р’РєР»СЋС‡РµРЅРёРµ:

```bash
systemctl enable --now awg-quick@awg0
```

### РђРІС‚РѕР·Р°РїСѓСЃРє РїРѕСЃР»Рµ РїРµСЂРµР·Р°РіСЂСѓР·РєРё СЃРµСЂРІРµСЂР°

В«Р’СЃРµРіРґР° РІРєР»СЋС‡С‘РЅВ» РѕР±РµСЃРїРµС‡РёРІР°СЋС‚:

- `systemctl enable awg-quick@awg0` вЂ” С‚СѓРЅРЅРµР»СЊ + policy-routing (С‡РµСЂРµР· PostUp)
  РїРѕРґРЅРёРјР°СЋС‚СЃСЏ РїСЂРё Р·Р°РіСЂСѓР·РєРµ (РїРѕСЃР»Рµ `network-online.target`);
- `ExecStartPre=/usr/local/sbin/amneziawg-ensure-module.sh` вЂ” РµСЃР»Рё СЏРґСЂРѕ
  РѕР±РЅРѕРІРёР»РѕСЃСЊ Рё РјРѕРґСѓР»СЏ РґР»СЏ РЅРµРіРѕ РЅРµС‚, РѕРЅ РїРµСЂРµСЃРѕР±РёСЂР°РµС‚СЃСЏ РїРµСЂРµРґ СЃС‚Р°СЂС‚РѕРј С‚СѓРЅРЅРµР»СЏ;
- `/etc/modules-load.d/amneziawg.conf` вЂ” РјРѕРґСѓР»СЊ РіСЂСѓР·РёС‚СЃСЏ РЅР° СЂР°РЅРЅРµРј СЌС‚Р°РїРµ;
- `PersistentKeepalive=25` РІ РєРѕРЅС„РёРіРµ вЂ” С‚СѓРЅРЅРµР»СЊ СЃР°Рј РїРµСЂРµСѓСЃС‚Р°РЅР°РІР»РёРІР°РµС‚ handshake;
- **watchdog** `vpn-watchdog.timer` (РєР°Р¶РґС‹Рµ ~3 РјРёРЅ): РµСЃР»Рё handshake СѓСЃС‚Р°СЂРµР» Р
  С‡РµСЂРµР· С‚СѓРЅРЅРµР»СЊ РЅРµС‚ РёРЅС‚РµСЂРЅРµС‚Р° вЂ” РїРµСЂРµР·Р°РїСѓСЃРєР°РµС‚ `awg-quick@awg0`.

### РўРµСЃС‚ / РїСЂРѕРІРµСЂРєР° СЃРѕСЃС‚РѕСЏРЅРёСЏ

Р‘С‹СЃС‚СЂС‹Р№ health-С‚РµСЃС‚ (РїРµС‡Р°С‚Р°РµС‚ СЃС‚Р°С‚СѓСЃ, РєРѕРґ РІРѕР·РІСЂР°С‚Р° 0 = РІСЃС‘ РѕРє):

```bash
ssh root@186.246.7.32 /usr/local/sbin/vpn-healthcheck.sh
```

РџСЂРѕРІРµСЂСЏРµС‚: СЃРµСЂРІРёСЃ enabled+active, СЃРІРµР¶РµСЃС‚СЊ handshake, РІС‹С…РѕРґРЅРѕР№ IP = `95.85.243.43`,
РґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ OpenAI (РЅРµ 403), С‡С‚Рѕ СЃР°Р№С‚ `:5002` Р¶РёРІ.

РџСЂРѕРІРµСЂРєР° РїСѓС‚Рё Р·Р°РіСЂСѓР·РєРё Р‘Р•Р— РїРѕР»РЅРѕР№ РїРµСЂРµР·Р°РіСЂСѓР·РєРё (СѓРґР°Р»РёС‚СЊ РёРЅС‚РµСЂС„РµР№СЃ Рё РїРѕРґРЅСЏС‚СЊ Р·Р°РЅРѕРІРѕ
С‡РµСЂРµР· systemd вЂ” РёРјРёС‚Р°С†РёСЏ СЂРµР±СѓС‚Р°):

```bash
ssh root@186.246.7.32 'awg-quick down awg0; systemctl restart awg-quick@awg0; sleep 5; /usr/local/sbin/vpn-healthcheck.sh'
```

РџРѕР»РЅС‹Р№ С‚РµСЃС‚ СЂРµР±СѓС‚РѕРј (СЃР°Р№С‚ РЅР° ~1 РјРёРЅ РЅРµРґРѕСЃС‚СѓРїРµРЅ РІРѕ РІСЂРµРјСЏ РїРµСЂРµР·Р°РіСЂСѓР·РєРё; VPN РґРѕР»Р¶РµРЅ
РїРѕРґРЅСЏС‚СЊСЃСЏ СЃР°Рј):

```bash
ssh root@186.246.7.32 reboot
# РїРѕРґРѕР¶РґР°С‚СЊ ~1-2 РјРёРЅСѓС‚С‹, Р·Р°С‚РµРј:
ssh root@186.246.7.32 /usr/local/sbin/vpn-healthcheck.sh   # РѕР¶РёРґР°РµРј RESULT: OK
```

### РљР°Рє РїРѕСЃС‚Р°РІРёС‚СЊ Р”Р РЈР“РћР™ VPN (Р·Р°РјРµРЅРёС‚СЊ РїСЂРѕС„РёР»СЊ/СЃРµСЂРІРµСЂ)

Р•СЃР»Рё РїРѕСЏРІРёС‚СЃСЏ РЅРѕРІС‹Р№ VPN (РґСЂСѓРіРѕР№ СЌСЃС‚РѕРЅСЃРєРёР№/РґСЂСѓРіРѕР№ СЃРµСЂРІРµСЂ) СЃ AmneziaWG-РєРѕРЅС„РёРіРѕРј:

1. РџРѕР»РѕР¶РёС‚СЊ РЅРѕРІС‹Р№ РєР»РёРµРЅС‚СЃРєРёР№ РєРѕРЅС„РёРі РІ `/etc/amnezia/amneziawg/awg0.conf`.
2. Р”РѕРїРёСЃР°С‚СЊ/СЃРѕС…СЂР°РЅРёС‚СЊ РІ СЃРµРєС†РёРё `[Interface]`:
   `Table = off`, `MTU = 1280`,
   `PostUp = /root/vpn_apply.sh`, `PreDown = /root/vpn_rollback.sh`;
   СѓРґР°Р»РёС‚СЊ СЃС‚СЂРѕРєСѓ `DNS = ...`.
3. РџРµСЂРµР·Р°РїСѓСЃС‚РёС‚СЊ Рё РїСЂРѕРІРµСЂРёС‚СЊ:

```bash
systemctl restart awg-quick@awg0
/usr/local/sbin/vpn-healthcheck.sh
```

РњРµРЅСЏС‚СЊ `vpn_apply.sh` РќР• РЅСѓР¶РЅРѕ вЂ” IP РЅРѕРІРѕРіРѕ VPN-СЃРµСЂРІРµСЂР° (endpoint) РѕРЅ РѕРїСЂРµРґРµР»СЏРµС‚
СЃР°Рј РёР· С‚СѓРЅРЅРµР»СЏ. Р•СЃР»Рё РЅРѕРІС‹Р№ VPN вЂ” РѕР±С‹С‡РЅС‹Р№ WireGuard (Р±РµР· РѕР±С„СѓСЃРєР°С†РёРё), РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ
СЃС‚Р°РЅРґР°СЂС‚РЅС‹Р№ `wg`/`wg-quick` Рё `/etc/wireguard/awg0.conf`, РѕСЃС‚Р°Р»СЊРЅР°СЏ Р»РѕРіРёРєР° С‚Р° Р¶Рµ.

### РћС‚РєР°С‚ / РІСЂРµРјРµРЅРЅРѕ РѕС‚РєР»СЋС‡РёС‚СЊ VPN (СЃРµСЂРІРµСЂ РІРµСЂРЅС‘С‚СЃСЏ РЅР° РїСЂСЏРјРѕР№ IP, СЃР°Р№С‚ РїСЂРѕРґРѕР»Р¶РёС‚ СЂР°Р±РѕС‚Р°С‚СЊ)

```bash
ssh root@186.246.7.32 'bash /root/vpn_rollback.sh && awg-quick down awg0'
# РѕС‚РєР»СЋС‡РёС‚СЊ Рё Р°РІС‚РѕР·Р°РїСѓСЃРє:
ssh root@186.246.7.32 'systemctl disable --now awg-quick@awg0 vpn-watchdog.timer'
```

### Р”РёР°РіРЅРѕСЃС‚РёРєР°

```bash
awg show awg0                       # handshake, С‚СЂР°С„РёРє, endpoint
ip rule show                        # РґРѕР»Р¶РЅС‹ Р±С‹С‚СЊ РїСЂР°РІРёР»Р° 900/901/902/1000/1001
ip route show table 200             # default dev awg0 + РїСЂСЏРјС‹Рµ РјР°СЂС€СЂСѓС‚С‹ endpoint/DNS
tail -n 40 /root/vpn_apply.log
journalctl -t vpn-watchdog -n 20    # СЃСЂР°Р±Р°С‚С‹РІР°РЅРёСЏ СЃС‚РѕСЂРѕР¶Р°
curl -s https://ifconfig.me/ip      # РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ 95.85.243.43
```

РљСЂРѕСЃСЃ-РїСЂРѕРІРµСЂРєР° СЃ СЌСЃС‚РѕРЅСЃРєРѕР№ СЃС‚РѕСЂРѕРЅС‹ (endpoint РїРёСЂР° `10.8.2.2` РґРѕР»Р¶РµРЅ РїРѕРєР°Р·С‹РІР°С‚СЊ
`186.246.7.32` вЂ” СЌС‚Рѕ Рё РµСЃС‚СЊ РїСЂРѕРґ-СЃРµСЂРІРµСЂ):

```bash
ssh root@95.85.243.43 "docker exec amnezia-awg-1234 wg show wg0"
```

## Codex (OpenAI) РЅР° РїСЂРѕРґ-СЃРµСЂРІРµСЂРµ

РЈСЃС‚Р°РЅРѕРІР»РµРЅ `@openai/codex` (codex-cli) РіР»РѕР±Р°Р»СЊРЅРѕ С‡РµСЂРµР· npm (Node 20+ СѓР¶Рµ РµСЃС‚СЊ):

```bash
npm install -g @openai/codex
codex --version
```

**Р’С…РѕРґ РІ ChatGPT-Р°РєРєР°СѓРЅС‚ РќРђ СЃРµСЂРІРµСЂРµ РЅР°РїСЂСЏРјСѓСЋ СЃРґРµР»Р°С‚СЊ РЅРµР»СЊР·СЏ:** OpenAI (Cloudflare)
Р±Р»РѕРєРёСЂСѓРµС‚ СЃС‚СЂР°РЅРёС†С‹ РІС…РѕРґР° Рё `codex login --device-auth` СЃ СЃРµСЂРІРµСЂРЅС‹С…/РґР°С‚Р°-С†РµРЅС‚СЂРѕРІС‹С…
IP (403). РџСЂРё СЌС‚РѕРј СЃР°Рј СЂР°РЅС‚Р°Р№Рј Codex СЃ СѓР¶Рµ РіРѕС‚РѕРІС‹Рј С‚РѕРєРµРЅРѕРј С‡РµСЂРµР· VPN СЂР°Р±РѕС‚Р°РµС‚.
РџРѕСЌС‚РѕРјСѓ РІС…РѕРґ РїРµСЂРµРЅРѕСЃРёС‚СЃСЏ СЃ РџРљ:

1. РќР° РџРљ, РіРґРµ Codex Р·Р°Р»РѕРіРёРЅРµРЅ РІ ChatGPT (`codex login` С‡РµСЂРµР· Р±СЂР°СѓР·РµСЂ), РІР·СЏС‚СЊ С„Р°Р№Р»
   `%USERPROFILE%\.codex\auth.json` (Windows) РёР»Рё `~/.codex/auth.json` (Linux/mac).
2. РџРѕР»РѕР¶РёС‚СЊ РµРіРѕ РЅР° СЃРµСЂРІРµСЂ РІ `/root/.codex/auth.json` (chmod 600).
3. РџСЂРѕРІРµСЂРёС‚СЊ: `codex login status` в†’ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ `Logged in using ChatGPT`.

**РљСЂРёС‚РёС‡РЅРѕ:** Р±РµР· Р±Р»РѕРєРёСЂРѕРІРєРё РёСЃС…РѕРґСЏС‰РµРіРѕ IPv6 (СЃРј. VPN-СЂР°Р·РґРµР», РѕРЅР° РІ `vpn_apply.sh`)
Codex РёРґС‘С‚ РІ `wss://chatgpt.com/backend-api/codex/responses` РїРѕ СЂРѕСЃСЃРёР№СЃРєРѕРјСѓ IPv6 РІ
РѕР±С…РѕРґ VPN Рё РїРѕР»СѓС‡Р°РµС‚ `403`. РЎ Р±Р»РѕРєРёСЂРѕРІРєРѕР№ IPv6 С‚СЂР°С„РёРє РёРґС‘С‚ С‡РµСЂРµР· IPv4-VPN (Р­СЃС‚РѕРЅРёСЏ),
Рё Р±СЌРєРµРЅРґ РѕС‚РІРµС‡Р°РµС‚.

РўРµСЃС‚ Р·Р°РїСЂРѕСЃР° СЃ СЃРµСЂРІРµСЂР°:

```bash
cd /tmp && printf "Respond with exactly: PING-OK" | codex exec --skip-git-repo-check
```

- Р РµР°Р»СЊРЅР°СЏ СЂР°Р±РѕС‚Р° Codex Р·Р°РІРёСЃРёС‚ РѕС‚ С‚Р°СЂРёС„Р° ChatGPT-Р°РєРєР°СѓРЅС‚Р°: РЅР° Р±РµСЃРїР»Р°С‚РЅРѕРј Р±СѓРґРµС‚
  `You've hit your usage limit` вЂ” РЅСѓР¶РµРЅ ChatGPT Plus/Pro СЃ РєРІРѕС‚РѕР№ Codex.
- Р•СЃР»Рё РІС…РѕРґ РЅР° СЃРµСЂРІРµСЂРµ В«РїСЂРѕС‚СѓС…В» (С‚РѕРєРµРЅ РёСЃС‚С‘Рє Рё РЅРµ РѕР±РЅРѕРІР»СЏРµС‚СЃСЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё) вЂ”
  РїСЂРѕСЃС‚Рѕ Р·Р°РЅРѕРІРѕ СЃРєРѕРїРёСЂРѕРІР°С‚СЊ СЃРІРµР¶РёР№ `~/.codex/auth.json` СЃ РџРљ.
- Р›РѕРіРёРЅ/РїР°СЂРѕР»СЊ ChatGPT РІ `.env` (`GPT Р›РѕРіРёРЅ`/`GPT_Password`) РґР»СЏ РІС…РѕРґР° Codex
  Р±РµСЃРїРѕР»РµР·РЅС‹ (РІС…РѕРґ С‚РѕР»СЊРєРѕ Р±СЂР°СѓР·РµСЂРѕРј) вЂ” РёС… Р»СѓС‡С€Рµ СѓР±СЂР°С‚СЊ РёР· `.env`.

## Hermes Agent (Р°РІС‚РѕРЅРѕРјРЅС‹Р№ РР-Р°РіРµРЅС‚, РјРѕР·Рі = ChatGPT Plus)

РќР°СЃС‚СЂРѕРµРЅРѕ 2026-05-27. РџРѕСЃС‚Р°РІР»РµРЅ Р»РѕРєР°Р»СЊРЅРѕ РЅР° РџРљ РІ WSL2 РґР»СЏ С‚РµСЃС‚Р°; СЃР»РµРґСѓСЋС‰РёР№ С€Р°Рі вЂ”
РїРµСЂРµРЅРѕСЃ РЅР° РїСЂРѕРґ-СЃРµСЂРІРµСЂ.

### Р§С‚Рѕ СЌС‚Рѕ Рё Р·Р°С‡РµРј

`Hermes Agent` (Nous Research, open-source) вЂ” Р°РІС‚РѕРЅРѕРјРЅС‹Р№ Р°РіРµРЅС‚ СЃ **РїРѕСЃС‚РѕСЏРЅРЅРѕР№
РїР°РјСЏС‚СЊСЋ, РЅР°РІС‹РєР°РјРё, cron-РїР»Р°РЅРёСЂРѕРІС‰РёРєРѕРј Рё MCP-РєР»РёРµРЅС‚РѕРј**. РћРЅ **model-agnostic**:
СЃРІРѕРµРіРѕ В«РјРѕР·РіР°В» Сѓ РЅРµРіРѕ РЅРµС‚, РјРѕРґРµР»СЊ РїРѕРґРєР»СЋС‡Р°РµС‚СЃСЏ РїРѕ OAuth/API. Р­С‚Рѕ **РѕР±РІСЏР·РєР°-Р°РіРµРЅС‚**
(РєР°Рє Codex/Cline), Р° РќР• РјРѕРґРµР»СЊ.

РќР°С€Р° Р·Р°РґР°С‡Р°: В«С†РёС„СЂРѕРІРѕР№ СЃРѕС‚СЂСѓРґРЅРёРєВ» РїРѕ РѕС‚С‡С‘С‚Р°Рј/РґРµР№СЃС‚РІРёСЏРј (Р° РЅРµ РїСЂР°РІРєР° РєРѕРґР°). Albery
СѓР¶Рµ РѕС‚РґР°С‘С‚ РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹ РґР»СЏ СЌС‚РѕРіРѕ С‡РµСЂРµР· MCP вЂ” Hermes РІС‹СЃС‚СѓРїР°РµС‚ Р°РІС‚РѕРЅРѕРјРЅС‹Рј
РёСЃРїРѕР»РЅРёС‚РµР»РµРј РїРѕРІРµСЂС… РЅРёС…. В«РњРѕР·РіВ» СЃРµР№С‡Р°СЃ вЂ” **ChatGPT Plus (РјРѕРґРµР»СЊ `gpt-5.5`)**.

### РљР»СЋС‡РµРІС‹Рµ РїСѓС‚Рё Рё С„Р°РєС‚С‹

```text
РІРµСЂСЃРёСЏ:        v0.14.0
Р±РёРЅР°СЂСЊ:        ~/.local/bin/hermes
СѓСЃС‚Р°РЅРѕРІРєР°:     ~/.hermes/hermes-agent
РєРѕРЅС„РёРі:        ~/.hermes/config.yaml
С‚РѕРєРµРЅС‹ Р°РєРєР°СѓРЅС‚РѕРІ: ~/.hermes/auth.json   в†ђ РґР»СЏ СЃРјРµРЅС‹ Р°РєРєР°СѓРЅС‚Р° Рё РїРµСЂРµРЅРѕСЃР° РЅР° СЃРµСЂРІРµСЂ
РїСЂРѕРІР°Р№РґРµСЂ:     openai-codex   (= Р°РєРєР°СѓРЅС‚ ChatGPT С‡РµСЂРµР· OAuth)
РјРѕРґРµР»СЊ:        gpt-5.5        (РґРѕСЃС‚СѓРїРЅР° Рё gpt-5.4)
РґР°С€Р±РѕСЂРґ:       http://127.0.0.1:9119   (hermes dashboard --tui)
```

### Р’Р°Р¶РЅС‹Рµ РїРѕРЅСЏС‚РёСЏ (С‡С‚РѕР±С‹ РЅРµ РїСѓС‚Р°С‚СЊ)

- РџСЂРѕРІР°Р№РґРµСЂ **`openai-codex`** вЂ” СЌС‚Рѕ РќР• РѕС‚РґРµР»СЊРЅС‹Р№ СѓСЂРµР·Р°РЅРЅС‹Р№ РїСЂРѕРґСѓРєС‚, Р° С‚РµС…РЅРёС‡РµСЃРєРёР№
  **OAuth-РєР°РЅР°Р» Рє С‚РІРѕРµРјСѓ Р°РєРєР°СѓРЅС‚Сѓ ChatGPT**. РњРѕРґРµР»СЊ `gpt-5.5` вЂ” РѕР±С‹С‡РЅР°СЏ ChatGPT.
- РџРѕРґРїРёСЃРєСѓ ChatGPT РІ Hermes РјРѕР¶РЅРѕ РїРѕРґРєР»СЋС‡РёС‚СЊ **С‚РѕР»СЊРєРѕ** С‡РµСЂРµР· `openai-codex`.
  РџСЂРѕРІР°Р№РґРµСЂ `openai` РёСЃРїРѕР»СЊР·СѓРµС‚ **API-РєР»СЋС‡**, Р° РЅРµ РїРѕРґРїРёСЃРєСѓ.
- **Р›РёРјРёС‚С‹**: РЅР° РїРѕРґРїРёСЃРєРµ Plus РѕРЅРё РµСЃС‚СЊ РІСЃРµРіРґР°, РєР°Рє РЅРё РїРѕРґРєР»СЋС‡Р°Р№СЃСЏ. В«Р‘РµР· РїРѕС‚РѕР»РєР°В» вЂ”
  С‚РѕР»СЊРєРѕ **API-РєР»СЋС‡** (РїР»Р°С‚РёС€СЊ РїРѕ С‚РѕРєРµРЅР°Рј). Р”Р»СЏ Р°РІС‚РѕРЅРѕРјРЅРѕРіРѕ Р°РіРµРЅС‚Р° 24/7 РЅР° СЃРµСЂРІРµСЂРµ
  РїСЂР°РІРёР»СЊРЅРµРµ API-РєР»СЋС‡; РїРѕРґРїРёСЃРєР° Plus РїРµСЂРёРѕРґРёС‡РµСЃРєРё Р±СѓРґРµС‚ СѓРїРёСЂР°С‚СЊСЃСЏ РІ `usage limit`.

### РџСЂРµРґСѓСЃР»РѕРІРёРµ РЅР° Windows-РџРљ: СЃРµС‚СЊ WSL2 С‡РµСЂРµР· VPN

`AmneziaVPN` РЅР° Windows Р»РѕРјР°РµС‚ СЃРµС‚СЊ РІРЅСѓС‚СЂРё WSL2 (РёСЃС…РѕРґСЏС‰РёР№ TCP РІРёСЃРЅРµС‚). Р›РµС‡РёС‚СЃСЏ
**mirrored-СЂРµР¶РёРјРѕРј** вЂ” WSL РЅР°С‡РёРЅР°РµС‚ С…РѕРґРёС‚СЊ С‡РµСЂРµР· СЃРµС‚РµРІРѕР№ СЃС‚РµРє С…РѕСЃС‚Р° (РІРјРµСЃС‚Рµ СЃ VPN,
РІС‹С…РѕРґ С‡РµСЂРµР· Р­СЃС‚РѕРЅРёСЋ `95.85.243.43`), Рё API OpenAI/Anthropic СЃС‚Р°РЅРѕРІСЏС‚СЃСЏ РґРѕСЃС‚СѓРїРЅС‹.

РЎРѕР·РґР°С‚СЊ `C:\Users\<user>\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
```

Р—Р°С‚РµРј `wsl --shutdown` (РїРµСЂРµР·Р°РїСѓСЃРє WSL). РџСЂРѕРІРµСЂРєР° РёР· WSL:
`curl -s https://api.ipify.org` в†’ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ `95.85.243.43`.

### РЈСЃС‚Р°РЅРѕРІРєР° Hermes (Linux / WSL2 / СЃРµСЂРІРµСЂ)

РўСЂРµР±СѓРµС‚СЃСЏ **Node.js 20+** (РґР»СЏ СЃР±РѕСЂРєРё РІРµР±-РґР°С€Р±РѕСЂРґР° РЅР° Vite) Рё Python 3.11
(СЃС‚Р°РІРёС‚ СѓСЃС‚Р°РЅРѕРІС‰РёРє СЃР°Рј). РќР° РїСЂРѕРґ-СЃРµСЂРІРµСЂРµ Node 20 СѓР¶Рµ РµСЃС‚СЊ; РІ WSL СЃС‚Р°РІРёР»СЃСЏ nvm-РѕРј.

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc        # РёР»Рё РЅРѕРІС‹Р№ С‚РµСЂРјРёРЅР°Р»
hermes --version
```

- РЈСЃС‚Р°РЅРѕРІС‰РёРє СЃС‚Р°РІРёС‚ uv, Python 3.11, РєР»РѕРЅРёСЂСѓРµС‚ СЂРµРїРѕ, СЃРѕР·РґР°С‘С‚ venv.
- РћРїС†РёРѕРЅР°Р»СЊРЅС‹Рµ `ripgrep`/`ffmpeg` С‚СЂРµР±СѓСЋС‚ sudo вЂ” РјРѕР¶РЅРѕ РїСЂРѕРїСѓСЃС‚РёС‚СЊ (Р°РіРµРЅС‚ СЂР°Р±РѕС‚Р°РµС‚
  Р±РµР· РЅРёС…; РїРѕРёСЃРє РёРґС‘С‚ С‡РµСЂРµР· grep).
- **Р’РђР–РќРћ РїСЂРё РЅРµРёРЅС‚РµСЂР°РєС‚РёРІРЅРѕРј Р·Р°РїСѓСЃРєРµ** (С„РѕРЅ, `curl | bash` Р±РµР· С‚РµСЂРјРёРЅР°Р»Р°):
  СѓСЃС‚Р°РЅРѕРІС‰РёРє С‡РёС‚Р°РµС‚ `/dev/tty` Рё **РІРёСЃРЅРµС‚ РЅР° sudo-РІРѕРїСЂРѕСЃРµ РїСЂРѕ ripgrep/ffmpeg**.
  Р—Р°РїСѓСЃРєР°С‚СЊ РІ СЃРµР°РЅСЃРµ Р±РµР· СѓРїСЂР°РІР»СЏСЋС‰РµРіРѕ С‚РµСЂРјРёРЅР°Р»Р° (`setsid`) Рё СЃ С„Р»Р°РіР°РјРё
  `--skip-setup --skip-browser`, Р»РёР±Рѕ РїСЂРѕСЃС‚Рѕ СЃС‚Р°РІРёС‚СЊ РІ Р¶РёРІРѕРј SSH-С‚РµСЂРјРёРЅР°Р»Рµ.

Р•СЃР»Рё РІ СЃРёСЃС‚РµРјРµ СЃС‚Р°СЂС‹Р№ Node вЂ” РїРѕСЃС‚Р°РІРёС‚СЊ 20 С‡РµСЂРµР· nvm (Р±РµР· sudo):

```bash
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"
nvm install 20 && nvm alias default 20
# Р·Р°С‚РµРј РїРµСЂРµСЃРѕР±СЂР°С‚СЊ РІРµР±-РјРѕСЂРґСѓ РґР°С€Р±РѕСЂРґР°:
cd ~/.hermes/hermes-agent/web && rm -rf node_modules package-lock.json && npm install && npm run build
```

### РџРѕРґРєР»СЋС‡РµРЅРёРµ Р°РєРєР°СѓРЅС‚Р° ChatGPT (openai-codex, OAuth device-code)

```bash
hermes auth add openai-codex --type oauth
```

- РџРѕРєР°Р¶РµС‚ URL `https://auth.openai.com/codex/device` Рё РєРѕСЂРѕС‚РєРёР№ РєРѕРґ.
- Р’ Р±СЂР°СѓР·РµСЂРµ СЃРЅР°С‡Р°Р»Р° **РІРѕР№С‚Рё РІ Р°РєРєР°СѓРЅС‚ ChatGPT** (СЃС‚СЂР°РЅРёС†Р° РїРµСЂРµРєРёРЅРµС‚ РЅР° `/log-in`),
  РїРѕС‚РѕРј **СЃРЅРѕРІР° РѕС‚РєСЂС‹С‚СЊ** `/codex/device`, РІРІРµСЃС‚Рё РєРѕРґ, РїРѕРґС‚РІРµСЂРґРёС‚СЊ (Authorize).
- РђРєРєР°СѓРЅС‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ **Plus/Pro** вЂ” РЅР° Р±РµСЃРїР»Р°С‚РЅРѕРј Р±СѓРґРµС‚ `usage limit`.
- РўРѕРєРµРЅ СЃРѕС…СЂР°РЅСЏРµС‚СЃСЏ РІ `~/.hermes/auth.json`. РџСЂРѕРІРµСЂРєР°: `hermes auth list`.
- **IP-РЅСЋР°РЅСЃ**: РІС…РѕРґ СЃ РґР°С‚Р°С†РµРЅС‚СЂРѕРІРѕРіРѕ IP Cloudflare РјРѕР¶РµС‚ Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ (`403`).
  РќР° РџРљ (С‡РµСЂРµР· VPN-Р­СЃС‚РѕРЅРёСЋ) СЃСЂР°Р±РѕС‚Р°Р»Рѕ. РќР° СЃРµСЂРІРµСЂРµ РІС…РѕРґ РјРѕР¶РµС‚ РЅРµ РїСЂРѕР№С‚Рё вЂ” СЃРј. РїРµСЂРµРЅРѕСЃ.

### РџСЂРѕРІР°Р№РґРµСЂ Рё РјРѕРґРµР»СЊ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ

```bash
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5      # РёР»Рё gpt-5.4; РёРЅС‚РµСЂР°РєС‚РёРІРЅРѕ: hermes model
# РїСЂРѕРІРµСЂРєР°:
printf '' | hermes -z "Respond with exactly: PING-OK"
```

### РЎРјРµРЅР° Р°РєРєР°СѓРЅС‚Р° / РїСЂРѕРІР°Р№РґРµСЂР°

Р”Р»СЏ СЃРµСЂРІРµСЂР° `217.198.12.236` РґРѕР±Р°РІР»РµРЅ Р±С‹СЃС‚СЂС‹Р№ Р»РѕРєР°Р»СЊРЅС‹Р№ РјРµРЅРµРґР¶РµСЂ Р°РєРєР°СѓРЅС‚РѕРІ Hermes/Codex:

```powershell
.\scripts\hermes-codex-accounts.cmd          # double-click/launcher for Windows
.\scripts\hermes-codex-accounts.ps1          # РјРµРЅСЋ: СЃРїРёСЃРѕРє, РёРјРїРѕСЂС‚ С‚РµРєСѓС‰РµРіРѕ Codex, Р°РєС‚РёРІР°С†РёСЏ
python scripts/hermes_codex_accounts.py --target new list
python scripts/hermes_codex_accounts.py --target new import-current
python scripts/hermes_codex_accounts.py --target new activate 2
python scripts/hermes_codex_accounts.py --target new ensure-failover
```

Р§С‚Рѕ РґРµР»Р°РµС‚ `import-current`: С‡РёС‚Р°РµС‚ Р»РѕРєР°Р»СЊРЅС‹Р№ `%USERPROFILE%\.codex\auth.json`, РєРѕРЅРІРµСЂС‚РёСЂСѓРµС‚
РµРіРѕ РІ `openai-codex` credential РґР»СЏ `/root/.hermes/auth.json`, РґРµР»Р°РµС‚ Р±СЌРєР°Рї РІ
`/root/.hermes/auth-backups/`, СЃС‚Р°РІРёС‚ РёРјРїРѕСЂС‚РёСЂРѕРІР°РЅРЅС‹Р№ Р°РєРєР°СѓРЅС‚ priority `0` Рё РїРµСЂРµР·Р°РїСѓСЃРєР°РµС‚
`hermes-gateway`. РўРѕРєРµРЅС‹ РЅРµ РїРµСЂРµРґР°СЋС‚СЃСЏ РІ Р°СЂРіСѓРјРµРЅС‚Р°С… РєРѕРјР°РЅРґРЅРѕР№ СЃС‚СЂРѕРєРё; Р·Р°РїРёСЃСЊ РёРґС‘С‚ С‡РµСЂРµР· SFTP.
`ensure-failover` РІС‹СЃС‚Р°РІР»СЏРµС‚ `credential_pool_strategies.openai-codex: fill_first`: Hermes
РёСЃРїРѕР»СЊР·СѓРµС‚ Р°РєРєР°СѓРЅС‚ #1 РґРѕ Р»РёРјРёС‚Р°, РїСЂРё `usage limit`/429 РїРѕРјРµС‡Р°РµС‚ РµРіРѕ exhausted Рё Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё
СЂРѕС‚РёСЂСѓРµС‚ РЅР° СЃР»РµРґСѓСЋС‰РёР№ РґРѕСЃС‚СѓРїРЅС‹Р№ Р°РєРєР°СѓРЅС‚ РІ РїСѓР»Рµ.
РџРѕСЃР»Рµ СЃРјРµРЅС‹ Р°РєРєР°СѓРЅС‚Р° РІ Р°РєС‚РёРІРЅРѕРј Telegram-С‡Р°С‚Рµ СЃ Hermes РЅР°РїРёСЃР°С‚СЊ `/reset`, С‡С‚РѕР±С‹ СЃРµСЃСЃРёСЏ
РїРѕРґС‚СЏРЅСѓР»Р° РЅРѕРІС‹Р№ credential.

```bash
hermes auth list                       # С‡С‚Рѕ РїРѕРґРєР»СЋС‡РµРЅРѕ
hermes auth logout openai-codex        # РІС‹Р№С‚Рё РёР· Р°РєРєР°СѓРЅС‚Р°
hermes auth remove <index|id|label>    # СѓРґР°Р»РёС‚СЊ РєРѕРЅРєСЂРµС‚РЅС‹Р№ РєСЂРµРґР»
hermes auth add openai-codex --type oauth   # РІРѕР№С‚Рё Р·Р°РЅРѕРІРѕ (РґСЂСѓРіРёРј Р°РєРєР°СѓРЅС‚РѕРј)
```

РџРµСЂРµРєР»СЋС‡РёС‚СЊСЃСЏ РЅР° **API-РєР»СЋС‡** (Р±РµР· РїРѕС‚РѕР»РєР° Р»РёРјРёС‚РѕРІ, РїР»Р°С‚РЅРѕ РїРѕ С‚РѕРєРµРЅР°Рј):

```bash
hermes auth add openai --type api-key --api-key sk-...     # РёР»Рё anthropic / gemini
hermes config set model.provider openai                    # anthropic | gemini
hermes config set model.default <model-id>
```

Р’РµСЃСЊ С‚РѕРєРµРЅ-СЃС‚РѕСЂ вЂ” РѕРґРёРЅ С„Р°Р№Р» `~/.hermes/auth.json` (РµРіРѕ РјРѕР¶РЅРѕ Р±СЌРєР°РїРёС‚СЊ/РєРѕРїРёСЂРѕРІР°С‚СЊ).

### Р—Р°РїСѓСЃРє

```bash
hermes                       # С‡Р°С‚ РІ С‚РµСЂРјРёРЅР°Р»Рµ
hermes dashboard --tui       # РІРµР±-РґР°С€Р±РѕСЂРґ: С‡Р°С‚ + РЅР°СЃС‚СЂРѕР№РєРё + СЃРµСЃСЃРёРё + cron, РїРѕСЂС‚ 9119
#   РїРѕР»РµР·РЅС‹Рµ С„Р»Р°РіРё: --no-open  --port N  --skip-build (РѕС‚РґР°С‚СЊ РіРѕС‚РѕРІС‹Р№ dist Р±РµР· СЃР±РѕСЂРєРё)
#                   --status   --stop
hermes gateway run           # С„РѕРЅРѕРІС‹Р№ С€Р»СЋР·/cron (РґР»СЏ В«СЃРѕС‚СЂСѓРґРЅРёРєР°В»); install вЂ” РєР°Рє СЃРµСЂРІРёСЃ
```

Р”Р°С€Р±РѕСЂРґ СЃР»СѓС€Р°РµС‚ `127.0.0.1:9119`; РїСЂРё mirrored-WSL РѕС‚РєСЂС‹РІР°РµС‚СЃСЏ РІ Р±СЂР°СѓР·РµСЂРµ Windows
РїРѕ `http://localhost:9119`.

### РџРµСЂРµРЅРѕСЃ РЅР° РїСЂРѕРґ-СЃРµСЂРІРµСЂ (`186.246.7.32`, Ubuntu 22.04)

1. РЈСЃС‚Р°РЅРѕРІРёС‚СЊ (Node 20 С‚Р°Рј СѓР¶Рµ РµСЃС‚СЊ):
   `curl -fsSL .../install.sh | bash` (РІ Р¶РёРІРѕРј SSH-С‚РµСЂРјРёРЅР°Р»Рµ вЂ” TTY-С…Р°Рє РЅРµ РЅСѓР¶РµРЅ).
2. **Р›РѕРіРёРЅ Р°РєРєР°СѓРЅС‚Р°** вЂ” СѓРїСЂС‘С‚СЃСЏ РІ РґР°С‚Р°С†РµРЅС‚СЂРѕРІС‹Р№ IP (РєР°Рє Р±С‹Р»Рѕ СЃ Codex). Р”РІР° РїСѓС‚Рё:
   - **(Р°) device-login:** РЅР° СЃРµСЂРІРµСЂРµ `hermes auth add openai-codex --type oauth`,
     Р° URL+РєРѕРґ РѕС‚РєСЂС‹С‚СЊ/РІРІРµСЃС‚Рё РІ Р±СЂР°СѓР·РµСЂРµ РЅР° РџРљ (Р¶РёР»РѕР№ IP). Р•СЃР»Рё РѕРїСЂРѕСЃ С‚РѕРєРµРЅР° СЃ
     СЃРµСЂРІРµСЂР° РїРѕР»СѓС‡РёС‚ `403` вЂ” РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РїСѓС‚СЊ (Р±).
   - **(Р±) СЃРєРѕРїРёСЂРѕРІР°С‚СЊ РіРѕС‚РѕРІС‹Р№ `~/.hermes/auth.json` СЃ РџРљ РЅР° СЃРµСЂРІРµСЂ** (РєР°Рє РґРµР»Р°Р»Рё СЃ
     `~/.codex/auth.json` РґР»СЏ Codex): `scp ... root@186.246.7.32:/root/.hermes/auth.json`,
     `chmod 600`. РўРѕРіРґР° РѕС‚РґРµР»СЊРЅС‹Р№ РІС…РѕРґ РЅР° СЃРµСЂРІРµСЂРµ РЅРµ РЅСѓР¶РµРЅ.
3. РџСЂРѕРїРёСЃР°С‚СЊ РїСЂРѕРІР°Р№РґРµСЂР°/РјРѕРґРµР»СЊ (`hermes config set ...`, СЃРј. РІС‹С€Рµ).
4. Р”РµСЂР¶Р°С‚СЊ Р·Р°РїСѓС‰РµРЅРЅС‹Рј: `hermes gateway install` (systemd-СЃРµСЂРІРёСЃ, Р°РІС‚РѕР·Р°РїСѓСЃРє) РёР»Рё
   РґР°С€Р±РѕСЂРґ РєР°Рє СЃРµСЂРІРёСЃ.
5. VPN РЅР° СЃРµСЂРІРµСЂРµ СѓР¶Рµ Р·Р°РІРѕСЂР°С‡РёРІР°РµС‚ РёСЃС…РѕРґСЏС‰РёР№ С‚СЂР°С„РёРє С‡РµСЂРµР· Р­СЃС‚РѕРЅРёСЋ (СЃРј. СЂР°Р·РґРµР» РїСЂРѕ
   VPN-С€Р»СЋР·) вЂ” РѕРЅ РЅСѓР¶РµРЅ, РёРЅР°С‡Рµ OpenAI РѕС‚РґР°С‘С‚ `403` СЂРѕСЃСЃРёР№СЃРєРѕРјСѓ IP.

### Р§С‚Рѕ РЅСѓР¶РЅРѕ РґР»СЏ СЂР°Р±РѕС‚С‹ (С‡РµРє-Р»РёСЃС‚)

- **Node 20+** (РґР°С€Р±РѕСЂРґ) Рё Python 3.11 (СЃС‚Р°РІРёС‚ СѓСЃС‚Р°РЅРѕРІС‰РёРє).
- **Р Р°Р±РѕС‡РёР№ РјРѕР·Рі**: `openai-codex` (ChatGPT Plus) РёР»Рё API-РєР»СЋС‡.
- **РќРµСЂРѕСЃСЃРёР№СЃРєРёР№ РёСЃС…РѕРґСЏС‰РёР№ IP** (VPN) вЂ” OpenAI СЂРµР¶РµС‚ Р Р¤.
- Р”Р»СЏ СЂРѕР»Рё В«СЃРѕС‚СЂСѓРґРЅРёРє РїРѕ РѕС‚С‡С‘С‚Р°РјВ» (СЃР»РµРґСѓСЋС‰РёР№ СЌС‚Р°Рї): РїРѕРґРєР»СЋС‡РёС‚СЊ **MCP Albery**
  (СЃРµРєС†РёСЏ `mcp_servers` РІ `~/.hermes/config.yaml`, HTTP-С‚СЂР°РЅСЃРїРѕСЂС‚ РЅР°
  `https://mcp.m4s.ru/mcp/<MCP_SHARED_SECRET>`) Рё РЅР°СЃС‚СЂРѕРёС‚СЊ **cron-Р·Р°РґР°С‡Рё**
  (`hermes cron`) вЂ” С‚РѕРіРґР° Р°РіРµРЅС‚ СЃР°Рј РїРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ С‡РёС‚Р°РµС‚ РёРЅСЃС‚СЂСѓРєС†РёРё, СЃРѕР±РёСЂР°РµС‚
  РґР°РЅРЅС‹Рµ Рё С„РѕСЂРјРёСЂСѓРµС‚ РѕС‚С‡С‘С‚С‹ С‡РµСЂРµР· РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹ Albery.

### РЎР»СѓР¶РµР±РЅРѕРµ (РЅР° РџРљ)

- `C:\Users\<user>\.wslconfig` вЂ” mirrored-СЃРµС‚СЊ WSL (РЅРµ СѓРґР°Р»СЏС‚СЊ, РёРЅР°С‡Рµ WSL СЃРЅРѕРІР°
  РїРѕС‚РµСЂСЏРµС‚ РёРЅС‚РµСЂРЅРµС‚ РїРѕРґ VPN).
- Р Р°Р·РѕРІС‹Рµ РІСЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹Рµ СЃРєСЂРёРїС‚С‹ СѓСЃС‚Р°РЅРѕРІРєРё Р»РµР¶Р°Р»Рё РІ `C:\Users\<user>\*.sh` вЂ”
  РёС… РјРѕР¶РЅРѕ СѓРґР°Р»РёС‚СЊ, РЅР° СЂР°Р±РѕС‚Сѓ Р°РіРµРЅС‚Р° РЅРµ РІР»РёСЏСЋС‚.

### РџСЂРѕРґ-СЂР°Р·РІС‘СЂС‚С‹РІР°РЅРёРµ Hermes (РІС‹РїРѕР»РЅРµРЅРѕ 2026-05-27)

Hermes РїРµСЂРµРЅРµСЃС‘РЅ СЃ РџРљ РЅР° РїСЂРѕРґ-СЃРµСЂРІРµСЂ `186.246.7.32` Рё СЂР°Р±РѕС‚Р°РµС‚ **24/7** РєР°Рє
systemd-СЃР»СѓР¶Р±Р°. РњРѕР·Рі вЂ” ChatGPT Plus (`gpt-5.5`) С‡РµСЂРµР· `openai-codex` OAuth.
Р§С‚РѕР±С‹ РЅРµ СЃР¶РёРіР°С‚СЊ 5-С‡Р°СЃРѕРІРѕР№ Р»РёРјРёС‚ Codex, reasoning РЅР° РїСЂРѕРґРµ СЃРЅРёР¶РµРЅ РґРѕ `medium`:
`model.reasoning_effort=medium` Рё `agent.reasoning_effort=medium`.

Р Р°СЃРїРѕР»РѕР¶РµРЅРёРµ РЅР° СЃРµСЂРІРµСЂРµ:

```text
Р±РёРЅР°СЂСЊ:   /usr/local/bin/hermes
РєРѕРґ:      /usr/local/lib/hermes-agent
РґРѕРј:      /root/.hermes/   (config.yaml, .env, cron/, sessions/, logs/, state.db)
СЃР»СѓР¶Р±Р°:   /etc/systemd/system/hermes-gateway.service  (enabled+active, Р°РІС‚РѕР·Р°РїСѓСЃРє)
```

Р§С‚Рѕ СЃРґРµР»Р°РЅРѕ:

- **Р’С…РѕРґ РІ ChatGPT:** `/root/.hermes/auth.json` СЃРєРѕРїРёСЂРѕРІР°РЅ СЃ РџРљ (chmod 600) вЂ” РІС…РѕРґ
  РЅР° СЃРµСЂРІРµСЂРЅРѕРј IP Р±Р»РѕРєРёСЂСѓРµС‚ Cloudflare, Р° РіРѕС‚РѕРІС‹Р№ С‚РѕРєРµРЅ СЂР°Р±РѕС‚Р°РµС‚ С‡РµСЂРµР· VPN-Р­СЃС‚РѕРЅРёСЋ.
- **Swap:** РґРѕР±Р°РІР»РµРЅ `/swapfile` 2 Р“Р‘ (`vm.swappiness=10`, РІ `/etc/fstab`) вЂ” СЃС‚СЂР°С…РѕРІРєР°
  РѕС‚ OOM РЅР° 2 Р“Р‘ RAM. РЎР°Рј Р°РіРµРЅС‚ Р»С‘РіРєРёР№ (~185вЂ“270 РњР‘), РјРѕРґРµР»СЊ СЃС‡РёС‚Р°РµС‚СЃСЏ СѓРґР°Р»С‘РЅРЅРѕ.
- **MCP:** РІ `/root/.hermes/config.yaml` СЃРµРєС†РёСЏ `mcp_servers.albery` =
  `https://mcp.m4s.ru/mcp/<MCP_SHARED_SECRET>` (СЃРµРєСЂРµС‚ РёР· `/var/www/albery/.env`,
  auth none). 38 РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ. TZ СЃРµСЂРІРµСЂР° = Europe/Moscow, РїРѕСЌС‚РѕРјСѓ cron-РІСЂРµРјСЏ вЂ” РњРЎРљ.
- **Gateway-СЃР»СѓР¶Р±Р°:** `hermes gateway install --system --run-as-user root`
  (РїРѕРґ root, С‚.Рє. РІРµСЃСЊ СЃС‚РµРє С‚СѓС‚ РїРѕРґ root). РџР»Р°РЅРёСЂРѕРІС‰РёРє cron СЂР°Р±РѕС‚Р°РµС‚ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё.
- **Telegram:** РїРѕРґРєР»СЋС‡С‘РЅ Рє gateway С‡РµСЂРµР· `/root/.hermes/.env`:
  `TELEGRAM_BOT_TOKEN=<РёР· .env TG_BOT_TOKEN>` Рё
  `TELEGRAM_ALLOWED_USERS=<РёР· .env TG_ID>`. РЈСЃС‚Р°РЅРѕРІР»РµРЅР° Р·Р°РІРёСЃРёРјРѕСЃС‚СЊ
  `python-telegram-bot[webhooks]` РІ `/usr/local/lib/hermes-agent/venv`.
  РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅР°Р¶Р°Р» `/start`, РїРѕСЃР»Рµ СЌС‚РѕРіРѕ РїСЂРѕРІРµСЂРѕС‡РЅС‹Р№ РїСѓС€ С‡РµСЂРµР·
  `hermes send --to telegram:<TG_ID> ...` РІРµСЂРЅСѓР»СЃСЏ `sent`.
- **РўРёС…РёР№ Telegram-СЂРµР¶РёРј:** РІ `/root/.hermes/config.yaml` РІРєР»СЋС‡РµРЅРѕ
  `display.platforms.telegram.tool_progress: off` вЂ” Telegram РЅРµ РїРѕРєР°Р·С‹РІР°РµС‚
  С‚РµС…РЅРёС‡РµСЃРєРёРµ tool-calls РІРёРґР° `mcp_albery_*`; Рё `cron.wrap_response: false` вЂ”
  cron РїСЂРёСЃС‹Р»Р°РµС‚ С‚РѕР»СЊРєРѕ С‡РёСЃС‚С‹Р№ РѕС‚РІРµС‚ Р°РіРµРЅС‚Р° Р±РµР· РѕР±С‘СЂС‚РєРё `Cronjob Response`,
  `job_id` Рё РїРѕРґСЃРєР°Р·РєРё `stop reminder`.

Р”РІРµ Р°РІС‚РѕРјР°С‚РёР·Р°С†РёРё (`hermes cron list`):

- `zoom-to-tasks` вЂ” `*/30 * * * *`: РЅР°С…РѕРґРёС‚ Zoom-СЃРѕР·РІРѕРЅС‹ Р±РµР· РѕС‚С‡С‘С‚Р°
  **Р±РµР· СЂР°СЃС…РѕРґР° Codex РЅР° РїСѓСЃС‚С‹С… РїСЂРѕРІРµСЂРєР°С…**. Р РµР°Р»РёР·РѕРІР°РЅРѕ РєР°Рє `no-agent` cron
  СЃРѕ СЃРєСЂРёРїС‚РѕРј `/root/.hermes/scripts/zoom_watchdog.sh`: СЃРєСЂРёРїС‚ РЅР°РїСЂСЏРјСѓСЋ Рё Р±С‹СЃС‚СЂРѕ
  РїСЂРѕРІРµСЂСЏРµС‚ PostgreSQL (`zoom_calls` Р·Р° РїРѕСЃР»РµРґРЅРёРµ 2 РґРЅСЏ, `analytical_note=''`,
  С‚СЂР°РЅСЃРєСЂРёРїС‚ РµСЃС‚СЊ). Р•СЃР»Рё РЅРѕРІС‹С… Zoom РЅРµС‚ вЂ” stdout РїСѓСЃС‚РѕР№, Telegram РјРѕР»С‡РёС‚, LLM РЅРµ
  РІС‹Р·С‹РІР°РµС‚СЃСЏ. Р•СЃР»Рё РµСЃС‚СЊ РЅРѕРІС‹Р№ Zoom вЂ” С‚РѕР»СЊРєРѕ С‚РѕРіРґР° СЃРєСЂРёРїС‚ Р·Р°РїСѓСЃРєР°РµС‚ `hermes -z` СЃ
  РїСЂРѕРјРїС‚РѕРј РёР· `/root/.hermes/scripts/hermes_zoom_to_tasks_prompt.txt`
  (РёСЃС‚РѕС‡РЅРёРє РїСЂР°РІРґС‹ РІ git: [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt)).
  РџСЂРѕРјРїС‚ РїРѕРґСЃС‚Р°РІР»СЏРµС‚ `$DATE_FROM`, `$DATE_TO`, `$MISSING` С‡РµСЂРµР· awk-substitution
  (Р±РµР· РїСЂРѕР±Р»РµРј СЃРѕ sed-escaping РґР»СЏ РјРЅРѕРіРѕСЃС‚СЂРѕС‡РЅС‹С… Р·РЅР°С‡РµРЅРёР№).
  Р’ СЃРєСЂРёРїС‚Рµ РµСЃС‚СЊ `flock` Рё cooldown 7200 СЃРµРє РЅР° С‚РѕС‚ Р¶Рµ РЅР°Р±РѕСЂ missing-call id,
  С‡С‚РѕР±С‹ РїСЂРё РѕС€РёР±РєРµ РЅРµ Р¶РµС‡СЊ Р»РёРјРёС‚ РєР°Р¶РґС‹Рµ 30 РјРёРЅСѓС‚.

  **Р§С‚Рѕ РґРµР»Р°РµС‚ Р°РіРµРЅС‚.** РџРѕ РїСЂРѕРјРїС‚Сѓ СЃС‚СЂРѕРіРѕ:
  1. `start_here_always_read_ai_instructions` в†’ `get_context_guide`;
  2. РґР»СЏ РєР°Р¶РґРѕРіРѕ СЃРѕР·РІРѕРЅР°: `get_report_contract(zoom_processing)` (РєРѕРЅС‚СЂР°РєС‚ вЂ” 13 KB, 12 СЂР°Р·РґРµР»РѕРІ РІ `report_text` + JSON-СЃС…РµРјР° СЃ РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рј `operational_tasks`), `get_zoom_call_transcript(include_full_text=true)`, `get_org_structure`;
  3. С„РѕСЂРјРёСЂСѓРµС‚ РѕС‚С‡С‘С‚ **СЃС‚СЂРѕРіРѕ РїРѕ РєРѕРЅС‚СЂР°РєС‚Сѓ** (12 СЂР°Р·РґРµР»РѕРІ + РїРѕР»РЅС‹Р№ JSON) Рё СЃРѕС…СЂР°РЅСЏРµС‚ С‡РµСЂРµР· `save_zoom_call_report` вЂ” СЌС‚Рѕ РєР»Р°РґС‘С‚ `analytical_note` Рё `raw_json.ai_report.analysis.operational_tasks`;
  4. РІ Р‘РёС‚СЂРёРєСЃ Р·Р°РґР°С‡Рё РќР• СЃРѕР·РґР°С‘С‚ (verification mode).

  **Р§С‚Рѕ РїСЂРёС…РѕРґРёС‚ РІ Telegram (С„РѕСЂРјР°С‚ РїСЂРёРЅС†РёРїРёР°Р»СЊРЅРѕ РєРѕСЂРѕС‚РєРёР№).** РќРёРєР°РєРѕРіРѕ РїРµСЂРµСЃРєР°Р·Р° РѕС‚С‡С‘С‚Р°, РЅРёРєР°РєРёС… СЂР°Р·РґРµР»РѕРІ В«РљСЂР°С‚РєР°СЏ СЃСѓС‚СЊВ» / В«Р РёСЃРєРёВ» / В«Р’С‹РІРѕРґС‹В»:
  ```
  РЎРѕР·РІРѕРЅ: <Р”Р”.РњРњ.Р“Р“Р“Р“> вЂ” <С‚РµРјР°>

  РџСЂРµРґР»Р°РіР°СЋ РїРѕСЃС‚Р°РІРёС‚СЊ Р·Р°РґР°С‡Рё РІ Р‘РёС‚СЂРёРєСЃ:
  1. <Р¤РРћ> вЂ” <task_text>. РЎСЂРѕРє: <deadline_text>. РљСЂРёС‚РµСЂРёР№: <result_criteria>.
  2. вЂ¦

  РЎРѕР·РґР°С‘Рј Р·Р°РґР°С‡Рё РІ Р‘РёС‚СЂРёРєСЃ? РћС‚РІРµС‚СЊ В«СЃС‚Р°РІСЊВ» вЂ” СЏ РїРѕ РєР°Р¶РґРѕРјСѓ РѕС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРјСѓ СЃРѕР·РґР°Рј РѕРґРЅСѓ Р°РіСЂРµРіРёСЂРѕРІР°РЅРЅСѓСЋ Р·Р°РґР°С‡Сѓ В«РС‚РѕРіРё СЃРѕР·РІРѕРЅР° <Р§Р§:РњРњ>В» СЃ РґРµРґР»Р°Р№РЅРѕРј <РґР°С‚Р° СЃРѕР·РІРѕРЅР°> 19:00 РњРЎРљ Рё РѕРїРёСЃР°РЅРёРµРј СЃРѕ СЃРїРёСЃРєРѕРј РІСЃРµС… РµРіРѕ Р·Р°РґР°С‡ РёР· СЃРѕР·РІРѕРЅР° (С„РѕСЂРјР°С‚ РєР°Рє РІ Albery UI). В«РќРµ СЃС‚Р°РІСЊВ» вЂ” РїСЂРѕРїСѓСЃРєР°СЋ. В«РџСЂР°РІРєРё РїРѕ в„–<n>: <С‚РµРєСЃС‚>В» вЂ” РїРµСЂРµСЃРѕР±РµСЂСѓ РєРѕРЅРєСЂРµС‚РЅСѓСЋ.
  ```
  Р•СЃР»Рё Р·Р°РґР°С‡ 0 вЂ” СЃС‚СЂРѕРєР° В«Р—Р°РґР°С‡ РЅРµ РІС‹РґРµР»РµРЅРѕ.В» Рё С„РёРЅР°Р»СЊРЅС‹Р№ РІРѕРїСЂРѕСЃ РЅРµ Р·Р°РґР°С‘С‚СЃСЏ. Р•СЃР»Рё РѕР±СЂР°Р±РѕС‚Р°РЅРѕ РЅРµСЃРєРѕР»СЊРєРѕ СЃРѕР·РІРѕРЅРѕРІ вЂ” РєР°Р¶РґС‹Р№ РѕС‚РґРµР»СЊРЅС‹Рј Р±Р»РѕРєРѕРј С‡РµСЂРµР· СЂР°Р·РґРµР»РёС‚РµР»СЊ В«вЂ”вЂ”вЂ”В».

  РџРѕР»РЅС‹Р№ РѕС‚С‡С‘С‚ РїРѕ РєРѕРЅС‚СЂР°РєС‚Сѓ (РєСЂР°С‚РєР°СЏ СЃСѓС‚СЊ, СЂРёСЃРєРё, РїРѕРІРµРґРµРЅС‡РµСЃРєРёРµ С„Р°РєС‚РѕСЂС‹, РґРёР°РіРЅРѕСЃС‚РёРєР° Рё С‚.Рґ.) Р¶РёРІС‘С‚ **С‚РѕР»СЊРєРѕ РІ Р‘Р”** (`analytical_note` + `raw_json.ai_report.analysis`) Рё РґРѕСЃС‚СѓРїРµРЅ С‡РµСЂРµР· UI Albery / MCP `get_zoom_call_transcript`. Р’ Telegram РѕРЅ РЅРµ РґСѓР±Р»РёСЂСѓРµС‚СЃСЏ.

  **РќР° РѕС‚РІРµС‚ В«СЃС‚Р°РІСЊВ» (Phase 2 вЂ” РѕС‚РїСЂР°РІРєР° РІ Р‘РёС‚СЂРёРєСЃ).** Hermes РІ Telegram-СЃРµСЃСЃРёРё **РќР• СЃРѕР·РґР°С‘С‚ РїРѕ РѕРґРЅРѕР№ РјРµР»РєРѕР№ Р·Р°РґР°С‡Рµ С‡РµСЂРµР· `create_bitrix_task`** вЂ” РѕРЅ РёСЃРїРѕР»СЊР·СѓРµС‚ existing UI dispatcher (С‚РѕС‚ Р¶Рµ РєРѕРґ, С‡С‚Рѕ Рё РєРЅРѕРїРєР° В«РћС‚РїСЂР°РІРєР° Р·Р°РґР°С‡В» РІ Albery UI):
  1. `list_pending_zoom_operational_dispatches()` Р±РµР· Р°СЂРіСѓРјРµРЅС‚РѕРІ вЂ” РІРѕР·РІСЂР°С‰Р°РµС‚ РјР°СЃСЃРёРІ `pending` РўРћР›Р¬РљРћ Р·Р° СЃРµРіРѕРґРЅСЏ (Europe/Moscow). Р­С‚Рѕ РёРјРµРЅРЅРѕ С‚Рµ СЃРѕР·РІРѕРЅС‹, РєРѕС‚РѕСЂС‹Рµ РІР»Р°РґРµР»РµС† РІРёРґРµР» РІ РЅРµРґР°РІРЅРµР№ СЃРІРѕРґРєРµ.
  2. Р”Р»СЏ РєР°Р¶РґРѕРіРѕ `pending` в†’ `dispatch_zoom_operational_tasks(call_id, confirm=true)`. Р­С‚РѕС‚ РёРЅСЃС‚СЂСѓРјРµРЅС‚ СЃР°Рј СЃРіСЂСѓРїРїРёСЂСѓРµС‚ `operational_tasks` РїРѕ РѕС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРјСѓ, СЃРѕР·РґР°СЃС‚ **РѕРґРЅСѓ Р°РіСЂРµРіРёСЂРѕРІР°РЅРЅСѓСЋ Bitrix-Р·Р°РґР°С‡Сѓ** В«РС‚РѕРіРё СЃРѕР·РІРѕРЅР° Р§Р§:РњРњВ» РЅР° РєР°Р¶РґРѕРіРѕ С‡РµР»РѕРІРµРєР° СЃ РѕРїРёСЃР°РЅРёРµРј С‡РµСЂРµР· СЃС‚Р°РЅРґР°СЂС‚РЅС‹Р№ intro `РћР·РЅР°РєРѕРјСЊС‚РµСЃСЊ СЃРѕ СЃРїРёСЃРєРѕРј РІС‹РґРµР»РµРЅРЅС‹С… РёР· СЃРѕР·РІРѕРЅР° Р·Р°РґР°С‡ Рё РїРѕСЃС‚Р°РІСЊС‚Рµ СЃРµР±Рµ СЃР°РјС‹Рµ РІР°Р¶РЅС‹Рµ РІ Р‘РёС‚СЂРёРєСЃвЂ¦` + РЅСѓРјРµСЂРѕРІР°РЅРЅС‹Р№ СЃРїРёСЃРѕРє СЌС‚РѕРіРѕ С‡РµР»РѕРІРµРєР°.
  3. РџРѕСЃР»Рµ СѓСЃРїРµС€РЅРѕР№ РѕС‚РїСЂР°РІРєРё Р±СЌРєРµРЅРґ РїРѕРјРµС‡Р°РµС‚ `zoom_calls.raw_json.ai_report.bitrix_dispatch` (timestamp + task_ids) в†’ СЃР»РµРґСѓСЋС‰РёР№ `list_pending` РґР»СЏ С‚РѕРіРѕ Р¶Рµ РґРЅСЏ СѓР¶Рµ РЅРµ РІРµСЂРЅС‘С‚ СЌС‚РѕС‚ СЃРѕР·РІРѕРЅ.
  4. Hermes РѕС‚РІРµС‡Р°РµС‚ РІР»Р°РґРµР»СЊС†Сѓ РєРѕСЂРѕС‚РєРѕР№ С‡РµР»РѕРІРµС‡РµСЃРєРѕР№ СЃРІРѕРґРєРѕР№ (В«РЎРѕР·РґР°РЅРѕ M Р·Р°РґР°С‡ РІ Р‘РёС‚СЂРёРєСЃ РїРѕ СЃРѕР·РІРѕРЅСѓ <С‚РµРјР°>: вЂ” Р¤РРћ (N Р·Р°РґР°С‡)В»), Р±РµР· С‚РµС…РЅ id, MCP, РїСЂРѕС‡РµР№ РєСѓС…РЅРё.

  РџСЂР°РІРёР»Рѕ РїРѕРІРµРґРµРЅРёСЏ РЅР° В«СЃС‚Р°РІСЊВ» Р·Р°С„РёРєСЃРёСЂРѕРІР°РЅРѕ РѕС‚РґРµР»СЊРЅРѕР№ AI-РёРЅСЃС‚СЂСѓРєС†РёРµР№ РІ Albery (В«Cron Р°РІС‚РѕРјР°С‚РёР·Р°С†РёРё/Zoom Р·Р°РґР°С‡Рё вЂ” РѕС‚РІРµС‚ СЃС‚Р°РІСЊВ», РёСЃС‚РѕС‡РЅРёРє РІ git: [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md)). Hermes С‡РёС‚Р°РµС‚ РµС‘ С‡РµСЂРµР· `start_here_always_read_ai_instructions` РІ РЅР°С‡Р°Р»Рµ Telegram-СЃРµСЃСЃРёРё. Р”РµРїР»РѕР№ РёРЅСЃС‚СЂСѓРєС†РёРё вЂ” `python scripts/upsert_albery_ai_instruction.py "<path>" scripts/ai_instruction_zoom_approval.md`.

  Р–С‘СЃС‚РєРёРµ РїСЂР°РІРёР»Р° РІ СЌС‚РѕР№ AI-РёРЅСЃС‚СЂСѓРєС†РёРё (РІР°Р¶РЅС‹ С‡С‚РѕР±С‹ Hermes РЅРµ СЃР¶РёРіР°Р» С‚РѕРєРµРЅС‹ Рё РЅРµ РґРµР»Р°Р» Р»РёС€РЅРµРіРѕ):
  - РќР• РїРµСЂРµСЃРїСЂР°С€РёРІР°Р№ В«3 РѕР±СЏР·Р°С‚РµР»СЊРЅС‹С… РїРѕР»СЏВ» вЂ” Сѓ `dispatch_zoom_operational_tasks` РІСЃРµ РїРѕР»СЏ СЃРѕР±РёСЂР°СЋС‚СЃСЏ РёР· Р‘Р” Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё.
  - РќР• РІС‹Р·С‹РІР°Р№ `create_bitrix_task` РґР»СЏ РѕС‚РґРµР»СЊРЅС‹С… Р·Р°РґР°С‡ вЂ” СЌС‚Рѕ СЃРѕР·РґР°С‘С‚ РјРЅРѕРіРѕ РјРµР»РєРёС… Р·Р°РґР°С‡ РІРјРµСЃС‚Рѕ РѕРґРЅРѕР№ Р°РіСЂРµРіРёСЂРѕРІР°РЅРЅРѕР№.
  - РќР• РёС‰Рё `call_id` РІСЂСѓС‡РЅСѓСЋ С‡РµСЂРµР· `list_zoom_calls`/`get_zoom_call_transcript` вЂ” `list_pending_zoom_operational_dispatches` СѓР¶Рµ РѕС‚С„РёР»СЊС‚СЂРѕРІР°Р» РЅСѓР¶РЅРѕРµ.
  - РќР• С‡РёС‚Р°Р№ `get_org_structure`, `get_zoom_call_transcript`, `get_report_contract` вЂ” dispatch СЃР°Рј РІСЃС‘ РїРѕРґС‚СЏРЅРµС‚ РёР· Р‘Р”.
  - РќР° В«РЅРµ СЃС‚Р°РІСЊВ» вЂ” РЅРёС‡РµРіРѕ РЅРµ СЃРѕР·РґР°РІР°Р№, РѕС‚РІРµС‡Р°Р№ В«РџРѕРЅСЏР», Р·Р°РґР°С‡Рё РЅРµ СЃС‚Р°РІР»СЋ.В».
  - РќР° В«РїСЂР°РІРєРё РїРѕ в„–N: вЂ¦В» вЂ” `dispatch_zoom_operational_tasks` РЅРµ РІС‹Р·С‹РІР°Р№; СЂРµР¶РёРј СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РѕС‚РґРµР»СЊРЅРѕР№ Р·Р°РґР°С‡Рё РїРѕРєР° РЅРµ Р°РІС‚РѕРјР°С‚РёР·РёСЂРѕРІР°РЅ, РѕР±СЃСѓРґРё СЃ РІР»Р°РґРµР»СЊС†РµРј СѓСЃС‚РЅРѕ.

  **Р”РµРїР»РѕР№ РѕР±РЅРѕРІР»С‘РЅРЅРѕРіРѕ РїСЂРѕРјРїС‚Р°/watchdog'Р°**:
  ```powershell
  python scripts/update_hermes_zoom_to_tasks.py
  # РћРїС†РёРё:
  #   --reset-and-run <zoom_call_uuid>
  #     РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ: СѓРґР°Р»РёС‚ СЃРѕС…СЂР°РЅС‘РЅРЅС‹Р№ РѕС‚С‡С‘С‚ Р·Р° СЌС‚РѕС‚ СЃРѕР·РІРѕРЅ С‡РµСЂРµР· MCP
  #     delete_zoom_call_report, СЃР±СЂРѕСЃРёС‚ cooldown, Рё Р·Р°РїСѓСЃС‚РёС‚ watchdog РѕРґРёРЅ СЂР°Р·
  #     С‡РµСЂРµР· bash (РґР»СЏ СЂР°Р·СЂР°Р±РѕС‚РєРё; РІ РїСЂРѕРґРµ РёСЃРїРѕР»СЊР·СѓР№С‚Рµ `hermes cron run f217482a8618`
  #     РµСЃР»Рё РЅСѓР¶РЅР° СЂРµР°Р»СЊРЅР°СЏ cron-delivery РІ Telegram).
  ```
  РСЃС‚РѕС‡РЅРёРєРё РїСЂР°РІРґС‹ РІ git:
  - [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt) вЂ” С‚РµРєСЃС‚ РїСЂРѕРјРїС‚Р° (РЅР° РїСЂРѕРґРµ: `/root/.hermes/scripts/hermes_zoom_to_tasks_prompt.txt`);
  - [scripts/hermes_zoom_watchdog.sh](scripts/hermes_zoom_watchdog.sh) вЂ” wrapper (РЅР° РїСЂРѕРґРµ: `/root/.hermes/scripts/zoom_watchdog.sh`, РїСЂР°РІР° 0700);
  - [scripts/update_hermes_zoom_to_tasks.py](scripts/update_hermes_zoom_to_tasks.py) вЂ” РїР°С‚С‡РµСЂ.
  - [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md) вЂ” AI-РёРЅСЃС‚СЂСѓРєС†РёСЏ Albery РґР»СЏ Telegram-СЃРµСЃСЃРёРё.
  - [scripts/upsert_albery_ai_instruction.py](scripts/upsert_albery_ai_instruction.py) вЂ” РѕР±С‰РёР№ РїР°С‚С‡РµСЂ AI-РёРЅСЃС‚СЂСѓРєС†РёР№ С‡РµСЂРµР· MCP `upsert_ai_instruction`.
  Р‘СЌРєР°Рї РїСЂРµРґС‹РґСѓС‰РµРіРѕ watchdog'a: `/root/.hermes/scripts/zoom_watchdog.sh.bak`.
- `owner-daily` вЂ” `0 18 * * *`: С„РѕСЂРјРёСЂСѓРµС‚ Рё СЃРѕС…СЂР°РЅСЏРµС‚ РµР¶РµРґРЅРµРІРЅС‹Р№ РѕС‚С‡С‘С‚ СЃРѕР±СЃС‚РІРµРЅРЅРёРєСѓ
  РїРѕ РєРѕРЅС‚СЂР°РєС‚Сѓ `get_report_contract(owner_daily)`. **РќР° СѓСЂРѕРІРЅРµ prompt СЃР°РјРѕРіРѕ Hermes**
  (РЅРµ MCP-РёРЅСЃС‚СЂСѓРєС†РёР№ вЂ” РєРѕРЅС‚СЂР°РєС‚ `owner_daily` РќР• С‚СЂРѕРіР°Р»Рё) РІРєР»СЋС‡С‘РЅ РґРІСѓС…С„Р°Р·РЅС‹Р№
  СЂРµР¶РёРј СЃРѕРіР»Р°СЃРѕРІР°РЅРёСЏ СЂРµРєРѕРјРµРЅРґР°С†РёР№ в†’ РѕС‚РїСЂР°РІРєР° РІ Р‘РёС‚СЂРёРєСЃ.

  **Р¤Р°Р·Р° 1 вЂ” С„РѕСЂРјРёСЂРѕРІР°РЅРёРµ (cron РІ 18:00 РњРЎРљ).** Hermes:
  1. С‡РёС‚Р°РµС‚ Р¶РёРІС‹Рµ AI-РёРЅСЃС‚СЂСѓРєС†РёРё, РєРѕРЅС‚СЂР°РєС‚ `owner_daily`, РёСЃС‚РѕС‡РЅРёРєРё Р·Р° РґРµРЅСЊ (С‡Р°С‚С‹ СЃ OCR, Zoom-РѕС‚С‡С‘С‚С‹, Bitrix-Р·Р°РґР°С‡Рё, РѕСЂРіСЃС‚СЂСѓРєС‚СѓСЂСѓ, СЂРµРіР»Р°РјРµРЅС‚С‹, РїСЂРµРґС‹РґСѓС‰РёР№ owner-РѕС‚С‡С‘С‚);
  2. РІС‹Р·С‹РІР°РµС‚ `save_owner_daily_report` Рё **РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ РїРµСЂРµРґР°С‘С‚** Р°СЂРіСѓРјРµРЅС‚ `manager_messages` вЂ” РјР°СЃСЃРёРІ Р°РґСЂРµСЃРЅС‹С… СЃРѕРѕР±С‰РµРЅРёР№ РўРћР›Р¬РљРћ РґР»СЏ РїСЏС‚С‘СЂРєРё (РЎРµСЂРіРµР№ Р’РёРЅРѕРіСЂР°РґРѕРІ, РќР°С‚Р°Р»СЊСЏ Р“РѕСЂСЋРЅРѕРІР°, РђСЂС‚СѓСЂ РЎС‚РµРїР°РЅСЏРЅ, Р•РІРіРµРЅРёР№ РџР°Р»РµР№, РђР»РµРєСЃР°РЅРґСЂ РќРёРєРёС‚РµРЅРєРѕ). Р’ РєР°Р¶РґРѕРј `message_text` СѓР¶Рµ Р»РµР¶РёС‚ РџРћР›РќР«Р™ С„РёРЅР°Р»СЊРЅС‹Р№ С‚РµРєСЃС‚ РІ С„РѕСЂРјР°С‚Рµ В«<РРјСЏ>, РїСЂРёРІРµС‚СЃС‚РІСѓСЋ! Р РµРєРѕРјРµРЅРґР°С†РёРё: 1) вЂ¦ 2) вЂ¦В», РєРѕС‚РѕСЂС‹Р№ РїРѕР№РґС‘С‚ РІ Р‘РёС‚СЂРёРєСЃ РѕРґРЅРѕР№ СЂРµРїР»РёРєРѕР№;
  3. РґР»СЏ Р•РІРіРµРЅРёСЏ РџР°Р»РµСЏ (СЃРѕР±СЃС‚РІРµРЅРЅРёРє) РІ РЅР°С‡Р°Р»Рѕ `message_text` РґРѕР±Р°РІР»СЏРµС‚СЃСЏ Р±Р»РѕРє В«Р“Р»Р°РІРЅС‹Р№ РІС‹РІРѕРґ РґРЅСЏ вЂ” <2-3 СЃС‚СЂРѕРєРё executive summary>В»;
  4. РЅР° СЃС‚РѕСЂРѕРЅРµ MCP `tool_save_owner_daily_report` РїРѕСЃР»Рµ INSERT РІ `owner_daily_reports` РІС‹Р·С‹РІР°РµС‚ `save_owner_daily_manager_messages` (РІ `app.py`), РєРѕС‚РѕСЂС‹Р№ РїР°СЂСЃРёС‚ `manager_messages` Рё РїРёС€РµС‚ РєР°Р¶РґРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ СЃС‚СЂРѕРєРѕР№ РІ `owner_manager_recommendations` СЃРѕ `status='new'`;
  5. РґР»СЏ **РќР•-СЂР°Р·СЂРµС€С‘РЅРЅС‹С…** СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ СЂРµРєРѕРјРµРЅРґР°С†РёРё РІ `manager_messages` РќР• РїРµСЂРµРґР°СЋС‚СЃСЏ РІРѕРѕР±С‰Рµ вЂ” РЅР°Р±Р»СЋРґРµРЅРёСЏ РїРѕ РЅРёРј РѕСЃС‚Р°СЋС‚СЃСЏ С‚РѕР»СЊРєРѕ РІ `report_text/recommendations` РѕС‚С‡С‘С‚Р°;
  6. **РµСЃР»Рё РґР»СЏ РїСЏС‚С‘СЂРєРё Р·Р° РґРµРЅСЊ РЅРµС‚ С„Р°РєС‚РѕРІ-РѕСЃРЅРѕРІР°РЅРёР№** (РЅРµС‚ СЃРѕР·РІРѕРЅРѕРІ/С‡Р°С‚РѕРІ/РѕС‚РІРµС‚РѕРІ/РїСЂРѕСЃСЂРѕС‡РµРє) вЂ” `manager_messages` РїСѓСЃС‚РѕР№, РІ Р‘Р” РЅРёС‡РµРіРѕ РЅРµ Р·Р°РїРёСЃС‹РІР°РµС‚СЃСЏ, Рё Hermes РІРѕР·РІСЂР°С‰Р°РµС‚ **РїСѓСЃС‚РѕР№ stdout** в†’ Telegram РјРѕР»С‡РёС‚ РІРѕРѕР±С‰Рµ (РїСЂР°РІРёР»Рѕ С‚РёС€РёРЅС‹, РєР°Рє Сѓ `zoom-to-tasks` РїСЂРё РѕС‚СЃСѓС‚СЃС‚РІРёРё РЅРѕРІС‹С… СЃРѕР·РІРѕРЅРѕРІ);
  7. РµСЃР»Рё С…РѕС‚СЊ РѕРґРёРЅ Р±Р»РѕРє РµСЃС‚СЊ вЂ” Hermes СЃРѕР±РёСЂР°РµС‚ РµРґРёРЅРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ Рё РїСЂРёСЃС‹Р»Р°РµС‚ РјРЅРµ РІ Telegram:
     ```
     РЎРѕРіР»Р°СЃСѓР№С‚Рµ С‡С‚Рѕ РјС‹ РѕС‚РїСЂР°РІР»СЏРµРј:

     Р•РІРіРµРЅРёР№, РїСЂРёРІРµС‚СЃС‚РІСѓСЋ!
     Р“Р»Р°РІРЅС‹Р№ РІС‹РІРѕРґ РґРЅСЏ вЂ” вЂ¦
     Р РµРєРѕРјРµРЅРґР°С†РёРё: 1) вЂ¦ 2) вЂ¦

     вЂ”вЂ”вЂ”

     РЎРµСЂРіРµР№, РїСЂРёРІРµС‚СЃС‚РІСѓСЋ!
     Р РµРєРѕРјРµРЅРґР°С†РёРё: 1) вЂ¦

     РћС‚РїСЂР°РІР»СЏСЋ РІ Р‘РёС‚СЂРёРєСЃ? РћС‚РІРµС‚СЊ: РѕС‚РїСЂР°РІР»СЏР№ / РЅРµ РѕС‚РїСЂР°РІР»СЏР№ / РїСЂР°РІРєРё РїРѕ <РёРјСЏ>: <С‚РµРєСЃС‚>.
     ```

  **Р¤Р°Р·Р° 2 вЂ” РѕС‚РїСЂР°РІРєР° РІ Р‘РёС‚СЂРёРєСЃ (РѕС‚РІРµС‚ РІР»Р°РґРµР»СЊС†Р° РІ Telegram).** РќР° В«РѕС‚РїСЂР°РІР»СЏР№В»
  Hermes РІ РЅРѕРІРѕР№ Telegram-СЃРµСЃСЃРёРё:
  1. `list_pending_owner_recommendations(report_date=today)` вЂ” С‡РёС‚Р°РµС‚ СЃРѕС…СЂР°РЅС‘РЅРЅС‹Рµ С‡РµСЂРЅРѕРІРёРєРё РёР· `owner_manager_recommendations` (СЃС‚Р°С‚СѓСЃ `new`);
  2. СЃРѕР±РёСЂР°РµС‚ `recipient_recommendations = {manager_bitrix_user_id: recommendation_text}` СЃС‚СЂРѕРіРѕ РєР°Рє РµСЃС‚СЊ (С‚РµРєСЃС‚С‹ СѓР¶Рµ С„РёРЅР°Р»СЊРЅС‹Рµ Рё РѕРґРѕР±СЂРµРЅРЅС‹Рµ);
  3. `send_owner_recommendations_to_bitrix(report_date, recipient_recommendations, confirm=true)` в†’ backend (`send_owner_report_recommendations_to_bitrix` РІ `app.py`) С€Р»С‘С‚ РєР°Р¶РґРѕРјСѓ С‡РµСЂРµР· **`im.message.add` РѕС‚ РјРѕРµРіРѕ РёРјРµРЅРё** (С‡РµСЂРµР· СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ `BITRIX_WEBHOOK_BASE`, РѕС‚РґРµР»СЊРЅРѕРіРѕ Р±РѕС‚Р° РїРѕРєР° РЅРµ РґРµР»Р°РµРј) СЃ fallback РЅР° `im.notify.personal.add` РїСЂРё `ERROR_NO_ACCESS`;
  4. С„Р°РєС‚ РѕС‚РїСЂР°РІРєРё РїРёС€РµС‚СЃСЏ РІ `owner_recommendation_dispatches` (channel `bitrix_im` РёР»Рё `bitrix_notification`), СЃС‚Р°С‚СѓСЃ СЃРѕРѕС‚РІРµС‚СЃС‚РІСѓСЋС‰РёС… `owner_manager_recommendations` РѕР±РЅРѕРІР»СЏРµС‚СЃСЏ РЅР° `sent`, РІ `owner_recommendation_events` С„РёРєСЃРёСЂСѓРµС‚СЃСЏ СЃРѕР±С‹С‚РёРµ `sent`;
  5. РЅР° В«РїСЂР°РІРєРё РїРѕ <РёРјСЏ>: вЂ¦В» вЂ” Hermes РїРµСЂРµСЃРѕР±РёСЂР°РµС‚ С‚РµРєСЃС‚ РґР»СЏ СЌС‚РѕРіРѕ С‡РµР»РѕРІРµРєР° Рё СЃРЅРѕРІР° РїРѕРєР°Р·С‹РІР°РµС‚ РЅР° СЃРѕРіР»Р°СЃРѕРІР°РЅРёРµ (СЃС‚Р°СЂС‹Р№ С‡РµСЂРЅРѕРІРёРє РјРѕР¶РЅРѕ РїРѕРјРµС‚РёС‚СЊ `cancel_owner_recommendation(recommendation_id, reason)`);
  6. РЅР° В«РЅРµ РѕС‚РїСЂР°РІР»СЏР№В» вЂ” РѕС‚РјРµС‚РєР° СЃС‚Р°С‚СѓСЃРѕРІ `cancelled`, РЅРёС‡РµРіРѕ РІ Р‘РёС‚СЂРёРєСЃ РЅРµ СѓС…РѕРґРёС‚.

  РЎС†РµРЅР°СЂРёР№ РїРѕР»РЅРѕСЃС‚СЊСЋ Р°РІС‚РѕРјР°С‚РёР·РёСЂРѕРІР°РЅРЅС‹Р№ вЂ” РѕС‚РґРµР»СЊРЅРѕРіРѕ В«РђР»СЊР±РµСЂРё Р‘РѕС‚Р°В» РІ Bitrix РїРѕРєР° РЅРµС‚, СЃРѕРѕР±С‰РµРЅРёСЏ РёРґСѓС‚ РѕС‚ РјРѕРµРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ С‡РµСЂРµР· С‚РѕС‚ Р¶Рµ webhook, С‡С‚Рѕ Рё `create_bitrix_task`. РљРѕРіРґР° РґРѕР±Р°РІРёРј РѕС‚РґРµР»СЊРЅРѕРіРѕ Р±РѕС‚Р° (Phase 2), РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ Р±СѓРґРµС‚ РїРµСЂРµРєР»СЋС‡РёС‚СЊ `send_owner_report_recommendations_to_bitrix` РЅР° РЅРѕРІС‹Р№ webhook.

### Bitrix-РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹ РІ MCP

Р’ MCP Albery РґРѕСЃС‚СѓРїРЅС‹ РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹:

- `create_bitrix_task` вЂ” СЃРѕР·РґР°С‘С‚ РѕРґРЅСѓ Р·Р°РґР°С‡Сѓ РІ Bitrix (СЂР°Р·РѕРІСѓСЋ РёР»Рё РїРµСЂРёРѕРґРёС‡РµСЃРєСѓСЋ,
  СЃ РЅР°Р±Р»СЋРґР°С‚РµР»СЏРјРё РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ). РђРіРµРЅС‚ РѕР±СЏР·Р°РЅ СЃРѕР±СЂР°С‚СЊ Рё РїРѕРєР°Р·Р°С‚СЊ С‡РµР»РѕРІРµРєСѓ РїРµСЂРµРґ
  СЃРѕР·РґР°РЅРёРµРј: РѕС‚РІРµС‚СЃС‚РІРµРЅРЅС‹Р№, РґРµРґР»Р°Р№РЅ, РїСЂРѕРІРµСЂСЏРµРјС‹Р№ СЂРµР·СѓР»СЊС‚Р°С‚, С„РёРЅР°Р»СЊРЅС‹Р№ С‡РµР»РѕРІРµС‡РµСЃРєРёР№
  С‚РµРєСЃС‚ Р·Р°РґР°С‡Рё, РїРѕР»РЅС‹Р№ СЃРїРёСЃРѕРє РЅР°Р±Р»СЋРґР°С‚РµР»РµР№ (РµСЃР»Рё РµСЃС‚СЊ), Рё СЂР°СЃРїРёСЃР°РЅРёРµ (РµСЃР»Рё
  РїРµСЂРёРѕРґРёС‡РµСЃРєР°СЏ). Р•СЃР»Рё С‡РµРіРѕ-С‚Рѕ РЅРµС‚ вЂ” СѓС‚РѕС‡РЅСЏС‚СЊ РґРѕ РєРѕРЅС†Р°, РЅРµ СЃРѕР·РґР°РІР°С‚СЊ. **Р Р°СЃС€РёСЂРµРЅ
  28.05.2026** вЂ” С‚СЂРё РЅРѕРІС‹С… РїР°СЂР°РјРµС‚СЂР°:
  - `auditor_names: list[str]` / `auditor_bitrix_user_ids: list[int]` вЂ” РЅР°Р±Р»СЋРґР°С‚РµР»Рё
    РёР· Р°РєС‚РёРІРЅРѕР№ РѕСЂРіСЃС‚СЂСѓРєС‚СѓСЂС‹ (`users.is_active=TRUE`). Р РµР·РѕР»РІРёРЅРі С‡РµСЂРµР· РЅРѕРІС‹Р№ С…РµР»РїРµСЂ
    `_resolve_active_bitrix_users` ([mcp/context_server.py](mcp/context_server.py)):
    fuzzy-match РїРѕ `_person_names_match`, РЅРµРѕРґРЅРѕР·РЅР°С‡РЅРѕСЃС‚СЊ в†’ РѕС‚РєР°Р· + СЃРїРёСЃРѕРє РєР°РЅРґРёРґР°С‚РѕРІ
    СЃ `bitrix_user_id`/`full_name`/`work_position`. РЎРїРёСЃРєРё РѕР±СЉРµРґРёРЅСЏСЋС‚СЃСЏ Рё
    РґРµРґСѓРїР»РёС†РёСЂСѓСЋС‚СЃСЏ. РќР° Bitrix СѓС…РѕРґРёС‚ РєР°Рє `fields.AUDITORS = [int]`.
  - `periodic: {type, interval?, weekdays?, day_of_month?, daily_mode?, until?}` вЂ”
    СЂР°СЃРїРёСЃР°РЅРёРµ. Р•СЃР»Рё РїСЂРёСЃСѓС‚СЃС‚РІСѓРµС‚, Р·Р°РґР°С‡Р° СЃРѕР·РґР°С‘С‚СЃСЏ РєР°Рє `IS_REGULAR=Y` +
    `REGULAR_PARAMETERS` (С‡РµСЂРµР· `_build_bitrix_regular_parameters`). РџРѕРґРґРµСЂР¶РєР°:
    - `type="daily"` + `daily_mode="all"|"workdays"` (default `all`) в†’ `REPEAT_TYPE=daily`, `DAILY_MODE`;
    - `type="weekly"` + `weekdays=["MO","WE","FR"]` + `interval` в†’ `REPEAT_TYPE=weekly`, `REPEAT_WEEKDAYS`, `REPEAT_EVERY`;
    - `type="monthly"` + `day_of_month=1-31` + `interval` в†’ `REPEAT_TYPE=monthlydays`, `REPEAT_MONTHDAY`, `REPEAT_EVERY`;
    - РѕРїС†РёРѕРЅР°Р»СЊРЅС‹Р№ `until="YYYY-MM-DD"` в†’ `REPEAT_TILL`.
    РќРµРІР°Р»РёРґРЅС‹Рµ РєРѕРјР±РёРЅР°С†РёРё (РЅРµС‚ `type`, weekly Р±РµР· `weekdays`, monthly Р±РµР·
    `day_of_month`, РєСЂРёРІРѕР№ weekday-РєРѕРґ, `interval<1`, РєСЂРёРІРѕР№ `until`) в†’ РёРЅСЃС‚СЂСѓРјРµРЅС‚
    РѕС‚РєР°Р·С‹РІР°РµС‚ СЃ РїРѕРЅСЏС‚РЅС‹Рј СЃРѕРѕР±С‰РµРЅРёРµРј.
  Schema-РІР°Р»РёРґР°С†РёСЏ РІ `inputSchema` РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ РѕРіСЂР°РЅРёС‡РёРІР°РµС‚ enum'С‹. MCP server
  version РїРѕРґРЅСЏС‚ РґРѕ `0.6.0`.
- `delete_bitrix_task` вЂ” СѓРґР°Р»СЏРµС‚ РѕРґРЅСѓ Р·Р°РґР°С‡Сѓ РІ Bitrix. Р–С‘СЃС‚РєРѕРµ РїСЂР°РІРёР»Рѕ:
  СЃРЅР°С‡Р°Р»Р° `search_tasks(bitrix_task_id=...)`, Р·Р°С‚РµРј РїРѕРєР°Р·Р°С‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ С‚РѕС‡РЅСѓСЋ
  Р·Р°РґР°С‡Сѓ (РЅРѕРјРµСЂ, РЅР°Р·РІР°РЅРёРµ, СЃС‚Р°С‚СѓСЃ, РѕС‚РІРµС‚СЃС‚РІРµРЅРЅС‹Р№, РґРµРґР»Р°Р№РЅ) Рё СЃРїСЂРѕСЃРёС‚СЊ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёРµ.
  РўРѕР»СЊРєРѕ РїРѕСЃР»Рµ СЏРІРЅРѕРіРѕ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ РјРѕР¶РЅРѕ РІС‹Р·РІР°С‚СЊ
  `delete_bitrix_task(bitrix_task_id=..., confirm=true)`. РќРµР»СЊР·СЏ СѓРґР°Р»СЏС‚СЊ РїРѕ РЅР°Р·РІР°РЅРёСЋ,
  РїРѕРёСЃРєРѕРІРѕРјСѓ С‚РµРєСЃС‚Сѓ РёР»Рё РЅРµРѕРґРЅРѕР·РЅР°С‡РЅРѕР№ СЃСЃС‹Р»РєРµ. Р’ РёРЅСЃС‚СЂСѓРјРµРЅС‚Рµ РµСЃС‚СЊ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅР°СЏ
  Р·Р°С‰РёС‚Р°: Р±РµР· `confirm=true` РѕРЅ РѕС‚РєР°Р¶РµС‚, Р° `expected_title` РјРѕР¶РЅРѕ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ РєР°Рє
  safety-check РѕС‚ СѓРґР°Р»РµРЅРёСЏ РЅРµ С‚РѕР№ Р·Р°РґР°С‡Рё.
- `list_pending_owner_recommendations(report_date)` вЂ” РІРѕР·РІСЂР°С‰Р°РµС‚ СЃРѕС…СЂР°РЅС‘РЅРЅС‹Рµ
  С‡РµСЂРЅРѕРІРёРєРё СЂРµРєРѕРјРµРЅРґР°С†РёР№ РёР· `owner_manager_recommendations` Р·Р° СѓРєР°Р·Р°РЅРЅС‹Р№ РґРµРЅСЊ
  (С‚РѕР»СЊРєРѕ С‚РµРєСѓС‰Р°СЏ РІРµСЂСЃРёСЏ РѕС‚С‡С‘С‚Р°, С‚РѕР»СЊРєРѕ СЃС‚Р°С‚СѓСЃС‹ `new/queued`, С‚РѕР»СЊРєРѕ Р·Р°РїРёСЃРё СЃ
  `manager_bitrix_user_id IS NOT NULL`). Р’РјРµСЃС‚Рµ СЃ С‡РµСЂРЅРѕРІРёРєР°РјРё РѕС‚РґР°С‘С‚ РїРѕР»СЏ РѕС‚С‡С‘С‚Р°:
  `report_summary`, `report_dynamics_summary`, `report_risks_summary`,
  `report_text`. РСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ Hermes-Р°РіРµРЅС‚РѕРј РІ Telegram-СЃРµСЃСЃРёРё РїРѕСЃР»Рµ РѕС‚РІРµС‚Р°
  РІР»Р°РґРµР»СЊС†Р° В«РѕС‚РїСЂР°РІР»СЏР№В», С‡С‚РѕР±С‹ СЃРѕР±СЂР°С‚СЊ `recipient_recommendations` РїРѕРґ РѕС‚РїСЂР°РІРєСѓ.
- `send_owner_recommendations_to_bitrix(report_date, recipient_recommendations, confirm=true)`
  вЂ” С€Р»С‘С‚ РєР°Р¶РґРѕРјСѓ РїРѕР»СѓС‡Р°С‚РµР»СЋ РѕРґРёРЅ Р»РёС‡РЅС‹Р№ С‚РµРєСЃС‚ РІ Р‘РёС‚СЂРёРєСЃ С‡РµСЂРµР· `im.message.add`
  СЃ fallback РЅР° `im.notify.personal.add`. `confirm=true` РѕР±СЏР·Р°С‚РµР»РµРЅ вЂ” Р±РµР· РЅРµРіРѕ
  РёРЅСЃС‚СЂСѓРјРµРЅС‚ РѕС‚РєР°Р·С‹РІР°РµС‚. РџР°СЂР°РјРµС‚СЂ `recipient_recommendations` вЂ” СЌС‚Рѕ СЃР»РѕРІР°СЂСЊ
  `{bitrix_user_id: text}`; С‚РµРєСЃС‚ РѕС‚РїСЂР°РІР»СЏРµС‚СЃСЏ РєР°Рє РµСЃС‚СЊ, Р±РµР· СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ. РџРѕРґ
  РєР°РїРѕС‚РѕРј вЂ” `send_owner_report_recommendations_to_bitrix` РёР· `app.py`, РєРѕС‚РѕСЂС‹Р№
  РїРёС€РµС‚ РєР°Р¶РґСѓСЋ РѕС‚РїСЂР°РІРєСѓ РІ `owner_recommendation_dispatches` (channel `bitrix_im`
  / `bitrix_notification`), РїРµСЂРµРІРѕРґРёС‚ СЃРѕРѕС‚РІРµС‚СЃС‚РІСѓСЋС‰РёРµ `owner_manager_recommendations`
  РІ `status='sent'` Рё РїРёС€РµС‚ `sent`-СЃРѕР±С‹С‚РёРµ РІ `owner_recommendation_events`.
- `cancel_owner_recommendation(recommendation_id, reason?)` вЂ” РїРѕРјРµС‡Р°РµС‚ РѕРґРЅСѓ
  Р·Р°РїРёСЃСЊ `owner_manager_recommendations` РєР°Рє `cancelled`, С„РёРєСЃРёСЂСѓРµС‚ СЃРѕР±С‹С‚РёРµ
  `cancelled` РІ `owner_recommendation_events`. РСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РЅР° В«РЅРµ РѕС‚РїСЂР°РІР»СЏР№В»
  РёР»Рё В«РїСЂР°РІРєРё РїРѕ <РёРјСЏ>: вЂ¦В» (СЃС‚Р°СЂС‹Р№ С‡РµСЂРЅРѕРІРёРє РѕС‚РјРµРЅСЏРµС‚СЃСЏ, РЅРѕРІС‹Р№ С„РѕСЂРјРёСЂСѓРµС‚СЃСЏ).
- `save_owner_daily_report` вЂ” **СЂР°СЃС€РёСЂРµРЅ 28.05.2026**: С‚РµРїРµСЂСЊ РїСЂРёРЅРёРјР°РµС‚ РїРѕР»Рµ
  `manager_messages` (РјР°СЃСЃРёРІ РѕР±СЉРµРєС‚РѕРІ СЃРѕ СЃС‚СЂСѓРєС‚СѓСЂРѕР№
  `{manager_name, manager_bitrix_user_id, priority, message_type, subject, message_text, due, topics}`),
  Рё РїРѕСЃР»Рµ INSERT РІ `owner_daily_reports` СЃСЂР°Р·Сѓ РІС‹Р·С‹РІР°РµС‚
  `save_owner_daily_manager_messages` (РІ `app.py`) вЂ” РѕРЅ РЅР°РїРѕР»РЅСЏРµС‚
  `owner_manager_recommendations` СЃС‚СЂРѕРєРѕР№ РЅР° РєР°Р¶РґС‹Р№ РѕР±СЉРµРєС‚ РёР· `manager_messages`.
  Р‘РµР· `manager_messages` РёРЅСЃС‚СЂСѓРјРµРЅС‚ СЂР°Р±РѕС‚Р°РµС‚ РєР°Рє СЂР°РЅСЊС€Рµ (С‚РѕР»СЊРєРѕ СЃР°Рј РѕС‚С‡С‘С‚).
- `list_pending_zoom_operational_dispatches(date_from?, date_to?)` вЂ” **РґРѕР±Р°РІР»РµРЅ 28.05.2026**:
  РІРѕР·РІСЂР°С‰Р°РµС‚ Zoom-СЃРѕР·РІРѕРЅС‹ СЃ СЃРѕС…СЂР°РЅС‘РЅРЅС‹Рј `analytical_note`, РїРѕ РєРѕС‚РѕСЂС‹Рј РµС‰С‘ РЅРµ
  СЃРѕР·РґР°РЅС‹ Р°РіСЂРµРіРёСЂРѕРІР°РЅРЅС‹Рµ В«РС‚РѕРіРё СЃРѕР·РІРѕРЅР°В» Р·Р°РґР°С‡Рё РІ Р‘РёС‚СЂРёРєСЃ. **Default РїРµСЂРёРѕРґ вЂ”
  С‚РѕР»СЊРєРѕ СЃРµРіРѕРґРЅСЏ (Europe/Moscow)** вЂ” СЌС‚Рѕ СЃС‚СЂР°С…РѕРІРєР° РѕС‚ СЃР»СѓС‡Р°Р№РЅРѕР№ РѕС‚РїСЂР°РІРєРё СЃС‚Р°СЂС‹С…
  РЅРµРїРµСЂРµРґР°РЅРЅС‹С… СЃРѕР·РІРѕРЅРѕРІ РЅР° РѕС‚РІРµС‚ В«СЃС‚Р°РІСЊВ»; Р·Р° РїСЂРѕС€Р»С‹Рµ РґРЅРё РЅСѓР¶РЅРѕ РїРµСЂРµРґР°С‚СЊ
  `date_from` СЏРІРЅРѕ. Hermes РёСЃРїРѕР»СЊР·СѓРµС‚ СЌС‚Рѕ РєР°Рє РїРµСЂРІС‹Р№ С€Р°Рі Phase 2 zoom-to-tasks.
- `preview_zoom_operational_tasks(call_id)` вЂ” **РґРѕР±Р°РІР»РµРЅ 28.05.2026**: РїРѕРєР°Р·С‹РІР°РµС‚
  С‡С‚Рѕ Р±СѓРґРµС‚ СЃРѕР·РґР°РЅРѕ РІ Р‘РёС‚СЂРёРєСЃ Р‘Р•Р— РѕС‚РїСЂР°РІРєРё. Р’РѕР·РІСЂР°С‰Р°РµС‚ `title` (В«РС‚РѕРіРё СЃРѕР·РІРѕРЅР°
  Р§Р§:РњРњВ»), per-recipient `task_cards` (РѕРґРЅР° РєР°СЂС‚РѕС‡РєР° = РѕРґРЅР° Р°РіСЂРµРіРёСЂРѕРІР°РЅРЅР°СЏ
  Р·Р°РґР°С‡Р°), `deadline` (РґР°С‚Р° СЃРѕР·РІРѕРЅР° 19:00 РњРЎРљ), СЃС‚Р°РЅРґР°СЂС‚РЅРѕРµ `description`.
  РџРѕР»РµР·РµРЅ РґР»СЏ РѕС‚Р»Р°РґРєРё; РІ РѕР±С‹С‡РЅРѕРј flow Hermes СЌС‚РѕС‚ РёРЅСЃС‚СЂСѓРјРµРЅС‚ РЅРµ РґС‘СЂРіР°РµС‚ вЂ”
  РёРґС‘С‚ СЃСЂР°Р·Сѓ Рє `dispatch_zoom_operational_tasks`.
- `dispatch_zoom_operational_tasks(call_id, confirm=true)` вЂ” **РґРѕР±Р°РІР»РµРЅ
  28.05.2026**: СЃРѕР·РґР°С‘С‚ Р°РіСЂРµРіРёСЂРѕРІР°РЅРЅС‹Рµ Bitrix-Р·Р°РґР°С‡Рё В«РС‚РѕРіРё СЃРѕР·РІРѕРЅР° Р§Р§:РњРњВ» вЂ”
  РѕРґРЅР° Р·Р°РґР°С‡Р° РЅР° РєР°Р¶РґРѕРіРѕ РѕС‚РІРµС‚СЃС‚РІРµРЅРЅРѕРіРѕ РёР· `operational_tasks` СЃРѕС…СЂР°РЅС‘РЅРЅРѕРіРѕ
  РѕС‚С‡С‘С‚Р°. Р”РµРґР»Р°Р№РЅ = call_date 19:00 РњРЎРљ. РћРїРёСЃР°РЅРёРµ = `ZOOM_OPERATIONAL_TASKS_DISPATCH_INTRO` +
  СЃРїРёСЃРѕРє Р·Р°РґР°С‡ СЌС‚РѕРіРѕ С‡РµР»РѕРІРµРєР°. Р’РЅСѓС‚СЂРё РёСЃРїРѕР»СЊР·СѓРµС‚ С‚РѕС‚ Р¶Рµ
  `build_zoom_operational_task_cards` + `dispatch_prepared_zoom_operational_tasks`,
  С‡С‚Рѕ Рё Flask endpoint UI-РєРЅРѕРїРєРё В«РћС‚РїСЂР°РІРєР° Р·Р°РґР°С‡В», РїРѕСЌС‚РѕРјСѓ С„РѕСЂРјР°С‚ РёРґРµРЅС‚РёС‡РµРЅ.
  РџРѕСЃР»Рµ СѓСЃРїРµС…Р° Р·Р°РїРёСЃС‹РІР°РµС‚ `zoom_calls.raw_json.ai_report.bitrix_dispatch` (timestamp
  + СЃРѕР·РґР°РЅРЅС‹Рµ task_ids) вЂ” `list_pending_zoom_operational_dispatches` Р±РѕР»СЊС€Рµ РµРіРѕ
  РЅРµ РІРµСЂРЅС‘С‚. РўСЂРµР±СѓРµС‚ `confirm=true`. **РќР•Р›Р¬Р—РЇ Р·Р°РјРµРЅСЏС‚СЊ РЅР° СЃРµСЂРёСЋ
  `create_bitrix_task`** вЂ” СЌС‚Рѕ СЃРѕР·РґР°СЃС‚ РјРЅРѕРіРѕ РјРµР»РєРёС… Р·Р°РґР°С‡ РІРјРµСЃС‚Рѕ РѕРґРЅРѕР№ Р°РіСЂРµРіРёСЂРѕРІР°РЅРЅРѕР№.
- `send_bitrix_message(recipient_bitrix_user_id?, recipient_name?, message_text, confirm)` вЂ”
  **РґРѕР±Р°РІР»РµРЅ 28.05.2026**: РѕС‚РїСЂР°РІР»СЏРµС‚ РѕРґРЅРѕ Р»РёС‡РЅРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ РІ Bitrix Р»СЋР±РѕРјСѓ
  Р°РєС‚РёРІРЅРѕРјСѓ СЃРѕС‚СЂСѓРґРЅРёРєСѓ РѕС‚ РјРѕРµРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ (С‡РµСЂРµР· `BITRIX_WEBHOOK_BASE`,
  РѕС‚РґРµР»СЊРЅРѕРіРѕ Р±РѕС‚Р° РїРѕРєР° РЅРµС‚). РџРѕРґ РєР°РїРѕС‚РѕРј вЂ” `send_bitrix_personal_message` РІ
  [app.py](app.py): `im.message.add` СЃ fallback РЅР° `im.notify.personal.add` РїСЂРё
  `ERROR_NO_ACCESS`. РџРѕР»СѓС‡Р°С‚РµР»СЊ СЂРµР·РѕР»РІРёС‚СЃСЏ С‡РµСЂРµР· `_resolve_message_recipient` РІ
  [mcp/context_server.py](mcp/context_server.py) вЂ” РїСЂРёРѕСЂРёС‚РµС‚ Сѓ
  `recipient_bitrix_user_id` (С‚РѕС‡РЅС‹Р№ integer); РµСЃР»Рё РїРµСЂРµРґР°РЅРѕ С‚РѕР»СЊРєРѕ
  `recipient_name`, РґРµР»Р°РµС‚СЃСЏ fuzzy-match РїРѕ Р°РєС‚РёРІРЅС‹Рј `users` (С‡РµСЂРµР·
  `_person_names_match`), Рё РїСЂРё РЅРµРѕРґРЅРѕР·РЅР°С‡РЅРѕСЃС‚Рё РёРЅСЃС‚СЂСѓРјРµРЅС‚ РѕС‚РєР°Р·С‹РІР°РµС‚ Рё РІРѕР·РІСЂР°С‰Р°РµС‚
  РєР°РЅРґРёРґР°С‚РѕРІ. `confirm=true` РѕР±СЏР·Р°С‚РµР»РµРЅ вЂ” Hermes РґРѕР»Р¶РµРЅ СЃРЅР°С‡Р°Р»Р° РїРѕРєР°Р·Р°С‚СЊ РІР»Р°РґРµР»СЊС†Сѓ
  РёС‚РѕРіРѕРІС‹Р№ `message_text` + `full_name`/`work_position`/`bitrix_user_id` РїРѕР»СѓС‡Р°С‚РµР»СЏ
  Рё РїРѕР»СѓС‡РёС‚СЊ СЏРІРЅРѕРµ В«РѕС‚РїСЂР°РІР»СЏР№В». `message_text` СѓС…РѕРґРёС‚ РєР°Рє РµСЃС‚СЊ, Р±РµР· СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ
  Рё Р±РµР· РїРѕРґРїРёСЃРµР№. Р­С‚Рѕ **РѕР±С‰РёР№** РёРЅСЃС‚СЂСѓРјРµРЅС‚ РґР»СЏ СЃС†РµРЅР°СЂРёРµРІ В«РЅР°РїРёС€Рё <РёРјСЏ> РІ Р‘РёС‚СЂРёРєСЃ:
  вЂ¦В» РёР· Telegram-С‡Р°С‚Р° СЃ Hermes РёР»Рё Р»СЋР±РѕР№ РР С‡РµСЂРµР· РєРѕРЅРЅРµРєС‚РѕСЂ вЂ” РќР• РїСѓС‚Р°С‚СЊ СЃ
  `send_owner_recommendations_to_bitrix` (С‚РѕС‚ СЃС‚СЂРѕРіРѕ РїСЂРёРІСЏР·Р°РЅ Рє
  `owner_daily_reports.manager_messages` Рё СЂР°Р±РѕС‚Р°РµС‚ С‚РѕР»СЊРєРѕ РІ Phase 2 owner-daily).
  MCP server version РїРѕРґРЅСЏС‚ РґРѕ `0.5.0` (`hermes mcp test albery` РґРѕР»Р¶РµРЅ РїРѕРєР°Р·С‹РІР°С‚СЊ
  45 РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ).

РћР±Рµ cron-Р·Р°РґР°С‡Рё РґРѕСЃС‚Р°РІР»СЏСЋС‚ СЂРµР·СѓР»СЊС‚Р°С‚С‹ РІ Telegram:

```text
zoom-to-tasks -> Deliver: telegram:<TG_ID>
owner-daily   -> Deliver: telegram:<TG_ID>
```

РЈРїСЂР°РІР»РµРЅРёРµ Рё РЅР°Р±Р»СЋРґРµРЅРёРµ (РїРѕ SSH РЅР° СЃРµСЂРІРµСЂРµ):

```bash
hermes cron list                       # СЃРїРёСЃРѕРє Р°РІС‚РѕРјР°С‚РёР·Р°С†РёР№
hermes cron pause/resume/edit <id>     # РїР°СѓР·Р°/РїСЂР°РІРєР°
hermes chat                            # Р¶РёРІРѕР№ С‡Р°С‚ СЃ Р°РіРµРЅС‚РѕРј (РµСЃС‚СЊ СЂСѓРєРё Albery MCP)
hermes sessions list                   # РёСЃС‚РѕСЂРёСЏ Р·Р°РїСѓСЃРєРѕРІ
hermes logs gateway -f                 # Р»РѕРі С€Р»СЋР·Р°
journalctl -u hermes-gateway -f        # СЃРёСЃС‚РµРјРЅС‹Р№ Р»РѕРі СЃР»СѓР¶Р±С‹
systemctl status hermes-gateway        # СЃС‚Р°С‚СѓСЃ СЃР»СѓР¶Р±С‹
hermes send --to telegram:<TG_ID> "..." # С‚РµСЃС‚РѕРІС‹Р№ РїСѓС€ РІ Telegram
```

Telegram-Р±РѕС‚ РїСЂРёРЅРёРјР°РµС‚ РєРѕРјР°РЅРґС‹ С‚РѕР»СЊРєРѕ РѕС‚ `TG_ID`. РЎРЅР°СЂСѓР¶Рё Р±РѕС‚ СЂР°Р±РѕС‚Р°РµС‚ С‡РµСЂРµР·
polling, РїРѕСЌС‚РѕРјСѓ РѕС‚РґРµР»СЊРЅС‹Р№ webhook/Nginx РЅРµ РЅСѓР¶РµРЅ. Р”Р»СЏ РїСЂРѕРІРµСЂРєРё Р»РѕРіРѕРІ:
`tail -f /root/.hermes/logs/gateway.log` Рё `journalctl -u hermes-gateway -f`.
Р•СЃР»Рё РІ Telegram СЃРЅРѕРІР° РїРѕСЏРІСЏС‚СЃСЏ СЃС‚СЂРѕРєРё `вљ™пёЏ mcp_albery_...`, РІРµСЂРЅСѓС‚СЊ С‚РёС…РёР№ СЂРµР¶РёРј:

```bash
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path('/root/.hermes/config.yaml')
cfg = yaml.safe_load(p.read_text()) or {}
cfg.setdefault('display', {}).setdefault('platforms', {}).setdefault('telegram', {})['tool_progress'] = 'off'
cfg.setdefault('cron', {})['wrap_response'] = False
p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False))
PY
systemctl restart hermes-gateway
```

Р§С‚РѕР±С‹ Telegram-Р°РіРµРЅС‚ РЅРµ СЃР¶РёРіР°Р» Р»РёРјРёС‚ Codex РЅР° РЅРµСЂРµР»РµРІР°РЅС‚РЅС‹С… РёРЅСЃС‚СЂСѓРјРµРЅС‚Р°С…, РґР»СЏ
РїР»Р°С‚С„РѕСЂРјС‹ `telegram` РѕС‚РєР»СЋС‡РµРЅС‹ РІСЃС‚СЂРѕРµРЅРЅС‹Рµ toolsets:
`web`, `browser`, `terminal`, `file`, `code_execution`, `vision`, `image_gen`,
`tts`, `skills`, `todo`, `session_search`, `delegation`, `cronjob`,
`computer_use`, `messaging`. РћСЃС‚Р°РІР»РµРЅС‹ `memory`, `clarify` Рё MCP `albery`.
Р­С‚Рѕ РІР°Р¶РЅРѕ: Р±РёР·РЅРµСЃ-РєРѕРјР°РЅРґС‹ РёР· Telegram РґРѕР»Р¶РЅС‹ РёРґС‚Рё С‡РµСЂРµР· Albery MCP, Р° РЅРµ С‡РµСЂРµР·
РїРѕРёСЃРє РїРѕ С„Р°Р№Р»Р°Рј/С‚РµСЂРјРёРЅР°Р». РџСЂРѕРІРµСЂРєР°:

```bash
hermes tools list --platform telegram
```

28.05.2026 Р±С‹Р»Р° СѓРґР°Р»РµРЅР° СЂР°Р·РґСѓС‚Р°СЏ Telegram-СЃРµСЃСЃРёСЏ
`20260527_232811_0b70890e`: РЅР° РєРѕРјР°РЅРґРµ `Р•С‰С‘ СЂР°Р· РїРѕРїСЂРѕР±СѓР№` Р°РіРµРЅС‚ СЃРґРµР»Р°Р» 25 API
РІС‹Р·РѕРІРѕРІ, СЂР°Р·РѕРіРЅР°Р» РєРѕРЅС‚РµРєСЃС‚ РґРѕ 100k+ С‚РѕРєРµРЅРѕРІ Рё РїРѕР»РµР· РІ `search_files/read_file`.
Р•СЃР»Рё С‚Р°РєРѕРµ РїРѕРІС‚РѕСЂРёС‚СЃСЏ: `systemctl restart hermes-gateway`, Р·Р°С‚РµРј
`hermes sessions list` Рё `hermes sessions delete --yes <session_id>`.

Р§С‚РѕР±С‹ Telegram Р±РѕР»СЊС€Рµ РЅРµ С‚СЏРЅСѓР» Р±РµСЃРєРѕРЅРµС‡РЅСѓСЋ РёСЃС‚РѕСЂРёСЋ Рё РЅРµ СЃР¶РёРіР°Р» 5-С‡Р°СЃРѕРІРѕР№ Р»РёРјРёС‚
Codex, РЅРѕ РїСЂРё СЌС‚РѕРј РЅРµ Р·Р°Р±С‹РІР°Р» Р°РєС‚РёРІРЅС‹Р№ СЂР°Р±РѕС‡РёР№ РґРёР°Р»РѕРі, РЅР° СЃРµСЂРІРµСЂРµ РІРєР»СЋС‡С‘РЅ СЂРµР¶РёРј
В«С‡Р°СЃ РїСЂРѕСЃС‚РѕСЏ = РЅРѕРІС‹Р№ С‡Р°С‚, Р°РєС‚РёРІРЅС‹Р№ РґРёР°Р»РѕРі = СЃР¶Р°С‚РёРµВ»:

```yaml
session_reset:
  mode: both
  idle_minutes: 30
  at_hour: 4
compression:
  enabled: true
  threshold: 0.5
  target_ratio: 0.2
  protect_first_n: 3
  protect_last_n: 20
  hygiene_hard_message_limit: 80
telegram_context_guard:
  enabled: true
  token_threshold: 50000
  message_limit: 80
```

Current `217.198.12.236` values as of 2026-05-29:

- `session_reset.idle_minutes=30`: if Telegram is quiet for 30 minutes, the next message starts a fresh session.
- `telegram_context_guard.token_threshold=50000`: before running the model on a large Telegram session, gateway asks whether to compress old context and then continue with the original message.
- `telegram_context_guard.message_limit=80`: extra safety valve for very long chats even if token estimate is unavailable.
- Context guard buttons: `Compress and continue` (`Сжать и продолжить`) runs `/compress` first, then repeats the original message; `Continue without compression` (`Продолжить без сжатия`) runs the original message once without compression.
- Backs up before server patches: `/usr/local/lib/hermes-agent/gateway/run.py.bak.<stamp>`, `/usr/local/lib/hermes-agent/gateway/platforms/telegram.py.bak.<stamp>`, `/root/.hermes/config.yaml.bak.<stamp>`.

Hermes task time budgets on `217.198.12.236` as of 2026-05-29:

```yaml
agent:
  task_wall_timeout_seconds: 600
  code_task_wall_timeout_seconds: 3600
```

- The same preference is saved in `/root/.hermes/memories/USER.md`.
- Ordinary non-code tasks have a 10 minute wall-clock budget from task start.
- Code/server/debug/deploy tasks have a 1 hour wall-clock budget from task start.
- Code-related includes files, scripts, repos, deploys, servers, APIs, MCP, logs, bugs, stack traces, Python/JS/TS/React/Node/Git/Docker/systemd.
- This is a separate wall-clock guard in `/usr/local/lib/hermes-agent/gateway/run.py`; `agent.gateway_timeout` still means inactivity timeout, not total task time.

РЎРјС‹СЃР» РЅР°СЃС‚СЂРѕР№РєРё:

- РµСЃР»Рё РІ Telegram РЅРµС‚ Р°РєС‚РёРІРЅРѕСЃС‚Рё 30 минут, СЃР»РµРґСѓСЋС‰РёР№ Р·Р°РїСЂРѕСЃ СЃС‚Р°СЂС‚СѓРµС‚ РєР°Рє РЅРѕРІС‹Р№
  С‡Р°С‚ вЂ” СЌС‚Рѕ Р·Р°С‰РёС‚Р° РѕС‚ СЃР»СѓС‡Р°Р№РЅРѕРіРѕ РїРѕРґС‚СЏРіРёРІР°РЅРёСЏ РѕРіСЂРѕРјРЅРѕР№ РёСЃС‚РѕСЂРёРё;
- РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ РјРѕР¶РµС‚ РІСЂСѓС‡РЅСѓСЋ РЅР°С‡Р°С‚СЊ РЅРѕРІС‹Р№ С‡Р°С‚ РєРѕРјР°РЅРґРѕР№ `/new` РёР»Рё `/reset`;
- РєР°Р¶РґС‹Р№ РґРµРЅСЊ РІ 04:00 gateway РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ СЃР±СЂР°СЃС‹РІР°РµС‚ Р°РєС‚РёРІРЅС‹Рµ СЃРµСЃСЃРёРё, С‡С‚РѕР±С‹
  РѕРЅРё РЅРµ Р¶РёР»Рё РЅРµРґРµР»СЏРјРё;
- РµСЃР»Рё РєРѕРЅС‚РµРєСЃС‚ СЂР°СЃС‚С‘С‚ РІ СЂР°РјРєР°С… Р°РєС‚РёРІРЅРѕРіРѕ РґРёР°Р»РѕРіР°, Hermes СЂР°РЅРѕ СЃР¶РёРјР°РµС‚ СЃС‚Р°СЂСѓСЋ С‡Р°СЃС‚СЊ РІ summary
  Рё РѕСЃС‚Р°РІР»СЏРµС‚ СЃРІРµР¶РёР№ С…РІРѕСЃС‚ РёР· РїРѕСЃР»РµРґРЅРёС… 12 СЃРѕРѕР±С‰РµРЅРёР№;
- РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ РЅР° РїСЂРѕРґРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅ Telegram context guard РІ
  `/usr/local/lib/hermes-agent/gateway/run.py` Рё
  `/usr/local/lib/hermes-agent/gateway/platforms/telegram.py`: РµСЃР»Рё РїРµСЂРµРґ
  Р·Р°РїСѓСЃРєРѕРј РјРѕРґРµР»Рё РІ Telegram-СЃРµСЃСЃРёРё РїСЂРёРјРµСЂРЅРѕ `50000+` С‚РѕРєРµРЅРѕРІ РёР»Рё `80+`
  СЃРѕРѕР±С‰РµРЅРёР№, gateway **РЅРµ Р·Р°РїСѓСЃРєР°РµС‚ РјРѕРґРµР»СЊ**, Р° РїСЂРёСЃС‹Р»Р°РµС‚ РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёРµ СЃ
  РєРЅРѕРїРєР°РјРё `Р”Р°, СЃР¶Р°С‚СЊ Рё РїСЂРѕРґРѕР»Р¶РёС‚СЊ` / `РќРµС‚, РїСЂРѕРґРѕР»Р¶РёС‚СЊ С‚Р°Рє`. РџСЂРё РІС‹Р±РѕСЂРµ
  `Р”Р°` СЃРЅР°С‡Р°Р»Р° РІС‹РїРѕР»РЅСЏРµС‚СЃСЏ `/compress`, Р·Р°С‚РµРј РїРѕРІС‚РѕСЂСЏРµС‚СЃСЏ РёСЃС…РѕРґРЅРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ.
  РџСЂРё РІС‹Р±РѕСЂРµ `РќРµС‚` РёСЃС…РѕРґРЅРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ Р·Р°РїСѓСЃРєР°РµС‚СЃСЏ Р±РµР· СЃР¶Р°С‚РёСЏ, РЅРѕ СЌС‚Рѕ СѓР¶Рµ
  РѕСЃРѕР·РЅР°РЅРЅРѕРµ СЂРµС€РµРЅРёРµ РІР»Р°РґРµР»СЊС†Р°;
- СЃС‚Р°СЂС‹Рµ transcript-СЃРµСЃСЃРёРё С‡РёСЃС‚СЏС‚СЃСЏ С‡РµСЂРµР· 3 РґРЅСЏ;
- РїСЂРѕС€Р»С‹Рµ СЃРµСЃСЃРёРё С„РёР·РёС‡РµСЃРєРё РѕСЃС‚Р°СЋС‚СЃСЏ РІ SQLite, РЅРѕ **РЅРµ РїРѕРґС‚СЏРіРёРІР°СЋС‚СЃСЏ
  Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё** РІ Telegram: Р°РІС‚Рѕ-РїРѕРёСЃРє РїРѕ СЃС‚Р°СЂС‹Рј РґРёР°Р»РѕРіР°Рј РѕС‚РєР»СЋС‡С‘РЅ, РїРѕС‚РѕРјСѓ С‡С‚Рѕ
  РѕРЅ РјРѕР¶РµС‚ РЅР°Р№С‚Рё РЅРµСЂРµР»РµРІР°РЅС‚РЅРѕРµ Рё СЃРЅРѕРІР° СЃР¶РµС‡СЊ Р»РёРјРёС‚. Р•СЃР»Рё РїРѕСЃР»Рµ reset РЅСѓР¶РЅР°
  СЃРІСЏР·СЊ СЃ РїСЂРѕС€Р»РѕР№ С‚РµРјРѕР№, Р»СѓС‡С€Рµ РєРѕСЂРѕС‚РєРѕ РЅР°РїРѕРјРЅРёС‚СЊ РєРѕРЅС‚РµРєСЃС‚ РёР»Рё Р·Р°СЂР°РЅРµРµ СЃРѕС…СЂР°РЅРёС‚СЊ
  РІР°Р¶РЅРѕРµ С‡РµСЂРµР· `Р·Р°РїРѕРјРЅРё: ...`;
- РїРѕСЃС‚РѕСЏРЅРЅС‹Рµ РїСЂРµРґРїРѕС‡С‚РµРЅРёСЏ РЅСѓР¶РЅРѕ С…СЂР°РЅРёС‚СЊ РЅРµ РІ РґР»РёРЅРЅРѕР№ РїРµСЂРµРїРёСЃРєРµ, Р° РІ `memory`
  РёР»Рё РІ СЏРІРЅС‹С… РёРЅСЃС‚СЂСѓРєС†РёСЏС… cron/Albery. РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РјРѕР¶РµС‚ РїРёСЃР°С‚СЊ Р±РѕС‚Сѓ:
  `Р·Р°РїРѕРјРЅРё: ...`, РЅРѕ РІР°Р¶РЅС‹Рµ РїСЂР°РІРёР»Р° РґР»СЏ РѕС‚С‡С‘С‚РѕРІ Р»СѓС‡С€Рµ С„РёРєСЃРёСЂРѕРІР°С‚СЊ РІ
  `РќР°СЃС‚СЂРѕР№РєРё в†’ РРЅСЃС‚СЂСѓРєС†РёРё РґР»СЏ РР` РёР»Рё РІ СЌС‚РѕРј `agent.md`.

Р’РµР±-РґР°С€Р±РѕСЂРґ СЃР»СѓС€Р°РµС‚ `127.0.0.1:9119` (РЅР°СЂСѓР¶Сѓ РЅРµ РѕС‚РєСЂС‹С‚). РЎРјРѕС‚СЂРµС‚СЊ С‡РµСЂРµР· SSH-С‚СѓРЅРЅРµР»СЊ:

```bash
ssh -L 9119:127.0.0.1:9119 root@186.246.7.32
# Р·Р°С‚РµРј РЅР° РџРљ РѕС‚РєСЂС‹С‚СЊ http://localhost:9119  (РЅСѓР¶РµРЅ Р·Р°РїСѓС‰РµРЅРЅС‹Р№ `hermes dashboard`)
```

В«РћР±СѓС‡РµРЅРёРµВ»: РїРѕРІРµРґРµРЅРёРµ РѕС‚С‡С‘С‚РѕРІ/Р·Р°РґР°С‡ РїСЂР°РІРёС‚СЃСЏ РІ Albery (`РќР°СЃС‚СЂРѕР№РєРё в†’ РРЅСЃС‚СЂСѓРєС†РёРё
РґР»СЏ РР` Рё `РЎРІРѕРґРЅР°СЏ Р°РЅР°Р»РёС‚РёРєР° в†’ РќР°СЃС‚СЂРѕР№РєР° РїСЂРѕРјС‚РѕРІ`: РєРѕРЅС‚СЂР°РєС‚С‹ `zoom_processing`,
`owner_daily`) вЂ” СЌС‚Рѕ С‡РёС‚Р°СЋС‚ Рё Hermes, Рё РІРЅРµС€РЅРёРµ Р°СЃСЃРёСЃС‚РµРЅС‚С‹. РЈСЂРѕРІРµРЅСЊ Hermes вЂ”
`hermes memory` Рё С‚РµРєСЃС‚С‹ cron (`hermes cron edit <id> --prompt "..."`).

Р’Р°Р¶РЅРѕ: РЅР° РџРљ (Р»РѕРєР°Р»СЊРЅС‹Р№ WSL) РѕСЃС‚Р°Р»СЃСЏ СЃРІРѕР№ Hermes СЃ С‚РµРјРё Р¶Рµ cron-Р·Р°РґР°С‡Р°РјРё, РЅРѕ Р±РµР·
Р·Р°РїСѓС‰РµРЅРЅРѕРіРѕ gateway вЂ” РѕРЅ РЅРµ СЃСЂР°Р±РѕС‚Р°РµС‚. РќРµ Р·Р°РїСѓСЃРєР°С‚СЊ РѕР±Р° РїР»Р°РЅРёСЂРѕРІС‰РёРєР° РїСЂРѕС‚РёРІ РѕРґРЅРѕРіРѕ
Albery (РёРЅР°С‡Рµ РІРµСЂСЃРёРѕРЅРЅР°СЏ С‡РµС…Р°СЂРґР° РІ РѕС‚С‡С‘С‚Р°С…). РќР° С‚Р°СЂРёС„Рµ Plus РІРѕР·РјРѕР¶РЅС‹ upstream
`usage limit` РЅР° С‚СЏР¶С‘Р»С‹С… РїСЂРѕРіРѕРЅР°С… вЂ” РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё РїРµСЂРµР№С‚Рё РЅР° API-РєР»СЋС‡.

### Cron script timeout (СѓРІРµР»РёС‡РµРЅ 28.05.2026 РґРѕ 900s)

РџРѕ СѓРјРѕР»С‡Р°РЅРёСЋ Hermes СѓР±РёРІР°РµС‚ `--script` cron-Р·Р°РґР°С‡Сѓ С‡РµСЂРµР· **120 СЃРµРєСѓРЅРґ**. Р”Р»СЏ
`zoom-to-tasks` СЌС‚РѕРіРѕ РјР°Р»Рѕ: РєРѕРіРґР° `zoom_watchdog.sh` РЅР°С…РѕРґРёС‚ РЅРѕРІС‹Р№ СЃРѕР·РІРѕРЅ Рё
Р·Р°РїСѓСЃРєР°РµС‚ `hermes -z` СЃ С‚СЏР¶С‘Р»С‹Рј РїСЂРѕРјРїС‚РѕРј (РїРѕР»РЅС‹Р№ С‚СЂР°РЅСЃРєСЂРёРїС‚ + AI-РіРµРЅРµСЂР°С†РёСЏ),
СЃРµСЃСЃРёСЏ РёРґС‘С‚ 3-7 РјРёРЅСѓС‚ вЂ” СЂР°РЅСЊС€Рµ cron РїР°РґР°Р» СЃ
`Script timed out after 120s: /root/.hermes/scripts/zoom_watchdog.sh`.

Р›РёРјРёС‚ РІС‹РЅРµСЃРµРЅ РІ `/root/.hermes/config.yaml`:

```yaml
cron:
  wrap_response: false
  max_parallel_jobs: null
  script_timeout_seconds: 900
```

Р РµР·РѕР»РІРёС‚СЃСЏ РІ РїРѕСЂСЏРґРєРµ: env `HERMES_CRON_SCRIPT_TIMEOUT` в†’ `cron.script_timeout_seconds`
РІ config.yaml в†’ `120` (default). РџРѕСЃР»Рµ РёР·РјРµРЅРµРЅРёСЏ вЂ” `systemctl restart hermes-gateway`.
Р‘СЌРєР°Рї СЃС‚Р°СЂРѕРіРѕ РєРѕРЅС„РёРіР° РїРµСЂРµРґ РїСЂР°РІРєРѕР№: `/root/.hermes/config.yaml.bak.<unix_ts>`.

### Р”РµРїР»РѕР№ Hermes-РїСЂРѕРјРїС‚РѕРІ

РџСЂРѕРјРїС‚ cron-Р·Р°РґР°С‡Рё `owner-daily` Р¶РёРІС‘С‚ РІ **РґРІСѓС… РјРµСЃС‚Р°С…**:

1. **РСЃС‚РѕС‡РЅРёРє РїСЂР°РІРґС‹ (РІ git):** [scripts/hermes_owner_daily_prompt.txt](scripts/hermes_owner_daily_prompt.txt)
2. **РџСЂРёРјРµРЅС‘РЅРЅС‹Р№ РЅР° РїСЂРѕРґРµ:** РїРѕР»Рµ `prompt` Сѓ РґР¶РѕР±С‹ `owner-daily` РІ
   `/root/.hermes/cron/jobs.json`.

РџСЂРёРјРµРЅРµРЅРёРµ/РѕР±РЅРѕРІР»РµРЅРёРµ РїСЂРѕРјРїС‚Р° РЅР° РїСЂРѕРґРµ:

```powershell
python scripts/update_hermes_owner_daily_prompt.py
```

РЎРєСЂРёРїС‚:
- С‡РёС‚Р°РµС‚ `scripts/hermes_owner_daily_prompt.txt`;
- С‡РµСЂРµР· paramiko Р·Р°С…РѕРґРёС‚ РЅР° РїСЂРѕРґ (РїР°СЂРѕР»СЊ РёР· Р»РѕРєР°Р»СЊРЅРѕРіРѕ `.env`, РЅРµ СЃРІРµС‚РёС‚СЃСЏ РІ Р»РѕРіРµ);
- СЃРѕС…СЂР°РЅСЏРµС‚ Р±СЌРєР°Рї `/root/.hermes/cron/jobs.json.bak`;
- РїР°С‚С‡РёС‚ `prompt` Сѓ РґР¶РѕР±С‹ `owner-daily` Рё РєР»Р°РґС‘С‚ РѕР±СЂР°С‚РЅРѕ (chmod 600);
- РґРµР»Р°РµС‚ `systemctl restart hermes-gateway`.

РћС‚РєР°С‚ вЂ” РїРµСЂРµРёРјРµРЅРѕРІР°С‚СЊ `jobs.json.bak` РѕР±СЂР°С‚РЅРѕ РІ `jobs.json` Рё СЂРµСЃС‚Р°СЂС‚Р°РЅСѓС‚СЊ gateway.

### РџСЂР°РІРёР»Рѕ: РїРѕСЃР»Рµ Р»СЋР±С‹С… РёР·РјРµРЅРµРЅРёР№ РІ Hermes / MCP вЂ” СЂРµСЃС‚Р°СЂС‚РёС‚СЊ gateway Рё РїРёСЃР°С‚СЊ РґР°Р»СЊРЅРµР№С€РёРµ С€Р°РіРё РІР»Р°РґРµР»СЊС†Сѓ

**РћР±СЏР·Р°С‚РµР»СЊРЅРѕРµ РїСЂР°РІРёР»Рѕ РґР»СЏ Р±СѓРґСѓС‰РёС… РёР·РјРµРЅРµРЅРёР№.** `update_server.sh` РїРµСЂРµР·Р°РїСѓСЃРєР°РµС‚ С‚РѕР»СЊРєРѕ `albery.service` (С‚Р°Рј Р¶РёРІС‘С‚ MCP HTTP-СЃРµСЂРІРµСЂ). РќРѕ **`hermes-gateway.service` РѕС‚РґРµР»СЊРЅС‹Р№ РїСЂРѕС†РµСЃСЃ**, РєРѕС‚РѕСЂС‹Р№ РєСЌС€РёСЂСѓРµС‚ СЃРїРёСЃРѕРє MCP-РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ РЅР° СЃС‚Р°СЂС‚Рµ + Telegram-СЃРµСЃСЃРёРё РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ РєСЌС€РёСЂСѓСЋС‚ toolset РЅР° СЃС‚Р°СЂС‚Рµ СЃРµСЃСЃРёРё. РџРѕСЌС‚РѕРјСѓ РµСЃР»Рё РЅРёС‡РµРіРѕ Р±РѕР»СЊС€Рµ РЅРµ РґРµР»Р°С‚СЊ вЂ” Hermes РїСЂРѕРґРѕР»Р¶РёС‚ РІРёРґРµС‚СЊ СЃС‚Р°СЂС‹Р№ СЃРїРёСЃРѕРє, Рё Р°РєС‚РёРІРЅС‹Р№ Telegram-С‡Р°С‚ С‚РѕР¶Рµ.

РўСЂРёРіРіРµСЂС‹, РїРѕСЃР»Рµ РєРѕС‚РѕСЂС‹С… **РѕР±СЏР·Р°С‚РµР»РµРЅ** СЂРµСЃС‚Р°СЂС‚ `hermes-gateway`:
- РґРѕР±Р°РІР»РµРЅ/СѓРґР°Р»С‘РЅ/РїРµСЂРµРёРјРµРЅРѕРІР°РЅ MCP-РёРЅСЃС‚СЂСѓРјРµРЅС‚ РІ [mcp/context_server.py](mcp/context_server.py);
- РёР·РјРµРЅРµРЅР° `inputSchema` РёР»Рё `description` СЃСѓС‰РµСЃС‚РІСѓСЋС‰РµРіРѕ MCP-РёРЅСЃС‚СЂСѓРјРµРЅС‚Р° (Hermes РёС… РєСЌС€РёСЂСѓРµС‚);
- РёР·РјРµРЅС‘РЅ `/root/.hermes/config.yaml` (`display`, `cron`, `session_reset`, `compression`, `telegram_context_guard`, toolsets РїР»Р°С‚С„РѕСЂРјС‹);
- РёР·РјРµРЅС‘РЅ `/root/.hermes/cron/jobs.json` (РїСЂРѕРјРїС‚, СЂР°СЃРїРёСЃР°РЅРёРµ, deliver) вЂ” `update_hermes_*_prompt.py` СЌС‚Рѕ СѓР¶Рµ РґРµР»Р°СЋС‚ СЃР°РјРё;
- РёР·РјРµРЅС‘РЅ РєРѕРґ Hermes РІ `/usr/local/lib/hermes-agent/` (РїР°С‚С‡Рё gateway/telegram.py Рё С‚.Рї.).

РљРѕРјР°РЅРґР° (СЂРµСЃС‚Р°СЂС‚ РїР°СЂС‹):

```bash
ssh root@186.246.7.32 'systemctl restart albery hermes-gateway && systemctl is-active albery hermes-gateway'
```

РџСЂРѕРІРµСЂРєР°, С‡С‚Рѕ Hermes СѓРІРёРґРµР» РЅРѕРІС‹Р№ toolset:

```bash
ssh root@186.246.7.32 'hermes mcp test albery 2>&1 | grep -E "Tools discovered|<new_tool_name>"'
```

**РџРѕСЃР»Рµ СЂРµСЃС‚Р°СЂС‚Р° вЂ” РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ СЃРѕРѕР±С‰РёС‚СЊ РІР»Р°РґРµР»СЊС†Сѓ РґР°Р»СЊРЅРµР№С€РёРµ С€Р°РіРё РІ С‡Р°С‚Рµ.** РњРёРЅРёРјСѓРј: В«РІ Telegram-С‡Р°С‚Рµ СЃ Hermes РЅР°РїРёС€Рё `/reset` (РёР»Рё `/new`), С‡С‚РѕР±С‹ СЃРµСЃСЃРёСЏ РїРѕРґС‚СЏРЅСѓР»Р° РЅРѕРІС‹Р№ СЃРїРёСЃРѕРє РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІВ». Р‘РµР· `/reset` Р°РєС‚РёРІРЅР°СЏ Telegram-СЃРµСЃСЃРёСЏ РјРѕР¶РµС‚ РїСЂРѕРґРѕР»Р¶Р°С‚СЊ РІРёРґРµС‚СЊ СЃС‚Р°СЂС‹Р№ toolset РґРѕ С‚РµС… РїРѕСЂ, РїРѕРєР° РµС‘ РЅРµ СЃР±СЂРѕСЃРёС‚ idle-С‚Р°Р№РјРµСЂ (30 минут, РїРѕРІС‚РѕСЂРёС‚СЊ cron-РєРѕРјР°РЅРґСѓ РІ С‡Р°С‚Рµ, РёР»Рё РѕРґРѕР±СЂРёС‚СЊ СЂР°СЃСЃС‹Р»РєСѓ вЂ” СѓРєР°Р·Р°С‚СЊ РєРѕРЅРєСЂРµС‚РЅРѕРµ РґРµР№СЃС‚РІРёРµ).

РџСЂРёР·РЅР°Рє, С‡С‚Рѕ toolset СѓСЃС‚Р°СЂРµР»: Hermes РѕС‚РєР°Р·С‹РІР°РµС‚ СЃ РѕРїРёСЃР°РЅРёРµРј **РґСЂСѓРіРѕРіРѕ** РёРЅСЃС‚СЂСѓРјРµРЅС‚Р° (РІРёРґРµР» 2026-05-28 РїРѕСЃР»Рµ РґРµРїР»РѕСЏ `send_bitrix_message` вЂ” Hermes СЃРѕСЃР»Р°Р»СЃСЏ РЅР° `send_owner_recommendations_to_bitrix`, РїРѕС‚РѕРјСѓ С‡С‚Рѕ РІ РєСЌС€Рµ СЃРµСЃСЃРёРё РЅРѕРІРѕРіРѕ РёРЅСЃС‚СЂСѓРјРµРЅС‚Р° РµС‰С‘ РЅРµ Р±С‹Р»Рѕ).

### MCP-РёРЅСЃС‚СЂСѓРјРµРЅС‚ `fetch_url` (РґРѕР±Р°РІР»РµРЅРѕ 28.05.2026)

**Р—Р°С‡РµРј.** Р’ Hermes РґР»СЏ Telegram-РїР»Р°С‚С„РѕСЂРјС‹ РѕС‚РєР»СЋС‡РµРЅС‹ РІСЃС‚СЂРѕРµРЅРЅС‹Рµ `web`/`browser` toolset'С‹ ([agent.md:1538-1543](agent.md#L1538-L1543)) вЂ” РїРѕСЃР»Рµ РёРЅС†РёРґРµРЅС‚Р° 28.05 СЃ СЂР°Р·РґСѓС‚РѕР№ СЃРµСЃСЃРёРµР№ РЅР° 100k С‚РѕРєРµРЅРѕРІ. РџРѕСЌС‚РѕРјСѓ Hermes РЅРµ РјРѕРі РѕС‚РєСЂС‹РІР°С‚СЊ СЃСЃС‹Р»РєРё РёР· С‡Р°С‚Р° (Google Sheets/Docs, СЃС‚Р°С‚СЊРё, СЂРµРіР»Р°РјРµРЅС‚С‹). Р’РєР»СЋС‡Р°С‚СЊ `web` РѕР±СЂР°С‚РЅРѕ РѕРїР°СЃРЅРѕ вЂ” РѕРґРЅР° Р±РѕР»СЊС€Р°СЏ СЃС‚СЂР°РЅРёС†Р° СЃСЉРµСЃС‚ РїРѕР»РєРѕРЅС‚РµРєСЃС‚Р° Codex.

**Р РµС€РµРЅРёРµ.** РћС‚РґРµР»СЊРЅС‹Р№ MCP-РёРЅСЃС‚СЂСѓРјРµРЅС‚ `fetch_url(url, max_chars?, strip_html?)`:
- **Google Sheets** URL (`docs.google.com/spreadsheets/d/<id>/edit?gid=<n>`) Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё РїРµСЂРµРїРёСЃС‹РІР°РµС‚СЃСЏ РІ `/export?format=csv&gid=<n>` в†’ РІРѕР·РІСЂР°С‰Р°РµС‚СЃСЏ С‡РёСЃС‚С‹Р№ CSV.
- **Google Docs** URL (`docs.google.com/document/d/<id>/...`) в†’ `/export?format=txt`.
- РџСЂРѕС‡РёРµ URL: HTTP GET + `User-Agent: AlberyMCP/0.7`, РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ HTML-С‚РµРіРё СЃСЂРµР·Р°СЋС‚СЃСЏ РґРѕ С‚РµРєСЃС‚Р°, СЃРєСЂРёРїС‚С‹/СЃС‚РёР»Рё РІС‹РєРёРґС‹РІР°СЋС‚СЃСЏ.
- **Size cap:** default `max_chars=50000`, max 200000. Р­С‚Рѕ ~12k С‚РѕРєРµРЅРѕРІ РЅР° РѕС‚РІРµС‚ вЂ” РЅРµ СЃСЉРµРґР°РµС‚ РєРѕРЅС‚РµРєСЃС‚.
- РќР° HTTP 401/403 РґР»СЏ Google-РґРѕРєСѓРјРµРЅС‚РѕРІ РІ РѕС‚РІРµС‚ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ `hint`: В«РћС‚РєСЂРѕР№С‚Рµ РґРѕСЃС‚СѓРї "Р›СЋР±РѕР№, Сѓ РєРѕРіРѕ РµСЃС‚СЊ СЃСЃС‹Р»РєР° вЂ” РџСЂРѕСЃРјРѕС‚СЂ" Р»РёР±Рѕ РїРѕР»РѕР¶РёС‚Рµ С„Р°Р№Р» РІ Drive-РїР°РїРєСѓ, РєРѕС‚РѕСЂСѓСЋ С‡РёС‚Р°РµС‚ Albery С‡РµСЂРµР· Apps Script (`list_company_files` / `search_company_knowledge` / `get_company_file`)В».

РљРѕРіРґР° **РќР•** РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ `fetch_url`: РґР»СЏ Р·РЅР°РЅРёР№, РєРѕС‚РѕСЂС‹Рµ СѓР¶Рµ СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅС‹ РІ Albery (СЂРµРіР»Р°РјРµРЅС‚С‹, РёРЅСЃС‚СЂСѓРєС†РёРё, Zoom-СЂР°СЃС€РёС„СЂРѕРІРєРё, С‡Р°С‚С‹) вЂ” С‚Р°Рј Р±С‹СЃС‚СЂРµРµ Рё С‚РѕС‡РЅРµРµ СЂР°Р±РѕС‚Р°СЋС‚ `search_company_knowledge`, `list_company_files`, `get_company_file`, `search_messages`, `get_zoom_call_transcript`.

**РџСЂРѕРІРµСЂРµРЅРѕ РЅР° СЂРµР°Р»СЊРЅРѕРј Google Sheet** (28.05.2026, `17NZP5U5YBQPKKQrBUGq05bpTjq2V-KBX98uM1Wa2W_4`): 0.82СЃ, HTTP 200, 6103 СЃРёРјРІРѕР»Р° CSV, РЅРµ truncated. Р Р°СЃРїР°СЂСЃРёР»РѕСЃСЊ РєР°Рє 40 СЃС‚СЂРѕРє Г— 7 РєРѕР»РѕРЅРѕРє.

**Р’РµСЂСЃРёСЏ MCP** РїРѕРґРЅСЏС‚Р° РґРѕ `0.7.0`, РёРЅСЃС‚СЂСѓРјРµРЅС‚РѕРІ 46. РљРѕРјРјРёС‚ `92c7391`.

**Flow РІ Telegram РїРѕСЃР»Рµ /reset:** В«РџСЂРѕС‡РёС‚Р°Р№ С‚Р°Р±Р»РёС†Сѓ <СЃСЃС‹Р»РєР°> Рё СЃРѕР·РґР°Р№ Р·Р°РґР°С‡Рё РІ Р‘РёС‚СЂРёРєСЃРµВ» в†’ Hermes СЃР°Рј Р·РѕРІС‘С‚ `fetch_url(...)` в†’ РїР°СЂСЃРёС‚ CSV в†’ СЂРµР·РѕР»РІРёС‚ Р¤РРћ РёСЃРїРѕР»РЅРёС‚РµР»РµР№/РЅР°Р±Р»СЋРґР°С‚РµР»РµР№ С‡РµСЂРµР· `_resolve_active_bitrix_user(s)` в†’ РїРѕРєР°Р·С‹РІР°РµС‚ РїР»Р°РЅ в†’ Р¶РґС‘С‚ В«СЃРѕР·РґР°РІР°Р№В» в†’ С†РёРєР»РѕРј `create_bitrix_task` РЅР° РєР°Р¶РґСѓСЋ СЃС‚СЂРѕРєСѓ (СЃ `auditor_names`, `periodic` РµСЃР»Рё РµСЃС‚СЊ).

### РР·РІРµСЃС‚РЅС‹Р№ Р±Р°Рі: 120s С‚Р°Р№РјР°СѓС‚ `create_bitrix_task` / `delete_bitrix_task` (РёСЃРїСЂР°РІР»РµРЅРѕ 28.05.2026)

**РЎРёРјРїС‚РѕРј.** Hermes РІ Telegram РѕС‚РІРµС‡Р°Р»: В«РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР·РґР°С‚СЊ Р·Р°РґР°С‡СѓВ» РёР»Рё В«MCP call timed out after 120.0sВ». Р’ Р¶СѓСЂРЅР°Р»Рµ `journalctl -u hermes-gateway`:

```
ERROR tools.mcp_tool: MCP tool albery/create_bitrix_task call failed:
MCP call timed out after 120.0s (configured timeout: 120.0s)
```

**РљРѕСЂРЅРµРІР°СЏ РїСЂРёС‡РёРЅР°.** Р’ Albery Р¶РёР»Рё **РґРІРµ СЂР°Р·РЅС‹Рµ СЂРµР°Р»РёР·Р°С†РёРё Bitrix-РєР»РёРµРЅС‚Р°**:
- `BitrixClient` РІ [app.py:14246](app.py#L14246) вЂ” РЅР° `requests.Session`, РєСЌС€, retry. **Р‘С‹СЃС‚СЂС‹Р№**, < 2s. РСЃРїРѕР»СЊР·СѓСЋС‚ `send_bitrix_message`, `dispatch_zoom_operational_tasks`, `send_owner_recommendations_to_bitrix`.
- `_bitrix_call_with_fallback` РІ [mcp/context_server.py](mcp/context_server.py) вЂ” РЅР° РіРѕР»РѕРј `urllib.request.urlopen(timeout=60)`. **Р—Р°РІРёСЃР°Р» СЂРѕРІРЅРѕ 120СЃ** (30 минут, `delete_bitrix_task`.

Hermes-side MCP-РєР»РёРµРЅС‚ РёРјРµРµС‚ СЃРІРѕР№ ceiling 120s в†’ urllib РґРѕС…РѕРґРёР» РґРѕ 120s СЂР°РЅСЊС€Рµ, С‡РµРј С‡С‚Рѕ-Р»РёР±Рѕ РѕС‚РІРµС‚РёР» в†’ Hermes Р»РѕРІРёР» `MCP call timed out`, Р° РЅРёРєР°РєР°СЏ Р·Р°РґР°С‡Р° РІ Bitrix РЅРµ СЃРѕР·РґР°РІР°Р»Р°СЃСЊ.

Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅРѕ Сѓ `delete_bitrix_task` Р±С‹Р» **SQL-Р±Р°Рі**: JOIN РЅР° РЅРµСЃСѓС‰РµСЃС‚РІСѓСЋС‰СѓСЋ РєРѕР»РѕРЅРєСѓ `bitrix_tasks.responsible_user_id` (РЅР° СЃР°РјРѕРј РґРµР»Рµ РєРѕР»РѕРЅРєР° Р·РѕРІС‘С‚СЃСЏ `responsible_id`) в†’ РєР°Р¶РґС‹Р№ РІС‹Р·РѕРІ РїР°РґР°Р» СЃ `psycopg.errors.UndefinedColumn` РµС‰С‘ РґРѕ РѕР±СЂР°С‰РµРЅРёСЏ РІ Bitrix.

**Р¤РёРєСЃ.**
1. Р’ [app.py](app.py) РґРѕР±Р°РІР»РµРЅ workflow `bitrix_method_call(method, payload, prefer_api=True)` вЂ” С‚РѕРЅРєР°СЏ РѕР±С‘СЂС‚РєР° РЅР°Рґ `BitrixClient.call_with_fallback`. Р”РѕСЃС‚СѓРїРµРЅ С‡РµСЂРµР· `app_workflow_function("bitrix_method_call")`.
2. `_bitrix_call_with_fallback` РІ [mcp/context_server.py](mcp/context_server.py) СЃРІС‘СЂРЅСѓС‚ РґРѕ 8 СЃС‚СЂРѕРє вЂ” РґРµР»РµРіРёСЂСѓРµС‚ РІ `bitrix_method_call`. Р“РѕР»С‹Р№ urllib РІС‹РїРёР»РµРЅ.
3. SQL РІ `tool_delete_bitrix_task` РїРѕРїСЂР°РІР»РµРЅ: `responsible_user_id` в†’ `responsible_id`.

РџРѕСЃР»Рµ С„РёРєСЃР° Р·Р°РјРµСЂС‹ РЅР° РїСЂРѕРґРµ (СЃ СЂРµР°Р»СЊРЅС‹Рј Bitrix С‡РµСЂРµР· VPN-Р­СЃС‚РѕРЅРёСЋ):
- Р Р°Р·РѕРІР°СЏ Р·Р°РґР°С‡Р°: **1.02s**
- Р—Р°РґР°С‡Р° СЃ РЅР°Р±Р»СЋРґР°С‚РµР»СЏРјРё (1 С‡РµР»РѕРІРµРє): **0.67s**
- РџРµСЂРёРѕРґРёС‡РµСЃРєР°СЏ weekly СЃ `IS_REGULAR=Y`: **0.72s** (Bitrix-РїРѕСЂС‚Р°Р» РїСЂРёРЅРёРјР°РµС‚ `REGULAR_PARAMETERS` СЂРѕРІРЅРѕ РІ РЅР°С€РµРј С„РѕСЂРјР°С‚Рµ)

Р’РµСЂСЃРёСЏ MCP РїРѕРґРЅСЏС‚Р° РґРѕ `0.6.1`. РљРѕРјРјРёС‚С‹: `db0c4e0` (urllib в†’ BitrixClient), `90109e1` (SQL fix).

**РџСЂР°РІРёР»Рѕ РЅР° Р±СѓРґСѓС‰РµРµ.** Р›СЋР±РѕР№ РЅРѕРІС‹Р№ MCP-РёРЅСЃС‚СЂСѓРјРµРЅС‚, РґС‘СЂРіР°СЋС‰РёР№ Bitrix API, РѕР±СЏР·Р°РЅ РёРґС‚Рё С‡РµСЂРµР· `app_workflow_function("bitrix_method_call")` (РёР»Рё РїСЂСЏРјРѕ `BitrixClient` РІ СЃР°РјРѕРј app.py). РќРµ РґРµР»Р°С‚СЊ СЃРѕР±СЃС‚РІРµРЅРЅС‹Рµ urllib-РѕР±С‘СЂС‚РєРё вЂ” СЌС‚Рѕ СѓР¶Рµ РѕРґРёРЅ СЂР°Р· РїСЂРёРІРµР»Рѕ Рє 120СЃ С‚Р°Р№РјР°СѓС‚Сѓ РІ РїСЂРѕРґРµ.

### РР·РІРµСЃС‚РЅР°СЏ РіСЂР°РЅ. СЃРёС‚СѓР°С†РёСЏ: time-Р·РѕРЅС‹ РІ title В«РС‚РѕРіРё СЃРѕР·РІРѕРЅР° Р§Р§:РњРњВ»

Р’ Postgres РєРѕР»РѕРЅРєР° `zoom_calls.start_time_msk` С„Р°РєС‚РёС‡РµСЃРєРё С…СЂР°РЅРёС‚СЃСЏ РєР°Рє UTC
(`timestamptz`), РЅРµСЃРјРѕС‚СЂСЏ РЅР° РЅР°Р·РІР°РЅРёРµ СЃ `_msk`. РљРѕРЅРІРµСЂСЃРёСЏ РІ РњРЎРљ РґРµР»Р°РµС‚СЃСЏ РЅР°
runtime С‡РµСЂРµР· `astimezone(MSK_TZ)`. Р­С‚Рѕ СЂР°Р±РѕС‚Р°РµС‚ РєРѕСЂСЂРµРєС‚РЅРѕ РІ happy-path
(`zoom_call_row_payload` precomputed-РёС‚ `time_text` РєР°Рє `"09:28 - 10:26"` СѓР¶Рµ
РІ РњРЎРљ). РќРѕ **fallback-РїСѓС‚Рё** (РєРѕРіРґР° `time_text` РїСѓСЃС‚РѕР№) РєРѕРіРґР°-С‚Рѕ Р±СЂР°Р»Рё `str(start_time_msk)` РЅР°РїСЂСЏРјСѓСЋ вЂ” РІС‹РґР°РІР°Р»Рё
ISO СЃ `+00:00` Рё РІ title РІС‹Р»РµР·Р°Р»Рѕ UTC РІСЂРµРјСЏ (РЅР°РїСЂРёРјРµСЂ `"РС‚РѕРіРё СЃРѕР·РІРѕРЅР° 06:28"`
РІРјРµСЃС‚Рѕ РњРЎРљ `09:28`).

Р—Р°С„РёРєСЃРёСЂРѕРІР°РЅРѕ 28.05.2026:
- backend `build_zoom_operational_tasks_dispatch` ([app.py:3601-3611](app.py#L3601-L3611)) С‚РµРїРµСЂСЊ РєРѕРЅРІРµСЂС‚РёС‚ fallback С‡РµСЂРµР· `parse_datetime(...).astimezone(MSK_TZ).strftime('%H:%M')`;
- frontend `buildLocalZoomOperationalPreview` ([РРЅС‚РµСЂС„РµР№СЃ/src/App.tsx:4110-4124](РРЅС‚РµСЂС„РµР№СЃ/src/App.tsx#L4110-L4124)) РёСЃРїРѕР»СЊР·СѓРµС‚ `Date.toLocaleTimeString({timeZone: 'Europe/Moscow'})`.

Р•СЃР»Рё РІ Р±СѓРґСѓС‰РµРј РїРѕСЏРІРёС‚СЃСЏ РЅРѕРІС‹Р№ РєРѕРґ, С„РѕСЂРјРёСЂСѓСЋС‰РёР№ В«РС‚РѕРіРё СЃРѕР·РІРѕРЅР° вЂ¦В» РёР· ISO-СЃС‚СЂРѕРєРё вЂ” РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ РєРѕРЅРІРµСЂС‚РёСЂРѕРІР°С‚СЊ РІ РњРЎРљ. РџСЂСЏРјРѕР№ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ `str(call.start_time_msk)` РЅРµР»СЊР·СЏ.

### Р”РѕСЂРѕР¶РЅР°СЏ РєР°СЂС‚Р°: РІРЅРµРґСЂРµРЅРёРµ Hermes РІ РєРѕРјРїР°РЅРёСЋ + RBAC РїРѕ СЂРѕР»СЏРј (РїР»Р°РЅ, РЅРµ РІС‹РїРѕР»РЅРµРЅРѕ)

РћР±СЃСѓР¶РґРµРЅРѕ 28.05.2026. РЎРµР№С‡Р°СЃ Hermes РЅР° РїСЂРѕРґРµ вЂ” **РѕРґРёРЅ РёРЅСЃС‚Р°РЅСЃ, РѕРґРёРЅ Telegram-Р±РѕС‚, РѕРґРёРЅ MCP-СЃРµРєСЂРµС‚**, `TELEGRAM_ALLOWED_USERS=<TG_ID РІР»Р°РґРµР»СЊС†Р°>`. Р­С‚Рѕ СЂР°Р±РѕС‚Р°РµС‚ РґР»СЏ РІР»Р°РґРµР»СЊС†Р°, РЅРѕ **РЅРµ РјР°СЃС€С‚Р°Р±РёСЂСѓРµС‚СЃСЏ** РЅР° РјРµРЅРµРґР¶РµСЂРѕРІ/СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ.

**РћРіСЂР°РЅРёС‡РµРЅРёРµ Hermes:** `hermes tools list --platform telegram` Р·Р°РґР°С‘С‚ toolset РЅР° **РІСЃСЋ РїР»Р°С‚С„РѕСЂРјСѓ**, РЅРµ РЅР° РѕС‚РґРµР»СЊРЅРѕРіРѕ TG-РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ. Р’РЅСѓС‚СЂРё РѕРґРЅРѕРіРѕ Р±РѕС‚Р° СЃРґРµР»Р°С‚СЊ В«РІР»Р°РґРµР»СЊС†Сѓ РІСЃС‘, РјРµРЅРµРґР¶РµСЂСѓ РїРѕР»РѕРІРёРЅСѓ, СЃРѕС‚СЂСѓРґРЅРёРєСѓ С‚РѕР»СЊРєРѕ readВ» **РЅРµР»СЊР·СЏ РЅР°С‚РёРІРЅРѕ** вЂ” С‚РѕР»СЊРєРѕ soft-RBAC РІ AI-РёРЅСЃС‚СЂСѓРєС†РёРё, РєРѕС‚РѕСЂС‹Р№ РјРѕРґРµР»СЊ РјРѕР¶РµС‚ В«Р·Р°Р±С‹С‚СЊВ» РїРѕСЃР»Рµ `/compress`. Р”Р»СЏ Bitrix-write СЌС‚Рѕ РЅРµРґРѕРїСѓСЃС‚РёРјРѕ.

**Р¦РµР»РµРІР°СЏ Р°СЂС…РёС‚РµРєС‚СѓСЂР° (3 С‚РёСЂР°, СЂР°СЃС€РёСЂРµРЅРёРµ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РµРіРѕ FAQ MCP):**

```
Albery backend (РѕРґРёРЅ)
в”њв”Ђв”Ђ /mcp/<MCP_SHARED_SECRET>         в†’ 45 tools (full)          в†’ hermes-owner   (С‚РІРѕР№ TG)
в”њв”Ђв”Ђ /mcp-manager/<MCP_MANAGER_SECRET> в†’ ~20 tools (read + СЃРІРѕСЏ
в”‚                                       Р·РѕРЅР°, Р±РµР· im.message,
в”‚                                       Р±РµР· dispatch, Р±РµР· delete) в†’ hermes-manager (5 TG)
в””в”Ђв”Ђ /mcp-faq/<MCP_FAQ_SHARED_SECRET> в†’ 12 tools (read-only,
                                       СѓР¶Рµ СЂР°Р±РѕС‚Р°РµС‚)             в†’ hermes-staff   (РІСЃРµ TG)
```

РљР°Р¶РґС‹Р№ Hermes вЂ” РѕС‚РґРµР»СЊРЅС‹Р№ systemd-СЋРЅРёС‚ РІ `/root/.hermes-<role>/` СЃРѕ СЃРІРѕРёРј `auth.json`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, СЃРІРѕРµР№ `state.db`/РїР°РјСЏС‚СЊСЋ. Cron-РґР¶РѕР±С‹ (`zoom-to-tasks`, `owner-daily`) РѕСЃС‚Р°СЋС‚СЃСЏ **С‚РѕР»СЊРєРѕ Сѓ owner-РёРЅСЃС‚Р°РЅСЃР°**.

**Р¦РµРЅР°:** RAM ~250 РњР‘ Г— 3 = 750 РњР‘ (РЅР° 2 Р“Р‘ + swap 2 Р“Р‘ вЂ” С‚СЏРЅРµС‚). Codex-Р»РёРјРёС‚ РґРµР»РёС‚СЃСЏ РїРѕРёРЅСЃС‚Р°РЅСЃРЅРѕ в†’ Р»СѓС‡С€Рµ РѕС‚РґРµР»СЊРЅС‹Рµ ChatGPT Plus РїРѕРґРїРёСЃРєРё РЅР° РёРЅСЃС‚Р°РЅСЃ СЃ СЂРµР°Р»СЊРЅРѕР№ РЅР°РіСЂСѓР·РєРѕР№. РРЅР°С‡Рµ РІСЃРµ С‚СЂРё РёРЅСЃС‚Р°РЅСЃР° Р±СѓРґСѓС‚ РєРѕРЅРєСѓСЂРёСЂРѕРІР°С‚СЊ Р·Р° РѕРґРёРЅ 5-С‡Р°СЃРѕРІРѕР№ Р»РёРјРёС‚.

**РЁР°РіРё РІРЅРµРґСЂРµРЅРёСЏ (РІ СЌС‚РѕРј РїРѕСЂСЏРґРєРµ):**

1. **Р Р°СЃС€РёСЂРёС‚СЊ MCP РґРѕ manager-СЌРЅРґРїРѕРёРЅС‚Р°.** Р’ [mcp/context_server.py](mcp/context_server.py) РґРѕР±Р°РІРёС‚СЊ С‚СЂРµС‚СЊСЋ С‚РѕС‡РєСѓ РІС…РѕРґР° `/mcp-manager/<secret>` СЂСЏРґРѕРј СЃ `/mcp/` Рё `/mcp-faq/` (РїРѕ Р°РЅР°Р»РѕРіРёРё СЃ С‚РµРј, РєР°Рє СЃРґРµР»Р°РЅ FAQ вЂ” СЃРј. [agent.md:608-626](agent.md#L608-L626)). Toolset РґР»СЏ РјРµРЅРµРґР¶РµСЂР°: `search_tasks`, `get_task_comments`, `search_zoom_transcripts`, `get_zoom_call_transcript`, `search_company_knowledge`, `get_company_file`, `list_chats`, `search_messages`, `get_chat_transcript`, `get_org_structure`, `get_context_guide`, `start_here_always_read_ai_instructions`, `health`, `list_available_sources`. **РќРµ РґР°РІР°С‚СЊ** РјРµРЅРµРґР¶РµСЂСѓ: `create_bitrix_task`, `delete_bitrix_task`, `dispatch_zoom_operational_tasks`, `send_bitrix_message`, `send_owner_recommendations_to_bitrix`, `save_*_report`, `delete_zoom_call_report`, `upsert_ai_instruction`, `process_chat_ocr`, `cancel_owner_recommendation`.
2. **РџРѕРґРЅСЏС‚СЊ `hermes-manager` РёРЅСЃС‚Р°РЅСЃ.** РћС‚РґРµР»СЊРЅС‹Р№ `/root/.hermes-manager/`, РѕС‚РґРµР»СЊРЅС‹Р№ Р±РѕС‚ РІ BotFather, `TELEGRAM_ALLOWED_USERS` = TG-id 1-2 РјРµРЅРµРґР¶РµСЂРѕРІ РґР»СЏ РїРёР»РѕС‚Р°. Р‘РµР· cron. РџСЂРёС†РµРїРёС‚СЊ С‚РѕР»СЊРєРѕ `/mcp-manager/`. РЎРІРѕР№ `auth.json`, Р¶РµР»Р°С‚РµР»СЊРЅРѕ РѕС‚РґРµР»СЊРЅС‹Р№ ChatGPT-Р°РєРєР°СѓРЅС‚.
3. **РћР±РєР°С‚Р°С‚СЊ 1-2 РЅРµРґРµР»Рё** РЅР° РїРёР»РѕС‚РЅРѕР№ РїР°СЂРµ РјРµРЅРµРґР¶РµСЂРѕРІ. AI-РёРЅСЃС‚СЂСѓРєС†РёСЏ РґР»СЏ manager-MCP вЂ” РѕС‚РґРµР»СЊРЅС‹Р№ РґРѕРєСѓРјРµРЅС‚ РІ Albery В«Hermes РґР»СЏ РјРµРЅРµРґР¶РµСЂР°: С‡С‚Рѕ РјРѕР¶РЅРѕ РґРµР»Р°С‚СЊВ», С‡РёС‚Р°РµС‚СЃСЏ С‡РµСЂРµР· `start_here_always_read_ai_instructions` РєР°Р¶РґРѕР№ СЃРµСЃСЃРёРµР№.
4. **Р•СЃР»Рё Р·Р°Р№РґС‘С‚ вЂ” РѕС‚РєСЂС‹С‚СЊ `hermes-staff`** С‡РµСЂРµР· СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ `/mcp-faq/` (12 tools, СЂРµРіР»Р°РјРµРЅС‚С‹ + Zoom-СЂР°СЃС€РёС„СЂРѕРІРєРё + РѕСЂРіСЃС‚СЂСѓРєС‚СѓСЂР°). РўСЂРµС‚РёР№ Р±РѕС‚, С€РёСЂРёРј РЅР° РІСЃРµС… СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ.

**Р§РµРіРѕ РќР• РґРµР»Р°С‚СЊ:** РЅРµ РґР°РІР°С‚СЊ СЃРѕС‚СЂСѓРґРЅРёРєР°Рј MCP-СЃРµРєСЂРµС‚ РЅР°РїСЂСЏРјСѓСЋ (С‚РѕР»СЊРєРѕ С‡РµСЂРµР· СЃРµСЂРІРµСЂРЅРѕРіРѕ Hermes-Р±РѕС‚Р°); РЅРµ РїСѓР±Р»РёРєРѕРІР°С‚СЊ СЃРµРєСЂРµС‚С‹ РІ РєР»РёРµРЅС‚СЃРєРѕРј РєРѕРґРµ; РЅРµ Р·Р°РїСѓСЃРєР°С‚СЊ РІС‚РѕСЂРѕР№ РїР»Р°РЅРёСЂРѕРІС‰РёРє cron-РґР¶РѕР± РїСЂРѕС‚РёРІ С‚РѕРіРѕ Р¶Рµ Albery (РІРµСЂСЃРёРѕРЅРЅР°СЏ С‡РµС…Р°СЂРґР° РѕС‚С‡С‘С‚РѕРІ вЂ” СЃРј. [agent.md:1621-1624](agent.md#L1621-L1624)).

**РђР»СЊС‚РµСЂРЅР°С‚РёРІР° В«РїРѕРїСЂРѕС‰РµВ» (1 РёРЅСЃС‚Р°РЅСЃ + soft-RBAC):** РѕСЃС‚Р°РІРёС‚СЊ РѕРґРёРЅ Hermes, РІ AI-РёРЅСЃС‚СЂСѓРєС†РёРё РІС€РёС‚СЊ В«РµСЃР»Рё `sender_tg_id в€€ {X, Y}` вЂ” РЅРµР»СЊР·СЏ `dispatch_*`, `send_bitrix_message`, `delete_bitrix_task`, `send_owner_recommendations_to_bitrix`В». Р”С‘С€РµРІРѕ, РЅРѕ **СЌС‚Рѕ РЅРµ Р±РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ** вЂ” РјРѕРґРµР»СЊ РјРѕР¶РµС‚ РїСЂРѕРёРіРЅРѕСЂРёСЂРѕРІР°С‚СЊ РїРѕСЃР»Рµ СЃР¶Р°С‚РёСЏ РєРѕРЅС‚РµРєСЃС‚Р°. Р“РѕРґРёС‚СЃСЏ РґР»СЏ UX-СЂР°Р·РґРµР»РµРЅРёСЏ В«РЅРµ РїРѕРєР°Р·С‹РІР°Р№ РјРµРЅРµРґР¶РµСЂСѓ owner-РєРѕРјР°РЅРґС‹В», РЅРµ РґР»СЏ Р·Р°С‰РёС‚С‹ РѕС‚ Р·Р»РѕРіРѕ СѓРјС‹СЃР»Р°.

### РћР±СѓС‡РµРЅРёРµ Hermes (РіРґРµ РїСЂР°РІРёС‚СЊ РїРѕРІРµРґРµРЅРёРµ, РїРѕ СѓР±С‹РІР°РЅРёСЋ СЃРёР»С‹)

| РЈСЂРѕРІРµРЅСЊ | РСЃС‚РѕС‡РЅРёРє РїСЂР°РІРґС‹ | РљС‚Рѕ С‡РёС‚Р°РµС‚ | Р”РµРїР»РѕР№ |
|---|---|---|---|
| РљРѕРЅС‚СЂР°РєС‚ РѕС‚С‡С‘С‚Р° (СЃС‚СЂСѓРєС‚СѓСЂР° СЃРµРєС†РёР№ + JSON-СЃС…РµРјР°) | Albery UI в†’ `РЎРІРѕРґРЅР°СЏ Р°РЅР°Р»РёС‚РёРєР° в†’ РќР°СЃС‚СЂРѕР№РєР° РїСЂРѕРјС‚РѕРІ` (`zoom_processing`, `owner_daily`) | Р’СЃРµ вЂ” Hermes, РІРЅРµС€РЅРёРµ Р°СЃСЃРёСЃС‚РµРЅС‚С‹ | РЎРѕС…СЂР°РЅРµРЅРёРµ РІ UI = live |
| AI-РёРЅСЃС‚СЂСѓРєС†РёРё (РїСЂР°РІРёР»Р° РїРѕРІРµРґРµРЅРёСЏ) | Albery UI в†’ `РќР°СЃС‚СЂРѕР№РєРё в†’ РРЅСЃС‚СЂСѓРєС†РёРё РґР»СЏ РР` + git: [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md) | Hermes С‡РµСЂРµР· `start_here_always_read_ai_instructions` РІ РЅР°С‡Р°Р»Рµ СЃРµСЃСЃРёРё | `python scripts/upsert_albery_ai_instruction.py <path> <file>` |
| Cron-РїСЂРѕРјРїС‚ (С‡С‚Рѕ РґРµР»Р°РµС‚ РѕРґРЅР° РґР¶РѕР±Р°) | git: [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt), [scripts/hermes_owner_daily_prompt.txt](scripts/hermes_owner_daily_prompt.txt) | РўРѕР»СЊРєРѕ СЌС‚Р° cron-РґР¶РѕР±Р° | `python scripts/update_hermes_*_prompt.py` в†’ restart gateway |
| РџР°РјСЏС‚СЊ Hermes (Р»РёС‡РЅС‹Рµ РїСЂРµРґРїРѕС‡С‚РµРЅРёСЏ) | `/root/.hermes/state.db` С‡РµСЂРµР· `hermes memory` РёР»Рё В«Р·Р°РїРѕРјРЅРё: вЂ¦В» РІ Telegram | Hermes РІРµР·РґРµ, РІ СЂР°РјРєР°С… РёРЅСЃС‚Р°РЅСЃР° | Live |

**РџСЂР°РІРёР»Рѕ Р±РѕР»СЊС€РѕРіРѕ РїР°Р»СЊС†Р°:** С‡С‚Рѕ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ Сѓ РІСЃРµС… (С„РѕСЂРјР°С‚ РѕС‚С‡С‘С‚Р°, СЃРѕСЃС‚Р°РІ РїСЏС‚С‘СЂРєРё, С‡С‚Рѕ СЃС‡РёС‚Р°С‚СЊ СЃСЂРѕС‡РЅС‹Рј) в†’ **РєРѕРЅС‚СЂР°РєС‚/AI-РёРЅСЃС‚СЂСѓРєС†РёРё РІ Albery**. Р§С‚Рѕ СЃРїРµС†РёС„РёС‡РЅРѕ РґР»СЏ РѕРґРЅРѕР№ cron-РґР¶РѕР±С‹ (cooldown, С„РѕСЂРјР°С‚ Telegram-СЃРІРѕРґРєРё) в†’ **cron-РїСЂРѕРјРїС‚ РІ git**. Р›РёС‡РЅС‹Рµ РїСЂРµРґРїРѕС‡С‚РµРЅРёСЏ РІР»Р°РґРµР»СЊС†Р° в†’ **`hermes memory`**.

**Р‘РѕР»РµРІР°СЏ С‚РѕС‡РєР°** РёР· СЂРµС‚СЂРѕ [agent.md:1545-1549](agent.md#L1545-L1549): РѕР±СѓС‡Р°С‚СЊ **Р¶С‘СЃС‚РєРёРјРё Р·Р°РїСЂРµС‚Р°РјРё** РІ AI-РёРЅСЃС‚СЂСѓРєС†РёРё, Р° РЅРµ СѓРіРѕРІРѕСЂР°РјРё. РџСЂРёРјРµСЂ РёР· [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md): В«РќР• РІС‹Р·С‹РІР°Р№ `create_bitrix_task` / РќР• С‡РёС‚Р°Р№ `get_org_structure`В» вЂ” СЌС‚Рѕ СЃРїР°СЃР»Рѕ Codex-Р»РёРјРёС‚. Р‘РµР· С‚Р°РєРёС… Р·Р°РїСЂРµС‚РѕРІ Hermes РёРґС‘С‚ РІ `search_files` Рё СЃР¶РёРіР°РµС‚ 100k С‚РѕРєРµРЅРѕРІ.



### Фикс падения Hermes `NameError: name 'event'` + команды `/accounts` `/limits` + авто-переприменение правок (29.05.2026)

**Симптом.** В Telegram-чате с Hermes любое сообщение (даже «Как меня зовут») падало с
`Sorry, I encountered an error (NameError). name 'event' is not defined`. В журнале
`journalctl -u hermes-gateway`:

```
File "/usr/local/lib/hermes-agent/gateway/run.py", line 17738, in _run_agent
    _event_text = (getattr(event, "text", "") or "").casefold()
NameError: name 'event' is not defined
```

**Причина.** В ручном патче «wall-clock task guard» ([agent.md:1718-1730](agent.md#L1718-L1730))
для классификации задачи (code/general) код обращался к переменной `event`, которой в
`_run_agent` нет — там текст сообщения лежит в параметре `message`.

**Фикс.** В `/usr/local/lib/hermes-agent/gateway/run.py`:
`_event_text = (getattr(event, "text", "") or "").casefold()` → `_event_text = (message or "").casefold()`.

#### Команды бота `/accounts` и `/limits`

Добавлены в `/usr/local/lib/hermes-agent/gateway/platforms/telegram.py`. Обрабатываются
**самим gateway напрямую** (перехват в `_handle_command` до вызова модели) — мгновенно и
**без траты токенов Codex**. Также добавлены в меню бота (`set_my_commands`).

Команда читает `/root/.hermes/auth.json` (+ `config.yaml` для стратегии failover) и выдаёт по
каждому аккаунту: активен/резерв, план (из JWT access_token), статус лимита, время сброса
(если упёрся в лимит), счётчик запросов. Пример:

```
🔑 Аккаунты Hermes

openai-codex — 2 шт., автопереключение: fill_first
  1. 🟢 активен — codex-bis.sdan21@gmail.com
     план: plus | лимит: ✅ свободен | запросов: 0
  2. ⚪ резерв — openai-codex-oauth-1
     план: plus | лимит: ✅ свободен | запросов: 0
```

Реальный остаток лимита ChatGPT нигде заранее не хранится — Hermes узнаёт его только когда
аккаунт упирается в лимит (тогда у credential заполняются `last_status` / `last_error_reset_at`,
и команда покажет `лимит: ⛔ … (сброс: …)`). Автопереключение (`fill_first`) включено через
`python scripts/hermes_codex_accounts.py --target new ensure-failover` — при исчерпании активного
аккаунта Hermes сам переходит на резервный.

#### Авто-переприменение правок («под ключ»)

`hermes update` перезаписывает `/usr/local/lib/hermes-agent` и стирает любые ручные патчи.
Чтобы это **никогда не теряло** фикс `event` и команды `/accounts`/`/limits`, настроено
самовосстановление:

- **Источник правды (в git):** [scripts/hermes_apply_patches.py](scripts/hermes_apply_patches.py) —
  идемпотентный скрипт. Переприменяет обе правки по якорям; пишет через temp + `py_compile` и
  атомарный `os.replace`, при любой ошибке откатывается и **никогда не ломает файл**; всегда
  завершается кодом 0 (не блокирует старт gateway). Если якоря в новой версии Hermes изменятся —
  печатает `SKIP (anchors changed)` и оставляет файл нетронутым (тогда патч переносится вручную).
- **На проде:** `/root/.hermes/patches/apply_patches.py` (права 700).
- **Запуск перед каждым стартом gateway:** systemd drop-in
  `/etc/systemd/system/hermes-gateway.service.d/10-reapply-patches.conf` →
  `ExecStartPre=/usr/local/lib/hermes-agent/venv/bin/python /root/.hermes/patches/apply_patches.py`.
  Любой `systemctl restart hermes-gateway` сам возвращает правки.
- **One-command обновление:** [scripts/hermes_update.sh](scripts/hermes_update.sh) (на проде
  `/root/.hermes/patches/update.sh`): `hermes update` → `daemon-reload` → `restart hermes-gateway`
  (триггерит переприменение) → проверка `is-active` + лог `hermes-reapply`.

Проверено 29.05.2026: восстановил оригинальный (непропатченный) `telegram.py` из бэкапа →
`systemctl restart hermes-gateway` → в логе `[hermes-reapply] telegram.py: accounts/limits re-applied`,
команды вернулись, gateway `active`.

**Как обновлять Hermes теперь:**

```bash
ssh root@217.198.12.236 'bash /root/.hermes/patches/update.sh'
# либо вручную: hermes update && systemctl restart hermes-gateway
```

**Обновить сами правки** (после изменения `scripts/hermes_apply_patches.py` в git): залить новый
файл в `/root/.hermes/patches/apply_patches.py` и `systemctl restart hermes-gateway`.

Бэкапы перед правками на проде: `run.py.bak.<ts>`, `telegram.py.bak.<ts>`.


### Локальный веб-интерфейс базы знаний agent-knowledge (29.05.2026)

Интерфейс, чтобы владелец сам добавлял/редактировал инструкции и скиллы Hermes в удобной
форме и заливал на сервер одной кнопкой. Только `agent-knowledge` (instructions + skills +
INDEX.md) — Albery, AI-конфиг агента и его память не затрагиваются.

- **Запуск:** двойной клик по [scripts/hermes-knowledge-ui.cmd](scripts/hermes-knowledge-ui.cmd)
  (или `python scripts/hermes_knowledge_ui.py`). Открывает `http://127.0.0.1:8765`.
- **Код:** [scripts/hermes_knowledge_ui.py](scripts/hermes_knowledge_ui.py) — чистый Python
  stdlib (без pip и npm), слушает только localhost.
- **Что делает:**
  - левая панель — `INDEX.md (маршрутизация)`, список инструкций, список скиллов;
  - редактор markdown со сплит-превью; кнопки «Сохранить», «Удалить»;
  - `+ добавить` инструкцию (файл `instructions/<имя>.md`) или скилл (папка
    `skills/<имя>/SKILL.md` с автогенерацией YAML-фронтматтера из имени и описания);
  - **«⬆ Залить на сервер»** — упаковывает локальный `agent-knowledge` в tar, кладёт через
    SFTP в `/root/.hermes/_kn_upload.tar`, на сервере бэкапит текущую базу в
    `agent-knowledge.bak`, затем `rm -rf agent-knowledge && tar -xf …` (сервер становится точной
    копией локального — удаления тоже применяются). Использует `_deploy_helper.connect("new")`.
- **Источник правды** — локальная папка `agent-knowledge/` в репозитории; заливка делает
  серверную `/root/.hermes/agent-knowledge` её точной копией.
- **Подхват изменений:** Hermes читает базу знаний по требованию (через `agent-knowledge/INDEX.md`),
  рестарт gateway не нужен. Чтобы новая инструкция «нашлась» — добавьте на неё строку в
  `## Routing` внутри `INDEX.md` (редактируется в том же интерфейсе).
- **Откат заливки:** на сервере `cd /root/.hermes && rm -rf agent-knowledge && mv agent-knowledge.bak agent-knowledge`.
