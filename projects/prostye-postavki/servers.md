---
id: prostye-postavki-servers
type: project
project: prostye-postavki
tags: [servers, access]
updated: 2026-07-09
secret_refs: [proj/prostye-postavki/server/env, proj/prostye-postavki/ssh/root, proj/prostye-postavki/mcp/token]
---

# Простые поставки — servers & access

> Credentials are referenced by NAME only. Real values live in the secure zone. Never print or commit secrets.

## Production / public endpoints
- Host alias: `prod-prostye-postavki`
- Public host/domain: `miramed32.ru` = **5.129.202.216** (verified 2026-07-09)
- Working directory: `/var/www/prostye-postavki/app`
- MCP: `https://miramed32.ru/mcp/<secret-token>`; store only the token reference, never the token.
- Main service: `prostye-backend.service`; app on `127.0.0.1:8000`, health `/api/health`.
- GitHub source of truth: `https://github.com/xotizwf-create/prostavki`; **prod branch =
  `fix/incoming-paste-single-cell`** (см. deploy.md).
- Access: прямого SSH с ПК нет; заходить через 217 (sshpass, креды в
  `/opt/hermes/secure/projects/prostye-postavki/.env` — IP/USER/PASSWORD). Схема в deploy.md.
- Resources: 2 GB RAM + 2 GB swap — preflight обязателен, тяжёлое не гонять.

## Secure references
- `proj/prostye-postavki/server/env` — project env / server access bundle if present.
- `proj/prostye-postavki/ssh/root` — SSH/root access when added.
- `proj/prostye-postavki/mcp/token` — MCP secret token.
- `proj/prostye-postavki/database/url` — production database URL, if needed.

## Mandatory preflight
Before deploy, build, migration, backup restore, heavy OCR/bulk jobs, or long-running server work, read and follow `engineering/server-preflight.md`.

## Forbidden
- Не печатать секреты, токены MCP, пароли, строки подключения БД.
- Не запускать миграции/тесты/эксперименты на боевой базе.
- Не менять генерацию КП или обработку контрактов без проверки результата на безопасном примере.
