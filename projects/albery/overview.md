---
id: albery-overview
type: project
project: albery
tags: [overview]
updated: 2026-06-04
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

## Critical external dependencies
- Bitrix Marketplace subscription is mandatory for Albery. Without an active Marketplace subscription in Bitrix, message delivery and pulling information from Bitrix will not work reliably / may stop working entirely.

## Full reference
The legacy `agent.md` import (now de-mojibaked) is split into focused docs; the docs in this
folder are the curated summary, consult these for full detail:
- [server-context.md](server-context.md) — prod server **hub** (operating rules, host facts,
  git workflow, frequent commands, known fixes), routing to:
  - [server-infra.md](server-infra.md) — nginx, systemd, HTTPS, PostgreSQL, env, deploy, backups.
  - [server-mcp-tools.md](server-mcp-tools.md) — Bitrix/Zoom MCP tools, `fetch_url`, FAQ MCP, MCP fixes.
  - [server-integrations-sync.md](server-integrations-sync.md) — hourly sync + Google Apps Script/Drive.
- [vpn-gateway.md](vpn-gateway.md) — AmneziaWG outbound-via-Estonia gateway.
- [hermes.md](hermes.md) — Hermes autonomous agent **hub** (what it is, key paths), routing to:
  - [hermes-setup.md](hermes-setup.md) — Codex provider, install, accounts, deploy, RBAC roadmap.
  - [hermes-automations.md](hermes-automations.md) — `zoom-to-tasks` / `owner-daily` cron behavior.
  - [hermes-operations.md](hermes-operations.md) — cron/Telegram/sessions, STT, restart rule, fixes.
- [owner-reports.md](owner-reports.md) — owner daily/weekly/Zoom report contracts, the
  AI-instruction layer (`upsert_ai_instruction`), and hard rules (identity by transcription,
  owner not responsible, read company knowledge by file name).
