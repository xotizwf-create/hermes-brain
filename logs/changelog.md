---
id: changelog
type: log
tags: [changelog]
updated: 2026-05-29
secret_refs: []
---

# Changelog

Append-only, newest on top. Every approved change to the brain gets one line.

## 2026-05-30
- read-links Google profile (owner chose **OAuth = own account, read-only**): `gauth_read.py` reads
  the owner's Google Docs/Sheets/Slides via an OAuth refresh token at
  `/root/.hermes/secure/google_oauth_token.json` (600, gitignored — ref `agent/google/oauth-token`,
  scopes `drive.readonly`+`spreadsheets.readonly`) — no per-doc sharing; Sheets → all tabs as CSV.
  Service account kept as an alternative. `fetch_url.py` prefers the token, falls back to public export
  when absent; no-access message branches OAuth vs SA. Added `scripts/google_oauth_login.py` (PC-side
  browser consent → refresh token; Google blocks the consent screen from the server IP, so login is
  done on the PC and the token copied over, like Codex). `connectors/google-workspace.md` documents the
  one-time Cloud OAuth-client + login + token delivery. Token files gitignored. Google libs already in
  the venv. Pending: owner creates the OAuth client in Cloud + we run the PC login + drop the token.
- Added skill `read-links` + `scripts/fetch_url.py` (stdlib): read the content behind a pasted link.
  Google Docs/Sheets/Slides/Drive → share-link converted to the export URL (Docs→txt, Sheets→csv,
  Slides→txt) and fetched in full (no browser, no LLM/Firecrawl summarization, no token cost); normal
  pages → HTML reduced to readable text (capped ~20k). Private Google docs are detected and reported
  in Russian (need link-sharing or Google auth — offered as a follow-up). Skill routes JS-heavy/login
  pages to the native `browser_*` tools and "найди в интернете" to `web_search` (both already enabled
  on prod). All owner-facing output Russian, no technical noise. INDEX + CLAUDE key-skills updated.
  Grounded in prod inspection: web/browser/vision toolsets enabled; server reaches the internet
  (example.org 200); Google export endpoints reachable.
- connect-mcp auto-reload: after add/enable/disable/remove the live Telegram session now picks up the
  tool changes **by itself** — the owner no longer needs to send `/reload-mcp`. Implemented as an
  idempotent gateway patch (`skills/connect-mcp/patches/mcp_autoreload_patch.py`): before each agent
  turn the gateway hashes the `mcp_servers` block and, if it changed since last seen, calls its own
  `_execute_mcp_reload(event)` (the `/reload-mcp` path, which also refreshes cached agents so the
  active session sees new tools next turn). Cheap on the no-change path (stat); fires once per change.
  Self-heals across `hermes update` via systemd `ExecStartPre` drop-in
  `skills/connect-mcp/systemd/20-mcp-autoreload.conf`. Manager message updated (no more «отправь
  /reload-mcp»). Grounded in the live gateway source (anchors verified unique; patch validated by
  py_compile; never breaks run.py).
- connect-mcp fixes after the first real connection (`prostye_postavki` = "Простые поставки",
  miramed32, 19 tools). (1) **Hard rule: never auto-name a connector** — after `probe`, STOP and ask
  the owner; `probe` now ends with «Как назовём этот сервер?» and the skill forbids deriving a name
  from the URL/domain. (2) **All owner-facing manager output is Russian, no technical noise** (no
  paths/commands/ids/stack traces); errors print human Russian. Added the same rule globally to
  `profile/communication.md`. (3) Manager now **slugifies a human name** ("Простые поставки" →
  `prostye_postavki`) and echoes the human name in messages; enable/disable/remove accept the human
  label. Recorded the live connector in `connectors/registry.yaml` (+ `label`) and added
  `connectors/prostye-postavki.md`.
- MCP connectors subsystem (grounded in the live Hermes source on prod). Added skill `connect-mcp` +
  manager `skills/connect-mcp/scripts/hermes_mcp.py`. Hermes' native `hermes mcp add` is interactive
  (TTY prompts), so the manager writes the **same canonical `mcp_servers` schema** (`{url, headers?,
  enabled}`, from the bundled `native-mcp` skill) non-interactively into `~/.hermes/config.yaml` — so
  the owner can paste a URL to the bot and Hermes connects itself. Switching = the **native `enabled`
  flag** (not a custom park key). Apply live via **`/reload-mcp`** in Telegram (reconnect, no restart,
  no lost session); `--restart` is the heavy fallback. Default dry-run; every write backs up config;
  `rollback` restores it. Secrets (URL path / bearer token) stay only in `config.yaml`/`~/.hermes/.env`
  (600), redacted everywhere else; registry gets a secret-free `url_template`. Added
  `connectors/registry.yaml` + `connectors/mcp-servers.md` (model). INDEX + CLAUDE updated.
  **Discovered prod had 0 MCP servers** (`mcp_servers: {}` on 217 — Albery hands were missing); re-wired
  Albery as the live test (URL built server-side from `/var/www/albery/.env`, `hermes mcp test` =
  tools discovered).
- Added `chatgpt-sub-watch` (daily 10:00 МСК, no-agent): warns before each ChatGPT account expires and
  **auto-removes** it the day after expiry (`hermes auth remove openai-codex <id>`), keeping the last
  account as a safety net. Dates registry `/root/.hermes/chatgpt_accounts.json` (acct #1 13.06, acct #2
  abc9@btwwin.sbs 30.05). Fixed the remove-call to pass the provider arg.
- Added `logs/session-2026-05-30.md` — session retrospective + "how Hermes is trained / how it scales
  itself" + a map of where everything lives. Refreshed `CLAUDE.md` state and `INDEX.md` so both the
  next Claude session and Hermes itself find it.
- Activation (mail watcher): installed `himalaya` v1.2.0 on prod, configured the Gmail account
  (App Password in `/root/.hermes/secure/gmail_app_password`, 600, referenced via `auth.cmd` — not in
  repo/config). Created cron `mail-watch` (every 2h, `--skill himalaya`, deliver telegram). IMAP
  verified (folder list) and a live run returned `[SILENT]` (no important mail → no spam). Updated
  `reminders-and-watchers` skill with the deployed setup. Also corrected the stale telegram-toolset
  note in `hermes.md` (toolsets are enabled, not disabled).
- Activation: (1) verified reminders → Telegram live (test cron fired + `delivered to telegram:…`);
  (2) **two-way git**: server brain converted to a git clone via a repo-scoped read-write deploy key
  (`hermes_brain_deploy`), identity `hermes-server`; round-trip verified (server commit `651473c`
  pushed → pulled locally). Server is **UTC** → reminders use UTC−3 for Moscow times. Updated
  `update-knowledge` + `reminders-and-watchers` skills with the deployed reality.
- Phase B (teach Hermes): added skills `project-onboarding` (repo + prod/git/env access via secure
  store, then code per standards) and `reminders-and-watchers` (`hermes cron` one-shot/recurring +
  `himalaya` mail watcher → Telegram, grounded in the live `hermes cron create` interface). Reworked
  `update-knowledge` to a two-way git model (server brain = clone; Hermes self-edits → approve in
  Telegram → commit/push). Added INDEX routing + CLAUDE.md key-skills + decisions.md ADR. Grounded in
  server inspection: Hermes v0.15.0, builtin skills (himalaya/github-auth/codex), currently 0 MCP servers.
- Task 3 (single source of truth): in the "Сайт мой" repo, the legacy `agent.md` (186 KB) and old
  `agent-knowledge/` were untracked; archived both into `_legacy_agent_archive/` (chosen over delete)
  with a README pointing to hermes-brain. No tracked file referenced them; Hermes system_prompt
  already reads our `INDEX.md`. Updated CLAUDE.md state/tasks.
- Task 2 (sync): mirrored the brain to prod `217.198.12.236:/root/.hermes/agent-knowledge` via
  tar + `_deploy_helper.py` (per `update-knowledge`). Backed up the old structure to
  `agent-knowledge.bak.20260529_210928` first. New tree (profile/engineering/projects/…, 65 files)
  in place; `INDEX.md` preserved (the only path Hermes `config.yaml` system_prompt references).
  Confirmed prod outbound IP = `95.85.243.43` (VPN/Estonia active on 217).
- Task 1 (split): extracted two big subsystems out of `projects/albery/server-context.md` into
  focused docs — `vpn-gateway.md` (AmneziaWG outbound-via-Estonia) and `hermes.md` (Hermes agent:
  Codex provider, cron, Telegram, sessions, training, RBAC roadmap). `server-context.md` now holds
  the app/server reference + Bitrix MCP tools + fetch_url/bug notes. Updated its frontmatter/intro,
  `overview.md` "Full reference", added cross-links. IP `186.246.7.32` left in legacy commands with a
  banner (current prod `217.198.12.236`) — to reconcile live during brain sync (Task 2).

## 2026-05-29
- Fixed mojibake in `projects/albery/server-context.md`: 771 legacy lines were double-encoded
  (UTF-8 bytes read as CP1251 then re-encoded). Repaired in place via per-line round-trip
  (`cp1251.GetBytes` → `utf8.GetString`), kept already-clean lines, normalized CRLF→LF. 0 residual
  U+FFFD. Earlier "UTF-8 verified clean" claim was wrong (see mistakes.md).
- `scripts/validate.py`: also skip `CLAUDE.md` (landing/instruction file, no frontmatter needed).
- Created isolated `hermes-brain` repo. Built areas: profile, engineering (migrated + new
  coding-standards/code-review), projects (template, manifest schema, registry generator,
  validator), connectors (gmail/calendar/drive/bitrix/zoom), personal, skills, logs.
- Migrated albery as first reference project.
- Imported legacy `agent.md` (site repo) → `projects/albery/server-context.md` as the full
  operational reference (UTF-8 verified clean, scanned for secrets — none). Curated docs link to it.
- Hardened `scripts/validate.py`: skip README, expand secret-placeholder allowlist (getpass/env/...).
