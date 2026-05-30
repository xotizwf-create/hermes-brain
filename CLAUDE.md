# CLAUDE.md — working instructions for this repo

This repository **is the agent's brain**: the single, versioned source of truth for what the
agent knows and how it acts across all of the user's projects. It is isolated from any individual
project repo. Read this file first, then `INDEX.md`.

## What this is / why it exists
- Built 2026-05-29 by extracting the agent's knowledge out of the website repo ("Сайт мой")
  into its own private repo so it can scale across many projects for years.
- GitHub: https://github.com/xotizwf-create/hermes-brain (PRIVATE, branch `main`).
- Local: `C:\hermes-brain` (outside OneDrive). Mirrored to server `/root/.hermes/agent-knowledge`.

## Architecture (the design we committed to)
- **Canonical store = files in git.** No database for content. Versioned, diffable, reviewable.
- **Retrieval is layered & upgradeable:** today `INDEX.md` routing + frontmatter tags + grep;
  later a generated registry / RAG over the *same* files. So every doc carries strict frontmatter
  (`schema/frontmatter.schema.yaml`) from day one — those fields are the future search hooks.
- **Secrets never live here** — only references `proj/<slug>/<service>/<credential>`. Real values
  stay server-side in `/root/.hermes/secure/` (`access-map.yaml` + `secrets.yaml`, root-only 600/700).

## Areas
`profile/` (preferences, communication, do-not-do) · `engineering/` (standards, security, testing,
database, deployment, optimization, secrets-access, code-review) · `projects/` (one folder per
project + generated `registry.yaml`) · `connectors/` (gmail, calendar, drive, bitrix, zoom) ·
`personal/` · `skills/` · `logs/` (changelog, decisions, learning-log, mistakes) · `inbox/` · `archive/`.

## Hard rules
1. **Approval-gated mutations.** To change the brain: propose the edit → show a diff → wait for the
   user's confirmation → commit → append one line to `logs/changelog.md`. No silent edits.
2. **No secrets in any committed file.** References only. `scripts/validate.py` enforces this.
3. **Every doc needs valid frontmatter.** Skills use the `name`/`description` format instead.
4. **`projects/registry.yaml` is generated** — run `python scripts/build_registry.py`, never hand-edit.
5. **Validate before committing:** `python scripts/validate.py` must pass.
6. Keep LF line endings (`.gitattributes`); the brain syncs to a Linux server.

## Key skills
- `add-project` — register a new project safely (no secrets, refs only).
- `project-onboarding` — make a project workable by the agent: repo + prod access + git access + env
  (via the server secure store), then write code per the brain's standards.
- `reminders-and-watchers` — one-shot/recurring reminders & watchers (mail, etc.) via `hermes cron` → Telegram.
- `connect-mcp` — connect/switch/remove MCP servers for Hermes safely (owner pastes a URL → Hermes
  edits its own `config.yaml`, restarts gateway, records a secret-free entry in `connectors/registry.yaml`).
- `read-links` — read the content behind a link: web pages + Google Docs/Sheets/Slides (share-link →
  export), via `fetch_url.py`; native `browser`/`web_search` for JS/search.
- `google-account` — the agent's Google profile (owner's account, OAuth read-only): Calendar/Drive/
  Docs/Sheets/Gmail; how it was connected, keep-alive (publish to Production), rotation, adding write.
- `update-knowledge` — the workflow for changing the brain + two-way git sync (Hermes self-scaling).
- `new-repo` — create a git repo + private GitHub repo (gh CLI is installed & authed as `xotizwf-create`).
- `secure-access`, `postgres-production` — credentials & Postgres ops.

## Current state (2026-05-30)
- Brain scaffolded, committed, pushed to GitHub, and **mirrored to prod** `217.198.12.236:/root/.hermes/agent-knowledge`.
- `albery` is the first project. The legacy `agent.md` import was **de-mojibaked** and **split** into
  `projects/albery/{server-context,vpn-gateway,hermes}.md`.
- Single source of truth established: legacy `agent.md` + `agent-knowledge/` in the "Сайт мой" repo
  archived to `_legacy_agent_archive/`; Hermes `config.yaml` system_prompt points at our `INDEX.md`.
- Server connection (no SSH key on PC): `python _deploy_helper.py new "<cmd>"` from the "Сайт мой"
  repo (Paramiko, password from `.env.local`, never printed). Targets: new=217.198.12.236, estonia=95.85.243.43, prod(old)=186.246.7.32.

## Done (2026-05-30) — full session retrospective in `logs/session-2026-05-30.md`
1. ✅ Split `server-context.md` → `vpn-gateway.md` + `hermes.md` (+ encoding repair).
2. ✅ Synced brain to the server.
3. ✅ Switched pointer / archived legacy `agent.md` + `agent-knowledge/` in the site repo.
4. ✅ Phase B skills written: `project-onboarding`, `reminders-and-watchers`, `update-knowledge` (v2).
5. ✅ **Two-way git self-scaling live** — server brain is a git clone with a read-write deploy key;
   Hermes edits → validate → approve in Telegram → commit/push; local pulls. Telegram toolsets enabled.
6. ✅ **Automations live:** reminders → Telegram; `mail-watch` (himalaya, every 2h); `chatgpt-sub-watch`
   (daily 10:00 МСК, warns + auto-removes expired ChatGPT accounts). Clean deliveries (`cron.wrap_response=false`).
7. ✅ Prefs in `profile/`: max-brevity-by-default; no technical text in auto-deliveries; default TZ = MSK.
8. ✅ Security: removed leaked `.env` copies from server backups; secrets only in local `.env` + `/root/.hermes/secure/`.

## Live cron automations (server)
- `mail-watch` — every 2h, important non-newsletter Gmail → Telegram.
- `chatgpt-sub-watch` — daily, ChatGPT subscription expiry warnings + auto-disable; dates in
  `/root/.hermes/chatgpt_accounts.json`.

## Open tasks (next steps, not yet done)
- Reconcile legacy `186.246.7.32` references in `vpn-gateway.md`/`hermes.md` against the live host.
- Task 4 (deferred): add the user's second project via the `add-project` skill.
- MCP connection logic: shipped skill `connect-mcp` + manager (live-tested on 217). Use it for any
  new MCP server: owner pastes a URL → Hermes connects itself. See `connectors/mcp-servers.md`.
- Re-wire Albery MCP: confirmed 2026-05-30 that host 217.198.12.236 has **0 MCP servers** (no
  Bitrix/Zoom hands) AND it is **not** the Albery host (it's `andigital`, `/var/www/andidigital`).
  The MCP host `mcp.m4s.ru` is separate; `MCP_SHARED_SECRET` is not on 217. To connect, get the
  secret from the owner / the Albery box, then `connect-mcp` add albery. (Also reconcile the stale
  `production_host: 217...` + `/var/www/albery/.env` references in the albery docs.)

Keep this section current as tasks complete.
