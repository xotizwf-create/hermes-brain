---
id: albery-server-context
type: project
project: albery
tags: [albery, server, nginx, systemd, postgres, mcp, reference]
updated: 2026-05-30
secret_refs: []
---

> Imported from the legacy `agent.md` (site repo). Operational reference for the albery prod
> server (nginx, systemd, HTTPS, Postgres, env, sync cron, backups) and the Albery MCP-tools.
> The VPN gateway and the Hermes agent were split into [vpn-gateway.md](vpn-gateway.md) and
> [hermes.md](hermes.md). The curated docs (overview/servers/deploy/runbook) are the summary.
> Note: older sections reference the historical server `186.246.7.32`; current prod is `217.198.12.236`.
# Albery Server Context

## Current Operating Rules / Актуальный Контекст

This file is the first place to read in every new chat. It contains the current server context, deployment commands, webhook endpoints, cron schedule, and operational rules.

Server access (current project):

- Active server: `root@217.198.12.236` (`andigital`).
- Server project: `/var/www/albery`
- Hermes home: `/root/.hermes`
- Local project: `G:\OneDrive\Рабочий стол\Мои проекты\Сайт мой`
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

Этот файл фиксирует рабочий контекст проекта, чтобы в новом чате сразу было понятно, где что лежит и какими командами обслуживать сервер.

## Git Branch Workflow / Правила Работы С Ветками

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

## Репозиторий

- GitHub: `https://github.com/xotizwf-create/Albery.git`
- Основная ветка: `main`
- Локальный проект Windows: `G:\OneDrive\Рабочий стол\Мои проекты\Евгений. Разработка`
- Серверный проект: `/var/www/albery`

## Сервер

- IP: `186.246.7.32`
- Пользователь: `root`
- ОС: Ubuntu 22.04
- Основной домен: `m4s.ru`
- Канонический web-домен: `www.m4s.ru`
- MCP-домен: `mcp.m4s.ru`

DNS-записи:

```text
A  @    186.246.7.32
A  www  186.246.7.32
A  mcp  186.246.7.32
```

Проверка DNS:

```bash
dig +short m4s.ru
dig +short www.m4s.ru
dig +short mcp.m4s.ru
```

## Структура На Сервере

```text
/var/www/albery/                  проект
/var/www/albery/.env              production env, не хранится в git
/var/www/albery/.venv/            Python venv
/var/www/albery/run_5002.py       запуск Flask на 127.0.0.1:5002
/var/www/albery/Интерфейс/        React/Vite frontend
/var/www/albery/Интерфейс/dist/   собранный frontend
/var/www/albery/scripts/          служебные скрипты
/var/backups/albery/postgres/     бэкапы PostgreSQL
/etc/systemd/system/albery.service systemd service
/etc/nginx/sites-available/albery Nginx site config
/etc/cron.d/albery-postgres-backup cron автобэкапа БД
```

## Запуск Приложения

Backend слушает только локально:

```text
127.0.0.1:5002
```

Публичный доступ идет через Nginx reverse proxy:

```text
https://www.m4s.ru -> http://127.0.0.1:5002
https://mcp.m4s.ru -> http://127.0.0.1:5002
```

Главная страница приложения:

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

Сервис:

```bash
systemctl status albery --no-pager
systemctl restart albery
journalctl -u albery -n 120 --no-pager
```

Содержимое `/etc/systemd/system/albery.service`:

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

После изменения:

```bash
systemctl daemon-reload
systemctl enable --now albery
systemctl restart albery
```

## Nginx

Проверка:

```bash
nginx -t
systemctl reload nginx
tail -n 120 /var/log/nginx/error.log
```

Важные настройки:

- HTTP и IP должны редиректить на `https://www.m4s.ru`
- `m4s.ru` должен редиректить на `www.m4s.ru`
- `mcp.m4s.ru` остается отдельным хостом для MCP
- Для долгих Google Drive sync нужны proxy timeout `600s`

Рекомендуемый `/etc/nginx/sites-available/albery`:

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

Применение:

```bash
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/albery /etc/nginx/sites-enabled/albery
nginx -t && systemctl reload nginx
```

## HTTPS

Сертификат Let's Encrypt выпущен на:

```text
m4s.ru
www.m4s.ru
mcp.m4s.ru
```

Команды:

```bash
certbot certificates
certbot renew --dry-run
```

Если нужно перевыпустить:

```bash
certbot --nginx -d m4s.ru -d www.m4s.ru -d mcp.m4s.ru
```

## PostgreSQL

- БД: `albery`
- Пользователь БД: `albery_app`
- Пароль хранится только в `/var/www/albery/.env`

Проверка подключения:

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

Применить схему/миграции:

```bash
cd /var/www/albery
.venv/bin/python scripts/ensure_postgres.py
```

## Env

Открыть production env:

```bash
nano /var/www/albery/.env
```

Важные переменные:

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

Не вставлять реальные секреты в git или чат. `.env` исключен через `.gitignore`.

Сгенерировать hash пароля админки:

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

## Автоматическая Почасовая Синхронизация

Почасовая синхронизация ставится отдельным cron-файлом:

```text
/etc/cron.d/albery-daily-sync
```

Время запуска:

```text
каждый час в 00 минут по Europe/Moscow
```

Установить или обновить cron:

```bash
cd /var/www/albery && ./scripts/install_daily_sync_cron.sh
```

Запустить вручную:

```bash
cd /var/www/albery
ALBERY_LOG_DIR=/var/log/albery ALBERY_DAILY_SYNC_LOG=/var/log/albery/daily-sync.log .venv/bin/python scripts/run_daily_sync.py
```

Что запускает `scripts/run_daily_sync.py`:

- `bitrix_team` - синхронизация сотрудников Bitrix
- `bitrix_tasks` - синхронизация Bitrix-задач за период
- `bitrix_chat_messages` - синхронизация списка чатов и сообщений
- `zoom_api_calls` - синхронизация Zoom-созвонов через Zoom API
- `google_drive_company_instructions` - подтягивание Google Drive документов/инструкций в раздел "О компании"
- `google_drive_zoom_transcripts` - подтягивание `transcript.txt` из Google Drive для Zoom, если включено

Логи:

```text
/var/log/albery/daily-sync.log       структурированный JSONL-лог каждого шага
/var/log/albery/daily-sync.cron.log  stdout/stderr cron-обертки
```

Смотреть логи:

```bash
tail -n 200 /var/log/albery/daily-sync.log
tail -n 200 /var/log/albery/daily-sync.cron.log
grep '"status": "failed"' /var/log/albery/daily-sync.log
```

Настройки в `.env`:

```env
AUTO_SYNC_BITRIX_LOOKBACK_DAYS=30
AUTO_SYNC_CHAT_LOOKBACK_DAYS=1
AUTO_SYNC_CHAT_GENERATE_REPORTS=0
AUTO_SYNC_ZOOM_FROM=2026-01-01
AUTO_SYNC_ZOOM_TO=
AUTO_SYNC_GOOGLE_DRIVE_ZOOM_TRANSCRIPTS=1
```

Если нужно, чтобы при вечерней синхронизации сразу формировались дневные отчеты по чатам:

```env
AUTO_SYNC_CHAT_GENERATE_REPORTS=1
```

## Деплой И Обновление

Основная команда обновления сервера:

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

Что делает `scripts/update_server.sh`:

- `git fetch` и `git pull --ff-only origin main`
- создает `.venv`, если его нет
- обновляет `pip`
- ставит `requirements.txt`
- применяет PostgreSQL migrations через `scripts/ensure_postgres.py`
- находит frontend `package.json`
- делает `npm ci`
- делает `npm run build`
- перезапускает `albery`
- ждет доступности `http://127.0.0.1:5002`

Если после деплоя проблема:

```bash
systemctl status albery --no-pager
journalctl -u albery -n 120 --no-pager
curl -I http://127.0.0.1:5002
```

## Google Apps Script (Google Drive company sync)

Код Apps Script, который отдаёт документы и дерево папок из Google Drive,
лежит в репозитории и деплоится через `clasp` (а НЕ через `update_server.sh`).

- Проект: `scripts/google_drive_company_sync_project/` (`Code.gs`, `appsscript.json`)
- `.clasp.json` в корне: `scriptId = 1ga97W3bs386A00JokAHZyiQffEC1fFFjOoyzJm5GXUYkKjd3aXiRUoO9`
- Логин clasp: владелец скрипта `xotizwf@gmail.com` (`clasp show-authorized-user`)
- Прод web app deployment (это и есть `/exec` в `GOOGLE_APPS_SCRIPT_SYNC_URL`):
  - deploymentId = `AKfycbwsEL8z_HAoNmLP9utV4HCtkNDAcgbaAxnWsZ1Njs7h4L6DcrmRzcehzxB1y070CarBgA`
  - `/exec` URL = `https://script.google.com/macros/s/<deploymentId>/exec`

Обновление кода Apps Script (обновляет существующий `/exec`, URL не меняется):

```bash
clasp push --force
clasp redeploy AKfycbwsEL8z_HAoNmLP9utV4HCtkNDAcgbaAxnWsZ1Njs7h4L6DcrmRzcehzxB1y070CarBgA -d "что изменилось"
clasp deployments   # проверить активную версию
```

ВАЖНО — почему раньше `/exec` отдавал 404 после CLI-деплоя:

- Используйте `clasp redeploy <deploymentId>` (обновление на месте), а не
  `clasp deploy` (создаёт НОВЫЙ deployment с другим URL).
- В `appsscript.json` обязан быть блок `webapp`, иначе clasp создаёт версию
  без web app entry point и `/exec` отдаёт 404:

  ```json
  "webapp": { "executeAs": "USER_DEPLOYING", "access": "ANYONE_ANONYMOUS" }
  ```

Проверка, что `/exec` живой (должен вернуть JSON `{"ok": true, ...}`, не HTML):

```bash
token=$(awk -F= '$1=="GOOGLE_APPS_SCRIPT_SYNC_TOKEN"{print $2; exit}' .env)
url=$(awk -F= '$1=="GOOGLE_APPS_SCRIPT_SYNC_URL"{sub(/^[^=]*=/,""); print; exit}' .env)
curl -sS -L "$url?token=$token" | head -c 200
```

Логика синхронизации (инкрементально, без перезаписи неизменных файлов):

- сервер шлёт в Apps Script `known_files`/`known_folders` (id, имя, `updated_at`,
  `parent_folder_id`, `path`); скрипт по ним помечает неизменные файлы
  `unchanged: true` и НЕ выгружает их контент (DOC/XLS не конвертируются заново);
- сервер обновляет `company_folders` только при реальном изменении
  (сравнение `content_hash`, пути, родителя), иначе только `last_seen_at`;
- структура Google Drive зеркалится: папки -> `company_drive_folders` +
  `company_folders`, документы кладутся внутрь своих папок;
- временный сбой конвертации (`document_errors`, напр. Drive rate limit) НЕ
  удаляет уже синхронизированный документ — он подтянется на следующем прогоне.

Запустить серверную синхронизацию вручную:

```bash
cd /var/www/albery
.venv/bin/python - <<'PY'
from dotenv import load_dotenv; load_dotenv("/var/www/albery/.env")
import app, json
print(json.dumps(app.sync_google_drive_company_documents(), ensure_ascii=False, default=str)[:600])
PY
```

Авто-обновление по триггеру (near-realtime, ~1 минута):

- В Apps Script стоит time-driven триггер `checkDriveChangesAndNotify`
  (раз в минуту). Он считает лёгкую сигнатуру дерева папки (id, время правки,
  имена, родители; БЕЗ контента) и пингует сервер ТОЛЬКО при реальном изменении.
- Сервер: вебхук `POST /google-drive/events/<GOOGLE_DRIVE_EVENT_SECRET>` запускает
  ту же инкрементальную синхронизацию под Postgres advisory-lock (не пересекается
  с почасовым cron / ручной кнопкой; если занято — 409, триггер повторит).
- Секрет: `.env` `GOOGLE_DRIVE_EVENT_SECRET` == `CHANGE_NOTIFY_URL` в `Code.gs`.
- Триггер создаётся ОДИН раз вручную: открыть редактор скрипта, выбрать функцию
  `setupDriveChangeTrigger`, нажать Run, пройти авторизацию (нужны scope
  `script.scriptapp` и `drive`). Повторный запуск безопасен (старые триггеры
  удаляются). Снять триггер: запустить `removeDriveChangeTriggers`.
- Проверка вебхука: `curl https://mcp.m4s.ru/google-drive/events/<secret>` -> JSON
  `{"ok": true, ...}`; `POST` туда же запускает синхронизацию и возвращает result.
- Триггеры в Apps Script: https://script.google.com/home/triggers

## Frontend

Папка:

```bash
/var/www/albery/Интерфейс
```

Команды:

```bash
cd /var/www/albery/Интерфейс
npm ci
npm run build
```

Node.js должен быть современный. На сервере ставился Node 20 через NodeSource, потому что Ubuntu apt давал Node 12, а Vite требует Node >=18.

## Бэкапы БД

Автоматический ежедневный бэкап установлен:

```text
/etc/cron.d/albery-postgres-backup
```

Скрипты:

```text
scripts/backup_postgres.sh
scripts/restore_postgres.sh
scripts/install_backup_cron.sh
```

Папка бэкапов:

```bash
/var/backups/albery/postgres/
```

Ручной бэкап:

```bash
cd /var/www/albery && ./scripts/backup_postgres.sh
```

Установить/обновить cron:

```bash
cd /var/www/albery && ./scripts/install_backup_cron.sh
```

Восстановить custom dump:

```bash
cd /var/www/albery
./scripts/restore_postgres.sh /var/backups/albery/postgres/file.dump
systemctl restart albery
```

Восстановить plain SQL:

```bash
cd /var/www/albery
./scripts/backup_postgres.sh
DATABASE_URL=$(awk -F= '$1=="DATABASE_URL"{sub(/^[^=]*=/,""); print; exit}' .env)
psql "$DATABASE_URL" < /var/backups/albery/postgres/file.sql
.venv/bin/python scripts/ensure_postgres.py
systemctl restart albery
```

Сделать локальный SQL-бэкап на Windows:

```powershell
cd "G:\OneDrive\Рабочий стол\Мои проекты\Евгений. Разработка"
$envLine = Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
$DATABASE_URL = $envLine -replace '^DATABASE_URL=', ''
& 'C:\Program Files\PostgreSQL\18\bin\pg_dump.exe' --format=plain --no-owner --no-acl --clean --if-exists --file .\backups\albery_local.sql $DATABASE_URL
```

Загрузить локальный SQL на сервер:

```powershell
scp .\backups\albery_local.sql root@186.246.7.32:/var/backups/albery/postgres/albery_local.sql
```

## Известные Исправления

- Flask отдает frontend из `Интерфейс/dist`.
- `/` редиректит на `/main`.
- `/main` защищен паролем.
- Сессия админки хранится в signed cookie Flask.
- Пароль админки хранится hash-строкой `ADMIN_PASSWORD_HASH`.
- `CANONICAL_WEB_HOST=www.m4s.ru` редиректит web-трафик на `www`.
- MCP остается доступен через `mcp.m4s.ru` и `MCP_SHARED_SECRET`.
- Google Drive sync требует увеличенных таймаутов: frontend/backend/Nginx по 600 секунд.
- PDF-отчеты Bitrix на Linux требуют шрифты:

```bash
apt install -y fonts-dejavu-core fonts-liberation
```

## Частые Команды

Обновить код и перезапустить:

```bash
cd /var/www/albery && ./scripts/update_server.sh
```

Открыть env:

```bash
nano /var/www/albery/.env
```

Проверить backend:

```bash
curl -I http://127.0.0.1:5002
```

Проверить публичные домены:

```bash
curl -I https://www.m4s.ru
curl -I https://mcp.m4s.ru
```

Проверить логи:

```bash
journalctl -u albery -n 120 --no-pager
tail -n 120 /var/log/nginx/error.log
```

Перезапустить сервисы:

```bash
systemctl restart albery
nginx -t && systemctl reload nginx
```


## Moved out of this file

Two big subsystems were extracted into focused docs (kept this file as the Albery app/server + MCP-tools reference):

- VPN gateway (AmneziaWG, outbound-via-Estonia) → [vpn-gateway.md](vpn-gateway.md)
- Hermes agent (setup, Codex provider, cron, Telegram, sessions, training) → [hermes.md](hermes.md)

### Bitrix-инструменты в MCP

В MCP Albery доступны инструменты:

- `create_bitrix_task` — создаёт одну задачу в Bitrix (разовую или периодическую,
  с наблюдателями опционально). Агент обязан собрать и показать человеку перед
  созданием: ответственный, дедлайн, проверяемый результат, финальный человеческий
  текст задачи, полный список наблюдателей (если есть), и расписание (если
  периодическая). Если чего-то нет — уточнять до конца, не создавать. **Расширен
  28.05.2026** — три новых параметра:
  - `auditor_names: list[str]` / `auditor_bitrix_user_ids: list[int]` — наблюдатели
    из активной оргструктуры (`users.is_active=TRUE`). Резолвинг через новый хелпер
    `_resolve_active_bitrix_users` ([mcp/context_server.py](mcp/context_server.py)):
    fuzzy-match по `_person_names_match`, неоднозначность → отказ + список кандидатов
    с `bitrix_user_id`/`full_name`/`work_position`. Списки объединяются и
    дедуплицируются. На Bitrix уходит как `fields.AUDITORS = [int]`.
  - `periodic: {type, interval?, weekdays?, day_of_month?, daily_mode?, until?}` —
    расписание. Если присутствует, задача создаётся как `IS_REGULAR=Y` +
    `REGULAR_PARAMETERS` (через `_build_bitrix_regular_parameters`). Поддержка:
    - `type="daily"` + `daily_mode="all"|"workdays"` (default `all`) → `REPEAT_TYPE=daily`, `DAILY_MODE`;
    - `type="weekly"` + `weekdays=["MO","WE","FR"]` + `interval` → `REPEAT_TYPE=weekly`, `REPEAT_WEEKDAYS`, `REPEAT_EVERY`;
    - `type="monthly"` + `day_of_month=1-31` + `interval` → `REPEAT_TYPE=monthlydays`, `REPEAT_MONTHDAY`, `REPEAT_EVERY`;
    - опциональный `until="YYYY-MM-DD"` → `REPEAT_TILL`.
    Невалидные комбинации (нет `type`, weekly без `weekdays`, monthly без
    `day_of_month`, кривой weekday-код, `interval<1`, кривой `until`) → инструмент
    отказывает с понятным сообщением.
  Schema-валидация в `inputSchema` дополнительно ограничивает enum'ы. MCP server
  version поднят до `0.6.0`.
- `delete_bitrix_task` — удаляет одну задачу в Bitrix. Жёсткое правило:
  сначала `search_tasks(bitrix_task_id=...)`, затем показать пользователю точную
  задачу (номер, название, статус, ответственный, дедлайн) и спросить подтверждение.
  Только после явного подтверждения можно вызвать
  `delete_bitrix_task(bitrix_task_id=..., confirm=true)`. Нельзя удалять по названию,
  поисковому тексту или неоднозначной ссылке. В инструменте есть дополнительная
  защита: без `confirm=true` он откажет, а `expected_title` можно использовать как
  safety-check от удаления не той задачи.
- `list_pending_owner_recommendations(report_date)` — возвращает сохранённые
  черновики рекомендаций из `owner_manager_recommendations` за указанный день
  (только текущая версия отчёта, только статусы `new/queued`, только записи с
  `manager_bitrix_user_id IS NOT NULL`). Вместе с черновиками отдаёт поля отчёта:
  `report_summary`, `report_dynamics_summary`, `report_risks_summary`,
  `report_text`. Используется Hermes-агентом в Telegram-сессии после ответа
  владельца «отправляй», чтобы собрать `recipient_recommendations` под отправку.
- `send_owner_recommendations_to_bitrix(report_date, recipient_recommendations, confirm=true)`
  — шлёт каждому получателю один личный текст в Битрикс через `im.message.add`
  с fallback на `im.notify.personal.add`. `confirm=true` обязателен — без него
  инструмент отказывает. Параметр `recipient_recommendations` — это словарь
  `{bitrix_user_id: text}`; текст отправляется как есть, без редактирования. Под
  капотом — `send_owner_report_recommendations_to_bitrix` из `app.py`, который
  пишет каждую отправку в `owner_recommendation_dispatches` (channel `bitrix_im`
  / `bitrix_notification`), переводит соответствующие `owner_manager_recommendations`
  в `status='sent'` и пишет `sent`-событие в `owner_recommendation_events`.
- `cancel_owner_recommendation(recommendation_id, reason?)` — помечает одну
  запись `owner_manager_recommendations` как `cancelled`, фиксирует событие
  `cancelled` в `owner_recommendation_events`. Используется на «не отправляй»
  или «правки по <имя>: …» (старый черновик отменяется, новый формируется).
- `save_owner_daily_report` — **расширен 28.05.2026**: теперь принимает поле
  `manager_messages` (массив объектов со структурой
  `{manager_name, manager_bitrix_user_id, priority, message_type, subject, message_text, due, topics}`),
  и после INSERT в `owner_daily_reports` сразу вызывает
  `save_owner_daily_manager_messages` (в `app.py`) — он наполняет
  `owner_manager_recommendations` строкой на каждый объект из `manager_messages`.
  Без `manager_messages` инструмент работает как раньше (только сам отчёт).
- `list_pending_zoom_operational_dispatches(date_from?, date_to?)` — **добавлен 28.05.2026**:
  возвращает Zoom-созвоны с сохранённым `analytical_note`, по которым ещё не
  созданы агрегированные «Итоги созвона» задачи в Битрикс. **Default период —
  только сегодня (Europe/Moscow)** — это страховка от случайной отправки старых
  непереданных созвонов на ответ «ставь»; за прошлые дни нужно передать
  `date_from` явно. Hermes использует это как первый шаг Phase 2 zoom-to-tasks.
- `preview_zoom_operational_tasks(call_id)` — **добавлен 28.05.2026**: показывает
  что будет создано в Битрикс БЕЗ отправки. Возвращает `title` («Итоги созвона
  ЧЧ:ММ»), per-recipient `task_cards` (одна карточка = одна агрегированная
  задача), `deadline` (дата созвона 19:00 МСК), стандартное `description`.
  Полезен для отладки; в обычном flow Hermes этот инструмент не дёргает —
  идёт сразу к `dispatch_zoom_operational_tasks`.
- `dispatch_zoom_operational_tasks(call_id, confirm=true)` — **добавлен
  28.05.2026**: создаёт агрегированные Bitrix-задачи «Итоги созвона ЧЧ:ММ» —
  одна задача на каждого ответственного из `operational_tasks` сохранённого
  отчёта. Дедлайн = call_date 19:00 МСК. Описание = `ZOOM_OPERATIONAL_TASKS_DISPATCH_INTRO` +
  список задач этого человека. Внутри использует тот же
  `build_zoom_operational_task_cards` + `dispatch_prepared_zoom_operational_tasks`,
  что и Flask endpoint UI-кнопки «Отправка задач», поэтому формат идентичен.
  После успеха записывает `zoom_calls.raw_json.ai_report.bitrix_dispatch` (timestamp
  + созданные task_ids) — `list_pending_zoom_operational_dispatches` больше его
  не вернёт. Требует `confirm=true`. **НЕЛЬЗЯ заменять на серию
  `create_bitrix_task`** — это создаст много мелких задач вместо одной агрегированной.
- `send_bitrix_message(recipient_bitrix_user_id?, recipient_name?, message_text, confirm)` —
  **добавлен 28.05.2026**: отправляет одно личное сообщение в Bitrix любому
  активному сотруднику от моего пользователя (через `BITRIX_WEBHOOK_BASE`,
  отдельного бота пока нет). Под капотом — `send_bitrix_personal_message` в
  [app.py](app.py): `im.message.add` с fallback на `im.notify.personal.add` при
  `ERROR_NO_ACCESS`. Получатель резолвится через `_resolve_message_recipient` в
  [mcp/context_server.py](mcp/context_server.py) — приоритет у
  `recipient_bitrix_user_id` (точный integer); если передано только
  `recipient_name`, делается fuzzy-match по активным `users` (через
  `_person_names_match`), и при неоднозначности инструмент отказывает и возвращает
  кандидатов. `confirm=true` обязателен — Hermes должен сначала показать владельцу
  итоговый `message_text` + `full_name`/`work_position`/`bitrix_user_id` получателя
  и получить явное «отправляй». `message_text` уходит как есть, без редактирования
  и без подписей. Это **общий** инструмент для сценариев «напиши <имя> в Битрикс:
  …» из Telegram-чата с Hermes или любой ИИ через коннектор — НЕ путать с
  `send_owner_recommendations_to_bitrix` (тот строго привязан к
  `owner_daily_reports.manager_messages` и работает только в Phase 2 owner-daily).
  MCP server version поднят до `0.5.0` (`hermes mcp test albery` должен показывать
  45 инструментов).


### MCP-инструмент `fetch_url` (добавлено 28.05.2026)

**Зачем.** В Hermes для Telegram-платформы отключены встроенные `web`/`browser` toolset'ы ([agent.md:1538-1543](agent.md#L1538-L1543)) — после инцидента 28.05 с раздутой сессией на 100k токенов. Поэтому Hermes не мог открывать ссылки из чата (Google Sheets/Docs, статьи, регламенты). Включать `web` обратно опасно — одна большая страница съест полконтекста Codex.

**Решение.** Отдельный MCP-инструмент `fetch_url(url, max_chars?, strip_html?)`:
- **Google Sheets** URL (`docs.google.com/spreadsheets/d/<id>/edit?gid=<n>`) автоматически переписывается в `/export?format=csv&gid=<n>` → возвращается чистый CSV.
- **Google Docs** URL (`docs.google.com/document/d/<id>/...`) → `/export?format=txt`.
- Прочие URL: HTTP GET + `User-Agent: AlberyMCP/0.7`, по умолчанию HTML-теги срезаются до текста, скрипты/стили выкидываются.
- **Size cap:** default `max_chars=50000`, max 200000. Это ~12k токенов на ответ — не съедает контекст.
- На HTTP 401/403 для Google-документов в ответ добавляется `hint`: «Откройте доступ "Любой, у кого есть ссылка — Просмотр" либо положите файл в Drive-папку, которую читает Albery через Apps Script (`list_company_files` / `search_company_knowledge` / `get_company_file`)».

Когда **НЕ** использовать `fetch_url`: для знаний, которые уже синхронизированы в Albery (регламенты, инструкции, Zoom-расшифровки, чаты) — там быстрее и точнее работают `search_company_knowledge`, `list_company_files`, `get_company_file`, `search_messages`, `get_zoom_call_transcript`.

**Проверено на реальном Google Sheet** (28.05.2026, `17NZP5U5YBQPKKQrBUGq05bpTjq2V-KBX98uM1Wa2W_4`): 0.82с, HTTP 200, 6103 символа CSV, не truncated. Распарсилось как 40 строк × 7 колонок.

**Версия MCP** поднята до `0.7.0`, инструментов 46. Коммит `92c7391`.

**Flow в Telegram после /reset:** «Прочитай таблицу <ссылка> и создай задачи в Битриксе» → Hermes сам зовёт `fetch_url(...)` → парсит CSV → резолвит ФИО исполнителей/наблюдателей через `_resolve_active_bitrix_user(s)` → показывает план → ждёт «создавай» → циклом `create_bitrix_task` на каждую строку (с `auditor_names`, `periodic` если есть).

### Известный баг: 120s таймаут `create_bitrix_task` / `delete_bitrix_task` (исправлено 28.05.2026)

**Симптом.** Hermes в Telegram отвечал: «Не удалось создать задачу» или «MCP call timed out after 120.0s». В журнале `journalctl -u hermes-gateway`:

```
ERROR tools.mcp_tool: MCP tool albery/create_bitrix_task call failed:
MCP call timed out after 120.0s (configured timeout: 120.0s)
```

**Корневая причина.** В Albery жили **две разные реализации Bitrix-клиента**:
- `BitrixClient` в [app.py:14246](app.py#L14246) — на `requests.Session`, кэш, retry. **Быстрый**, < 2s. Используют `send_bitrix_message`, `dispatch_zoom_operational_tasks`, `send_owner_recommendations_to_bitrix`.
- `_bitrix_call_with_fallback` в [mcp/context_server.py](mcp/context_server.py) — на голом `urllib.request.urlopen(timeout=60)`. **Зависал ровно 120с** (30 минут, `delete_bitrix_task`.

Hermes-side MCP-клиент имеет свой ceiling 120s → urllib доходил до 120s раньше, чем что-либо ответил → Hermes ловил `MCP call timed out`, а никакая задача в Bitrix не создавалась.

Дополнительно у `delete_bitrix_task` был **SQL-баг**: JOIN на несуществующую колонку `bitrix_tasks.responsible_user_id` (на самом деле колонка зовётся `responsible_id`) → каждый вызов падал с `psycopg.errors.UndefinedColumn` ещё до обращения в Bitrix.

**Фикс.**
1. В [app.py](app.py) добавлен workflow `bitrix_method_call(method, payload, prefer_api=True)` — тонкая обёртка над `BitrixClient.call_with_fallback`. Доступен через `app_workflow_function("bitrix_method_call")`.
2. `_bitrix_call_with_fallback` в [mcp/context_server.py](mcp/context_server.py) свёрнут до 8 строк — делегирует в `bitrix_method_call`. Голый urllib выпилен.
3. SQL в `tool_delete_bitrix_task` поправлен: `responsible_user_id` → `responsible_id`.

После фикса замеры на проде (с реальным Bitrix через VPN-Эстонию):
- Разовая задача: **1.02s**
- Задача с наблюдателями (1 человек): **0.67s**
- Периодическая weekly с `IS_REGULAR=Y`: **0.72s** (Bitrix-портал принимает `REGULAR_PARAMETERS` ровно в нашем формате)

Версия MCP поднята до `0.6.1`. Коммиты: `db0c4e0` (urllib → BitrixClient), `90109e1` (SQL fix).

**Правило на будущее.** Любой новый MCP-инструмент, дёргающий Bitrix API, обязан идти через `app_workflow_function("bitrix_method_call")` (или прямо `BitrixClient` в самом app.py). Не делать собственные urllib-обёртки — это уже один раз привело к 120с таймауту в проде.

### Известная гран. ситуация: time-зоны в title «Итоги созвона ЧЧ:ММ»

В Postgres колонка `zoom_calls.start_time_msk` фактически хранится как UTC
(`timestamptz`), несмотря на название с `_msk`. Конверсия в МСК делается на
runtime через `astimezone(MSK_TZ)`. Это работает корректно в happy-path
(`zoom_call_row_payload` precomputed-ит `time_text` как `"09:28 - 10:26"` уже
в МСК). Но **fallback-пути** (когда `time_text` пустой) когда-то брали `str(start_time_msk)` напрямую — выдавали
ISO с `+00:00` и в title вылезало UTC время (например `"Итоги созвона 06:28"`
вместо МСК `09:28`).

Зафиксировано 28.05.2026:
- backend `build_zoom_operational_tasks_dispatch` ([app.py:3601-3611](app.py#L3601-L3611)) теперь конвертит fallback через `parse_datetime(...).astimezone(MSK_TZ).strftime('%H:%M')`;
- frontend `buildLocalZoomOperationalPreview` ([Интерфейс/src/App.tsx:4110-4124](Интерфейс/src/App.tsx#L4110-L4124)) использует `Date.toLocaleTimeString({timeZone: 'Europe/Moscow'})`.

Если в будущем появится новый код, формирующий «Итоги созвона …» из ISO-строки — обязательно конвертировать в МСК. Прямой использовать `str(call.start_time_msk)` нельзя.

