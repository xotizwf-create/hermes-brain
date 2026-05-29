---
id: albery-overview
type: project
project: albery
tags: [overview]
updated: 2026-05-29
secret_refs: []
---

# Albery — overview

## What it is
Flask backend + React/Vite frontend, plus an MCP context server that exposes company data
(Bitrix tasks & chats, Zoom calls/transcripts, company knowledge, org structure) to assistants.

## Stack
- Backend: Flask (`run_5002.py`, listens on `127.0.0.1:5002`), Python venv at `/var/www/albery/.venv`.
- Frontend: React/Vite (`Интерфейс/`, built to `Интерфейс/dist/`).
- Database: PostgreSQL (backups at `/var/backups/albery/postgres`).
- Infra: Ubuntu, systemd service `albery`, Nginx reverse proxy, Let's Encrypt.

## Key URLs (non-secret)
- Web: https://www.m4s.ru/main  (m4s.ru → www.m4s.ru)
- MCP: https://mcp.m4s.ru/mcp/<MCP_SHARED_SECRET>
- MCP FAQ (limited rights): https://mcp.m4s.ru/mcp-faq/<MCP_FAQ_SHARED_SECRET>
- Repo: https://github.com/xotizwf-create/Albery.git

## Domains / DNS
`m4s.ru`, `www.m4s.ru`, `mcp.m4s.ru` → A `217.198.12.236`.

## Current state
Active. Near-realtime Bitrix task sync (outgoing webhook), incremental Zoom recording sync,
Zoom webhooks. Big external sync cron runs daily 18:00 Europe/Moscow.

## Full reference
`server-context.md` — complete legacy operational reference (imported from `agent.md`):
nginx, systemd, HTTPS, PostgreSQL, env, cron sync, backups, FAQ MCP, Google Apps Script,
VPN gateway (AmneziaWG), Hermes agent, Codex, Bitrix MCP tools, known fixes. The docs in this
folder are the curated summary; consult `server-context.md` for full detail.
