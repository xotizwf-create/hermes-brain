---
id: prostye-postavki-servers
type: project
project: prostye-postavki
tags: [servers, access]
updated: 2026-05-31
secret_refs: [proj/prostye-postavki/server/env, proj/prostye-postavki/ssh/root, proj/prostye-postavki/mcp/token]
---

# Простые поставки — servers & access

> Credentials are referenced by NAME only. Real values live in the secure zone. Never print or commit secrets.

## Production / public endpoints
- Host alias: `prod-prostye-postavki`
- Public host/domain: `miramed32.ru`
- Working directory: `/var/www/prostye-postavki/app`
- MCP: `https://miramed32.ru/mcp/<secret-token>`; store only the token reference, never the token.
- Main service: `prostye-backend.service`.
- GitHub source of truth: `https://github.com/xotizwf-create/prostavki`.

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
