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
- `update-knowledge` — the workflow for changing the brain + syncing to Hermes.
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

## Done (2026-05-30)
1. ✅ Split `server-context.md` → `vpn-gateway.md` + `hermes.md` (+ encoding repair).
2. ✅ Synced brain to the server (backup at `agent-knowledge.bak.<ts>`).
3. ✅ Switched pointer / archived legacy `agent.md` + `agent-knowledge/` in the site repo.

## Open tasks (next steps, not yet done)
- **Phase B — teach Hermes 3 capabilities** (the active goal; agent lives in the user's Telegram):
  1. `project-onboarding` skill — create/run repos with per-project env + prod access (ip/user/pass)
     + git access, write code guided by the brain's skills/standards.
  2. `reminders-and-watchers` skill — one-shot & recurring reminders and watchers via `hermes cron`
     (e.g. "remind me tomorrow 18:00", "every day 10:00", "watch mail every 2h, flag important non-newsletter").
  3. Finalize `update-knowledge` so Hermes can update/create instructions and scale itself.
- Reconcile legacy `186.246.7.32` references in `vpn-gateway.md`/`hermes.md` against the live host.
- Task 4 (deferred): add the user's second project via the `add-project` skill.

Keep this section current as tasks complete.
