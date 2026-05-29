---
name: add-project
description: Use when the user wants to add a new project to the brain. Safely registers a project (github, prod/mcp servers, deploy, connectors) WITHOUT storing any secret values — only references.
---

# Skill: add-project

## Goal
Add a project to `projects/` in the standard shape, register its secret *references* (never values),
verify connectivity, regenerate the registry, and log it — all approval-gated.

## Collect
- Project name + desired slug (kebab-case, stable forever).
- One-line summary, tags, status.
- GitHub repo + default branch.
- Production: host alias, host, working dir, deploy method.
- MCP server (name, endpoint without secret segments), if any.
- Connectors used (ids from `connectors/`).
- List of secret reference names (NOT values), namespace `proj/<slug>/<service>/<credential>`.

## Forbidden
- Saving passwords, tokens, private keys, `.env`, DB URLs with credentials.
- Inventing a workaround when access is missing — document the needed credential instead.

## Algorithm
1. Copy `projects/_template/` → `projects/<slug>/`.
2. Fill `project.yaml` (manifest) and the docs (`overview`, `servers`, `deploy`, `runbook`,
   `decisions`, `incidents`). Set frontmatter `id`/`project`/`updated` on each doc.
3. Record secret **references** in the manifest `secret_refs`. For each, ensure a matching entry
   exists in server `access-map.yaml`; if a real value is needed, tell the user to add it manually
   to `/root/.hermes/secure/secrets.yaml` (the agent does not type secrets).
4. Run `python scripts/build_registry.py` to regenerate `projects/registry.yaml`.
5. Run `python scripts/validate.py` (frontmatter + secret-leak check). Fix any errors.
6. Connectivity check (prints nothing secret), e.g. service status + `git rev-parse`.
7. Show the user the diff. **Apply (commit) only after confirmation.**
8. Append a line to `logs/changelog.md`. Sync to Hermes (see `update-knowledge`).

## Done when
Manifest + docs filled, registry regenerated, validator passes, connectivity verified,
changelog updated, changes committed after approval.
