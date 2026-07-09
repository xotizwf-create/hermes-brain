---
id: prostye-postavki-deploy
type: project
project: prostye-postavki
tags: [deploy]
updated: 2026-07-09
secret_refs: [proj/prostye-postavki/server/env]
---

# Простые поставки — deploy

> Treat production as critical.

## Current rule
Do not deploy blindly. Production code lives in `/var/www/prostye-postavki/app` and must stay synchronized with GitHub repo `xotizwf-create/prostavki`. First run the universal server preflight, inspect the working tree, commit/push source changes, then verify service health.

## ⚠ Production branch (verified 2026-07-09)
Прод стоит на ветке **`fix/incoming-paste-single-cell`**, НЕ на `main` и НЕ на `Создание-документов`.
Перед деплоем всегда `git rev-parse --abbrev-ref HEAD` на проде; фичи мержить В эту ветку и пушить,
потом на проде `git pull --ff-only origin fix/incoming-paste-single-cell`. (2026-07-09 деплой падал
именно из-за этого: пуш ушёл в Создание-документов, а прод — на fix-ветке с 4 своими коммитами.)

## Working deploy path (proven 2026-07-09)
Прямого SSH с ПК на сервер проекта нет. Рабочая схема — через 217 как jump-host:
1. Креды сервера лежат в secure-зоне 217: `/opt/hermes/secure/projects/prostye-postavki/.env`
   (IP/USER/PASSWORD; на 2026-07-09 IP = 5.129.202.216, miramed32.ru). Никогда не печатать.
2. Скрипт деплоя (запускается НА сервере проекта): git fetch/pull --ff-only ветки прода →
   `py_compile` main.py/mcp_prompts.py/contract_templates.py → смоук-тест движка →
   `systemctl restart prostye-backend` → health 200 на `/api/health` → live MCP проверки
   (tools/list содержит новые тулы, prompts отдаются, list-тул создаёт схему БД).
3. Раннер на 217 читает креды в память и гонит скрипт через sshpass (`bash /tmp/pp_run.sh`
   образец; сами скрипты — одноразовые, класть в /tmp).
4. Заливка файлов на 217: `python _deploy_helper.py new --writeb64 /tmp/<name> <local>` из репо «Сайт мой».
Box: 2 GB RAM + 2 GB swap — лёгкий git-pull деплой ок, сборки/тесты тяжелее смоука не гонять.

## After deploy: Hermes на 217
Новые MCP-тулы Hermes подхватывает только при рестарте гейтвея: убедиться что журнал тихий →
`systemctl restart hermes-gateway` → проверить `hermes mcp test prostye_postavki` (список тулов).

## Flow draft
1. Confirm scope and rollback plan.
2. Inspect resources and live services with `engineering/server-preflight.md`.
3. Build/test off production when possible.
4. Upload or pull only a verified release.
5. Restart/switch atomically if the service layout supports it.
6. Run a read-only smoke check: web availability, MCP availability, database connectivity without exposing secrets.

## Git synchronization rule
- The production working tree must be clean after any change: no uncommitted edits and no stray temporary backup files.
- Commit production code changes to `xotizwf-create/prostavki` and keep `main` fast-forwarded to the production commit.
- Never leave a hotfix only on the server. If a change is deployed or tested in production, finish by pushing the exact tracked code to GitHub and verifying GitHub `main` points to the same commit as the production checkout.

## Post-deploy checks
- Application opens.
- MCP server responds to safe/read-only tool discovery.
- Contract/product/КП flows are not broken.
- Logs show no new errors.

## Rollback
Уточнить после документирования текущего способа деплоя и расположения релизов.
