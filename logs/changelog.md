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
- Google OAuth app **published to Production** (owner did it) → re-ran the PC consent once and
  re-minted the token, so the refresh token is now **long-lived** (no more ~7-day Testing expiry).
  Delivered to the secure store + compat path (600, old backed up); read re-verified. The durability
  caveat on the Calendar entry below is now resolved.
- Google **Calendar upgraded to read/write** (owner asked Hermes to see AND edit). Changed the Calendar
  scope in `read-links/scripts/google_oauth_login.py` (`calendar.readonly` → `calendar`), re-ran the
  PC browser consent with the owner's existing Desktop OAuth client, minted a new token (refresh +
  4 scopes: drive/sheets/gmail readonly + **calendar read/write**), delivered it over SFTP to
  `/root/.hermes/secure/google_oauth_token.json` AND the bundled-tool compat path
  `/root/.hermes/google_token.json` (both 600; old token backed up). Verified end-to-end with the
  bundled `google_api.py calendar`: list (read) ✓, create ✓, delete ✓ (test event added then removed,
  calendar left clean). Hermes now creates/edits/deletes events via `google_api.py calendar
  create|delete` (ISO+TZ; edit = delete+create); keep writes behind owner confirmation. Updated
  `skills/google-account`. ⚠ Still pending for durability: **publish the OAuth app to Production**
  (Testing-mode refresh tokens for sensitive scopes expire ~7 days) — else weekly re-login.
- GitHub account access for Hermes (prod). Before: server had only the single-repo `hermes-brain`
  deploy key + no `gh` → couldn't see/clone the owner's other repos. Now: installed `gh` CLI on prod
  (`/usr/bin/gh` 2.93.0) and authed it as **`xotizwf-create`** by **reusing this PC's gh OAuth token**
  (owner's choice: speed over a dedicated token; scope `repo, read:org, gist` = read/write to ALL the
  owner's repos). Token pushed to `/root/.hermes/secure/github_token` (600) over SFTP (never printed) +
  `/root/.config/gh/hosts.yml`; `gh auth setup-git` wired git's credential helper; git identity set.
  Verified: `gh repo list` (10 repos), `gh repo view <private>`, `GIT_TERMINAL_PROMPT=0 git ls-remote
  <private>` all OK. Brain holds no token — ref `agent/github/token`. Docs: `engineering/secrets-access.md`
  ("Server GitHub access" + broad-token/PC-coupling caveat), `skills/new-repo` prerequisites, server
  `access-map.yaml` github entry. ⚠ Same token as the PC — PC re-login may rotate it and break the server.
- UX round 2 — kill technical noise, keep human narration. Owner saw raw tool bubbles
  (`📚 skill_view`, `💻 terminal: "git …"`) after round 1: those come from tool progress, which is
  exactly the technical text he rejects. Reverted **`display.platforms.telegram.tool_progress: off`**.
  Also turned **`long_running_notifications: false`** (the `⏳ Working — N min` heartbeat is hardcoded
  English + leaks the current tool name). The real "live progress" is the model's own Russian
  narration (`interim_assistant_messages`, already on) — strengthened the system_prompt: send a brief
  natural status ~every 30s («Проверяю токен…»), never show tool names/commands/paths/iteration.
  Corrected `engineering/hermes-gateway-ux.md` (round 1 wrongly recommended tool_progress=new) +
  `profile/communication.md`. Config backed up, gateway restarted from SSH, healthy.
- Hermes UX made visible & honest (config, not code — no run.py patch). Telegram **tool progress
  turned on** (`display.platforms.telegram.tool_progress: new`) so the owner sees live step bubbles;
  native Telegram "typing…" indicator already auto-resumes = the "Думаю…" cue. **system_prompt
  expanded** with hard rules: only Russian, narrate steps briefly, honest "не нашёл" instead of
  made-up answers, no English/technical system strings in chat, business tone. `show_reasoning` left
  OFF on purpose (English `💭 Reasoning` block + raw CoT fights Russian-only); no `ru` UI locale ships
  so `language` stays `en`. Noted `display.personality: kawaii` as a tone risk (left as-is). Config
  backed up server-side; gateway restarted from SSH (external) and verified healthy. New brain doc
  `engineering/hermes-gateway-ux.md` + INDEX route.
- MCP "обнови" fix: refresh/restart no longer kills the active chat turn. `hermes_mcp.py` gained
  `detached_restart()` (restart dispatched to a separate `systemd-run --on-active` transient unit so
  the reply flushes first); `cmd_refresh` + `apply_live` route through it. Was the root cause of the
  garbled "Gateway shutting down — task interrupted" replies on "обнови". Made "обнови" an explicit
  trigger in `connect-mcp` (→ `refresh --apply`); reinforced in `connectors/mcp-servers.md`. Profile:
  Russian-only in chat, honest "не нашёл" instead of made-up answers, never restart the gateway mid-turn.
- Google Workspace compatibility documented: when bundled Hermes Google tools expect `/root/.hermes/google_token.json`, reuse the existing secure OAuth token at `/root/.hermes/secure/google_oauth_token.json` via `install -m 600 ...`, verify with `setup.py --check`, and install missing Google API deps with `uv pip install --system ...` if normal `pip` is unavailable. Updated `google-account`, `connectors/google-workspace`, and `update-knowledge` with the owner preference to auto-document new non-trivial procedures.
- Google account CONNECTED (OAuth, owner's account, read-only). Added skill `google-account` (the
  full instruction: how it was set up, usage, keep-alive, rotation, adding write) +
  `google-account/scripts/gcal_read.py` (Calendar agenda). Cloud project `gen-lang-client-0802797266`;
  enabled Drive/Sheets/Calendar/Gmail APIs; OAuth Desktop client; PC browser login (token has
  refresh_token + 4 read scopes); token delivered to `/root/.hermes/secure/google_oauth_token.json`
  (600, gitignored, ref `agent/google/oauth-token`). Verified live on prod: Calendar API call
  succeeded (auto-refresh works). Scopes widened to drive/sheets/calendar/gmail readonly (also in
  `gauth_read.py` + `google_oauth_login.py`). Fixed login script's Windows-console print crash.
  ⚠ Pending: owner should **publish the OAuth app to Production** (else sensitive-scope refresh tokens
  expire ~7 days); re-auth after publishing. Transport gotcha noted: Git-Bash `/root` path mangling →
  `MSYS_NO_PATHCONV=1` / base64-over-SSH.
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
