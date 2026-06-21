---
id: claude-code-tg-agent
type: engineering
tags: [agent, claude-code, telegram, server, 217, runbook]
updated: 2026-06-20
secret_refs: []
---

# Claude Code agent on 217 (Telegram coder / maintenance agent)

A **second agent** lives on server 217 alongside Hermes: **Claude Code** (Anthropic's CLI),
reachable through a private Telegram bot. Installed 2026-06-20. Hermes = messaging/ops brain
(Codex). This agent = **coder/maintenance** — edits the brain and project repos on git branches,
can diagnose and fix Hermes. Business MCP tools were intentionally **not** added (that is Hermes' job).

## What/where
- **Bot:** `@GoogleDeck_Bot` ("Агент Клод"). Owner-locked (TOFU — binds to the first user who writes;
  owner id `1451982360`). The bot token was previously used by an unrelated app, so old chat history
  and a stale reply-keyboard may appear; the bridge clears the keyboard with `remove_keyboard`.
- **Process:** PM2 service **`claude-tg`**, bridge `/root/claude-agent/bridge.js` (Node, Telegram
  long-polling + spawns `claude -p`). PM2 boot-persistence is enabled (`systemctl is-enabled pm2-root`
  → `enabled`; `pm2 save` done) so it survives reboot. Logs: `pm2 logs claude-tg`.
- **Binary:** `claude` 2.x at `/usr/bin/claude` (npm global, Node 22). State: `/root/claude-agent/state.json`.

## Identity — "1-to-1 with the owner's IDE Claude"
- **Same Claude account** as the owner's local Claude Code (org `9a7c49c2-...`,
  `alexxandr.nikitenko@gmail.com`, `claude_pro`). **Do not log this account in elsewhere** or its
  session can drop — same failure class as Codex (see brain note on Codex auth).
- **Auth:** Claude **Pro**, long-lived OAuth token (1 year, via `claude setup-token`) at
  `/root/.hermes/secure/claude_code/oauth_token` (mode 600). Bot token at `.../bot_token` (600).
  Re-auth if it ever expires: `claude setup-token` in a tmux session → owner opens the URL, logs in
  → token printed → store it at the path above → `pm2 restart claude-tg`.
- **Model:** `opus` + `effortLevel: high` (set in `/root/claude-agent/settings.json` and `--model opus`
  in the bridge) — matches the IDE brain.
- **Knowledge:** runs with `cwd = /root/.hermes/agent-knowledge` (the brain clone) so it reads the
  **same `CLAUDE.md` / `INDEX.md`** as Hermes. Operating charter: `/root/claude-agent/charter.md`.

## Safety model (why it is allowed to run as root)
Runs as root with `IS_SANDBOX=1` + `--dangerously-skip-permissions` (needed so it can fix Hermes /
edit root-owned brain). The real guard is a **PreToolUse hook** `/root/claude-agent/guard.py`
(registered in `settings.json`, exit 2 = block) that hard-denies: `rm -rf` of system/home paths,
`git push` to main/master, force-push, `systemctl stop/disable hermes*`, `DROP/TRUNCATE`, writes into
`/root/.hermes/secure`, `git reset --hard`, shutdown/reboot, fork bombs. The charter tells it to work
on branches and ask before anything touching production. Verified 10/10 on deploy.

## Telegram commands / menu
Native command menu via `setMyCommands` + an inline-button menu on `/start` and `/menu`:
- `/account` — **account (Pro) limit**: a tiny `/v1/messages` call (model `claude-haiku-4-5-...`,
  `max_tokens:1`, header `anthropic-beta: oauth-2025-04-20`) → parse response headers
  `anthropic-ratelimit-unified-{5h,7d}-{utilization,status,reset}` (utilization is a 0..1 fraction → ×100 = %).
- `/session` — usage of the current session (requests/tokens/cost, tracked per session slot).
- `/sessions`, `/new`, `/switch N`, `/reset` — multi-session management. Transcripts live under
  `/root/.claude/projects/` (added to the agent's `--add-dir`, so it can read other sessions).

## Maintenance quick-ref
- Restart: `pm2 restart claude-tg`. Status/logs: `pm2 list`, `pm2 logs claude-tg`.
- Memory guard: bridge runs one Claude session at a time; `NODE_OPTIONS=--max-old-space-size=512`;
  PM2 `--max-memory-restart 650M`. (217 is a ~1 GB box — keep it to one session; never build on it.)
- Connect from PC: paramiko, server creds in the Hermes-Brain repo `.env` (lines 1–4). PowerShell
  expands `$(...)` locally — send token-substitution commands via a Python (paramiko) script, not inline.
