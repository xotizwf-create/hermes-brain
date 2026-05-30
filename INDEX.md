---
id: index
type: schema
tags: [root, routing, entrypoint]
updated: 2026-05-29
secret_refs: []
---

# Hermes Brain — Index

This repository is the agent's brain. It is the **single source of truth** for what the
agent knows and how it acts across all projects. It is isolated from any single project repo.

**Read this file first in every new session.** Then load only the files relevant to the
current task — never load the whole brain unless asked for a full audit.

## Core principles

1. **Canonical store = files in git.** Versioned, diffable, reviewable. No database for content.
2. **Secrets never live here.** Only *references* (names) live in `secrets-templates/` and project
   manifests. Real values live on the server under `/root/.hermes/secure/` (root-only, mode 700/600).
3. **Knowledge = what to know. Skills = how to act.** Logs = what changed & what was learned.
4. **Mutations are approval-gated.** The agent proposes a diff; the user confirms; then it commits
   and writes to `logs/changelog.md`.
5. **Every doc carries frontmatter** (`id`, `type`, `tags`, `updated`, `secret_refs`) per
   `schema/frontmatter.schema.yaml`. This is the hook for future search/RAG without rewriting content.

## Areas

| Area | Path | Purpose |
|---|---|---|
| Profile | `profile/` | Who the user is, preferences, communication, hard rules |
| Engineering | `engineering/` | Universal how-to-build: standards, security, testing, db, deploy, optimization |
| Projects | `projects/` | One isolated folder per project + machine-readable `registry.yaml` |
| Connectors | `connectors/` | MCP connectors (Gmail, Calendar, Drive, Bitrix…) + `registry.yaml` + usage rules |
| Personal | `personal/` | Education, side-jobs, life knowledge that helps the agent act |
| Skills | `skills/` | Repeatable procedures the agent executes |
| Logs | `logs/` | changelog, decisions (ADR), learning-log, mistakes |
| Inbox | `inbox/` | Unsorted buffer awaiting classification |
| Archive | `archive/` | Retired material (archived, not deleted) |

## Routing

- **Project work / "connect to X" / deploy X** → read `projects/registry.yaml`, find the project,
  load only `projects/<slug>/`. For credentials use the `secure-access` skill.
- **Add a new project** → use skill `skills/add-project/`.
- **Securely take a project's secrets** (owner pastes a `.env` / prod-server password → store in the
  secure zone, never echoed; remember repo + prod host) → skill `skills/store-project-secrets/`.
- **Secret-manager web UI** (browser, tied to GitHub repos; install/operate/resell) → `skills/secure-access/vault/` (README).
- **Onboard a project to work in** (repo + prod access + git access + env, then write code) → skill `skills/project-onboarding/`.
- **Reminders / recurring tasks / watch mail** → skill `skills/reminders-and-watchers/`.
- **Connect / switch / remove an MCP server (owner pastes a URL)** → skill `skills/connect-mcp/`;
  model in `connectors/mcp-servers.md`; what's connected in `connectors/registry.yaml`.
- **Read a link / web page / Google Doc / Sheet / Slides (owner pastes a URL)** → skill `skills/read-links/`.
- **Google account access (Calendar / Drive / Docs / Sheets / Gmail), re-auth, scopes** → skill
  `skills/google-account/`; connector ref `connectors/google-workspace.md`.
- **Add/manage a GitHub repo** → use skill `skills/new-repo/`.
- **Credentials, SSH, tokens, DB URLs** → `engineering/secrets-access.md` + skill `secure-access`.
- **Database / migrations / Postgres** → `engineering/database.md` + skill `postgres-production`.
- **Deploy / systemd / nginx** → `engineering/deployment.md`.
- **Security / auth / webhooks** → `engineering/security.md`.
- **Tests / CI** → `engineering/testing.md`.
- **Performance** → `engineering/optimization.md`.
- **Code style / review** → `engineering/coding-standards.md`, `engineering/code-review.md`.
- **How the agent should answer/communicate** → `profile/`.
- **Hermes UX: "Думаю…"/typing, live step progress, reasoning, tone — config knobs** → `engineering/hermes-gateway-ux.md`.
- **Change the brain itself / how Hermes scales itself** → skill `skills/update-knowledge/`.
- **How Hermes was built & how it's taught (orientation)** → `logs/session-2026-05-30.md`.

## Secret model (summary)

- `secrets-templates/access-map.template.yaml` → non-secret routing: project → service → credential
  *name* + allowed actions. Deployed to `/root/.hermes/secure/access-map.yaml` (mode 600).
- `secrets-templates/secrets.template.yaml` → real values or `value_path`. Deployed to
  `/root/.hermes/secure/secrets.yaml` (mode 600). **Never committed.**
- Secret references use the namespace `proj/<slug>/<service>/<credential>`.

## Hermes sync

This repo is mirrored to the server at `/root/.hermes/agent-knowledge`. After changing the brain,
sync before expecting Hermes to use the new content. See `skills/update-knowledge/`.
