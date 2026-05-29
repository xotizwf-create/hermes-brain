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

## Current state (2026-05-29)
- Brain scaffolded and committed; pushed to GitHub.
- `albery` migrated as the first project. Full legacy reference imported from the old `agent.md`
  into `projects/albery/server-context.md` (nginx, systemd, https, postgres, cron, backups,
  VPN/AmneziaWG gateway, Hermes agent, Codex, Bitrix MCP tools).

## Open tasks (next steps, not yet done)
1. Split big blocks out of `projects/albery/server-context.md` into clean focused docs
   (`projects/albery/vpn-gateway.md`, `projects/albery/hermes.md`).
2. Sync this brain to the server at `/root/.hermes/agent-knowledge` (see `skills/update-knowledge/`).
3. Switch the Hermes / site `agent.md` pointer to this repo, then remove the old `agent-knowledge/`
   and `agent.md` from the "Сайт мой" repo so there is a single source of truth.
4. Add the user's second project (they chose 1–2 projects on start) via the `add-project` skill.

Keep this section current as tasks complete.
