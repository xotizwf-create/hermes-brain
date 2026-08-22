---
id: liniya-overview
type: project
project: liniya
tags: [overview, booking, telegram]
updated: 2026-08-22
secret_refs: []
---

# Линия — overview

## What it is
«Линия» — универсальный сервис онлайн-записи для частных мастеров. Клиенты записываются через публичную страницу или Telegram, специалисты управляют расписанием, услугами, клиентами и сообщениями, администратор — пользователями, оплатами, рефералами, подписками и состоянием системы.

## Stack
- Frontend/runtime: React 19, vinext, Vite, Node.js 22+.
- Database: PostgreSQL (`liniya_booking`), Drizzle migrations.
- Integrations: Telegram Bot/Mini App, ЮKassa; VK предусмотрен кодом, но его переменных нет в текущем production env.
- Infra: Caddy, systemd, immutable releases under `/opt/liniya/releases`.

## Key URLs
- Production: https://liteexams.ru
- GitHub: https://github.com/xotizwf-create/liniya-booking-service
- Local repo: `G:\OneDrive\Рабочий стол\Мои проекты\Сервис для записи`

## Current state
Production is live. Web app, Telegram poller, Caddy, PostgreSQL, notification timer and daily backup timer were active on 2026-08-22. The active release was commit `ce7189c`.
