---
name: project-audit
description: Use when asked to audit, document, or "break down" an existing project/codebase into a full dossier. Produces a plain-language human summary plus structured docs — overview/structure, architecture, database, API & integrations, runbook — with Mermaid diagrams, unknowns flagged, and secrets as references only. Then registers the project. Skip for trivial scripts.
---

# Skill: project-audit

## Goal
Take an existing project (repo + its live server) and lay it out **по полочкам**: a complete, honest
dossier that a human can read top-to-bottom and understand the project — both in plain words and in
technical detail. Output goes to `projects/<slug>/` in the brain's standard shape.

Approach is informed by the community `codebase-onboarding` skill (everything-claude-code) and the
brain's `projects/_template/` + `schema/project.schema.yaml`. Authored fresh (no vendored text).

## When to use
When the owner says "разбери проект", "сделай описание проекта", "audit/document this project",
"что это за проект", or onboards a new project that has code/prod but no docs. Skip for one-off scripts.

## Non-negotiable rules (how to do it RIGHT)
1. **Plain language first.** Every document opens with a short human summary in normal language
   (no jargon) — what it is, who uses it, what problem it solves. Then the technical detail.
2. **Recon with glob/grep, don't read everything.** Find manifests, routes, models, configs — sample,
   don't exhaustively read. Keeps it fast and cheap on context.
3. **Verify in the code, not in the README.** Existing README/comments may be stale or wrong. Trust
   what the code actually does.
4. **Flag unknowns, never invent.** If something isn't confirmed, write `❓ не подтверждено` with where
   you'd look. Wrong-but-confident is worse than "unknown".
5. **Secrets are references only.** Record env-variable *names* and `proj/<slug>/...` refs — never
   values, never commit a secret. (brain hard rule + `engineering/secrets-access.md`)
6. **Live server = read-only + preflight.** Before touching prod, run `engineering/server-preflight.md`;
   only inspect (status, ports, services), never build/migrate on it.
7. **Diagrams.** Use Mermaid for architecture, the DB schema (erDiagram), and the main request/data
   flow — diagrams are the visual "полки".
8. **Concise.** Each doc is scannable. No filler. (brain context hygiene + `karpathy-guidelines`)

## Phases
1. **Recon** — language(s) & frameworks from manifests (`package.json`, `requirements.txt`,
   `pyproject.toml`, `go.mod`, `composer.json`…); directory map; entry points (`main`, `app.py`,
   `index.*`, `run*.py`, `server.*`); build/deploy files (`Dockerfile`, CI, `systemd`, `Makefile`).
2. **Architecture** — components and how they connect; runtime processes/services; request/data flow.
3. **Database** — engine; main tables/entities and relationships; migrations; where it physically runs.
4. **API & integrations** — endpoints the project *exposes* (method + path + purpose); external
   services/APIs/MCP/webhooks it *consumes*; auth model (names only).
5. **Prod** — (if a live host exists) via `server-preflight`: where it runs, services, ports, deploy.
6. **Write** — generate the files below, then `project.yaml`. Register via skill `add-project` only when the owner asked to add the project to the brain/registry or when that is clearly the destination; otherwise deliver docs as files.

## Delivery modes
- **Default brain/onboarding mode:** write docs to `projects/<slug>/`, fill `project.yaml`, then run registry/validation steps if the brain repository and add-project workflow are in scope.
- **No-repo-write / send-me-files mode:** if the owner says not to commit, not to write into the project, or asks to “скинь сюда файлы”, create a separate audit directory outside the target repo, e.g. `/root/audits/<slug>_project_audit/`; write the same docs there; zip the directory; verify `git status --short --branch` in the audited repo is still clean; deliver the zip with `MEDIA:/absolute/path.zip`.
- Never commit audit docs into the target project unless the owner explicitly asks for a repo documentation change/PR.

## Output files → `projects/<slug>/`
Each starts with a **plain-language intro (2–6 sentences, no jargon)**, then detail.

- **`overview.md`** — *«Что это, простыми словами»* (human summary: what it does, who uses it, what
  problem it solves) → tech stack table → directory map → entry points.
- **`architecture.md`** — plain intro → components + responsibilities → data/request flow →
  **Mermaid** diagram (`graph`/`flowchart`).
- **`database.md`** — plain intro → engine + where it lives → main tables/entities → relationships
  (**Mermaid `erDiagram`**) → migrations.
- **`api.md`** — plain intro → **exposed endpoints** (table: method · path · purpose · auth) →
  **consumed** external services/APIs/MCP/webhooks (name · purpose · auth ref) → auth model.
- **`runbook.md`** — plain intro → how to run / build / deploy → commands → env-variable **names**
  only → services/ports. (build/test/migrate happen OFF the live box — `engineering/deployment.md`)
- **`project.yaml`** — machine-readable manifest per `schema/project.schema.yaml`; `links:` points to
  the docs above; `secret_refs:` names only.

## Finish
- Fill `project.yaml`, run `python scripts/build_registry.py` (via skill `add-project`), validate
  (`python scripts/validate.py`), and log to `logs/changelog.md`.
- Surface a short list of `❓ не подтверждено` items so the owner can confirm or correct them.

## Send-me-a-zip audit packaging pattern
When the owner asks for an audit archive in chat (`скинь зип`, `send me the files`), make the deliverable a real attachment, not a path or prose-only summary:
1. Clone/copy the audited source into a separate work directory, not inside the project repo, and record `git status --short --branch` + last commit in `evidence/`.
2. Generate the audit docs in a separate audit directory with at least: summary, architecture, database, API/MCP/integrations, runbook, risks/recommendations, unknowns, and a machine-readable manifest.
3. Run lightweight real checks where safe (for example dependency install/test, syntax compile, dependency audit) and save raw outputs under `evidence/`. Failed checks are valuable audit findings; do not hide them or keep going as if checks passed.
4. Remove transient dependency folders from the audit clone if they were created, then verify the audited repo remains clean.
5. Package with the system `zip` command when available; if it is missing, use Python `zipfile` and verify with `ZipFile.testzip()`.
6. Before final delivery, list/verify archive contents and send the actual file with `MEDIA:/absolute/path.zip`.
