---
id: albery-server-context
type: project
project: albery
tags: [albery, server, mcp, runbook, reference]
updated: 2026-06-13
secret_refs: []
---

> Imported from the legacy `agent.md` (site repo). This file is the **lean orientation hub** for the
> Albery prod server. Heavy reference moved to focused docs (see the map below): infra, MCP-tools, sync.
> The VPN gateway and Hermes agent live in [vpn-gateway.md](vpn-gateway.md) and [hermes.md](hermes.md).
> Hosts: **Albery production runs on `186.246.7.32`** (verified by DNS 2026-06-11 — see [servers.md](servers.md)).
> `217.198.12.236` is a *separate* server (general Hermes Brain + andigital + Vault); it appears below only
> where a line is explicitly about that box (e.g. the brain/Vault store), never as the Albery host.

# Albery Server Context

## Current Operating Rules / Актуальный Контекст

This file is the first place to read in every new chat. It contains the current server context, deployment commands, webhook endpoints, cron schedule, and operational rules.

Server access (current project):

- Active server: `root@186.246.7.32` (dedicated Albery host; **not** the `217.198.12.236`/andigital box). Access creds live in the 217 Vault — see [servers.md](servers.md).
- Server project: `/var/www/albery`
- Hermes home: `/root/.hermes`
- Local project: `G:\OneDrive\Рабочий стол\Мои проекты\Сайт мой`
- SSH credentials are stored only in local `.env.local` as `Host_IP`, `Host_User`, `Host_Password`.
- Do not print, quote, commit, or pass passwords/tokens through command-line arguments.
- For automated server work, reach the Albery host `186.246.7.32` using the access in [servers.md](servers.md) (creds in the 217 Vault → sshpass jump). Caution: `_deploy_helper.py new` connects to `217.198.12.236` — that's the **other** (general) box, not Albery.
- If already inside the server shell, run commands directly without `ssh root@...`.
- Never commit `.env*`; secrets stay only in local/server env files.
- For this project use the Albery host `186.246.7.32`. Any `217.198.12.236` below refers to the separate general Hermes Brain / Vault box, not Albery.

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

## Подробности (разбито по темам, 2026-06-13)

Этот файл — хаб. Грузи только нужную часть, а не весь дослер:

| Документ | Что внутри |
|---|---|
| [server-infra.md](server-infra.md) | структура на сервере, запуск, systemd, nginx, HTTPS, PostgreSQL, env, деплой/обновление, frontend, бэкапы БД |
| [server-mcp-tools.md](server-mcp-tools.md) | недавние прод-изменения (вебхуки Bitrix/Zoom), FAQ MCP, Bitrix-инструменты, `fetch_url`, баг 120s таймаута, баг таймзон в title |
| [server-integrations-sync.md](server-integrations-sync.md) | почасовая синхронизация, Google Apps Script / Google Drive sync |

См. также [overview.md](overview.md), [hermes.md](hermes.md), [vpn-gateway.md](vpn-gateway.md).
