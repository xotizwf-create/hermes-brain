---
id: liniya-servers
type: project
project: liniya
tags: [servers, access, systemd, caddy, postgres]
updated: 2026-08-22
secret_refs: [proj/liniya/ssh/root, proj/liniya/server/env, proj/liniya/database/url]
---

# Линия — servers & access

> Никогда не печатать и не коммитить значения секретов.

## Production
- Alias: `prod-liniya`.
- Host/IP: `91.220.109.145`.
- Public domain: `liteexams.ru`.
- SSH: `root`; текущие реквизиты находятся в самом низу локального gitignored `Hermes Brain/.env` под ключами `Ip`, `USER`, `PASSWORD`.
- Caddy: `liteexams.ru` → `127.0.0.1:3000`.
- Releases: `/opt/liniya/releases/<commit-or-release>`; active symlink `/opt/liniya/current`.
- Runtime env: `/opt/liniya/.env`; значения не читать в вывод, разрешено перечислять только имена ключей.
- Services: `liniya.service`, `liniya-telegram-poller.service` (оба запускаются от пользователя/группы `liniya`).
- Automation: `liniya-notifications.timer`, `liniya-backup.timer`.
- Database: local PostgreSQL, database `liniya_booking`.

## Capacity observed 2026-08-22
- 2 CPU, 1895 MB RAM, about 1246 MB available, no swap, about 23 GB disk free.
- Host is constrained: never build or run full tests on production. Run the mandatory universal server preflight before every server operation.

## Safe connectivity check
Read credentials inside the connecting process, never interpolate the password into command arguments. After connecting, check resources, service status, active symlink and HTTP health before any mutation.
