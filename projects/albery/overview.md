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
Albery is Александр's main work project: Flask backend + React/Vite frontend, plus an MCP context server that exposes company data to assistants. It pulls Bitrix tasks, employee chats, Zoom calls/transcripts, org structure, regulations and Google Drive knowledge, then analyzes everything into management reports.

A separate Hermes agent also runs on the same Albery server and is dedicated only to Albery work; do not confuse it with the current general-purpose Hermes Brain agent.

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
The legacy `agent.md` import (now de-mojibaked) is split into focused docs; the docs in this
folder are the curated summary, consult these for full detail:
- [server-context.md](server-context.md) — prod server: nginx, systemd, HTTPS, PostgreSQL, env,
  cron sync, backups, FAQ MCP, Google Apps Script, Bitrix MCP tools, known fixes.
- [vpn-gateway.md](vpn-gateway.md) — AmneziaWG outbound-via-Estonia gateway.
- [hermes.md](hermes.md) — Hermes autonomous agent: setup, Codex provider, cron, Telegram,
  sessions, training, roadmap.
