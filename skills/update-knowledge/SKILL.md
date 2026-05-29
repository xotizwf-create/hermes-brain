---
name: update-knowledge
description: Use when changing the brain itself — adding/editing knowledge, classifying inbox items, or syncing to the Hermes server. Enforces approval-gated, logged, validated edits.
---

# Skill: update-knowledge

## Goal
Evolve the brain safely: classify → edit → validate → show diff → confirm → commit → log → sync.

## Classify new information into one area
- **profile** — user, preferences, communication, hard rules.
- **engineering** — universal how-to-build.
- **project** — belongs to a specific project (`projects/<slug>/`).
- **connector** — an MCP connector.
- **personal** — education, side-jobs, life knowledge.
- **skill** — a repeatable procedure.
- If unclear, drop into `inbox/unsorted.md` and propose classification later.

## Algorithm
1. Decide the target file (or new file). New docs MUST have valid frontmatter
   (`id`, `type`, `updated`, optional `tags`/`secret_refs`/`aliases`) per `schema/frontmatter.schema.yaml`.
2. Make the edit. Bump `updated`. Never write secret values — references only.
3. If a project manifest changed: `python scripts/build_registry.py`.
4. `python scripts/validate.py` — must pass.
5. **Show the diff to the user. Apply (commit) only after confirmation.**
6. Append a line to `logs/changelog.md`. For architectural choices, add to `logs/decisions.md`;
   for lessons, `logs/learning-log.md`; for errors, `logs/mistakes.md`.
7. Sync to Hermes server.

## Sync model: two-way git (single source of truth)
Canonical = the GitHub repo `hermes-brain`. Both the local working copy (`C:\hermes-brain`) and the
server brain (`/root/.hermes/agent-knowledge`, a **git clone**) are checkouts of it. Sync = git.

- **Local edit → everywhere:** commit locally → `git push` → on the server `git -C
  /root/.hermes/agent-knowledge pull --ff-only`.
- **Server/Hermes edit → everywhere:** Hermes commits+pushes on the server (see self-scaling) →
  locally `git pull`.
- Hermes `config.yaml` system_prompt points only at `…/agent-knowledge/INDEX.md`; knowledge files
  are read on demand, so **no gateway restart** is needed after a content sync.

One-time setup to convert the server mirror into a clone (needs GitHub read/write on the server via
the `github-auth` skill or a fine-grained PAT; the repo is private):
```bash
mv /root/.hermes/agent-knowledge /root/.hermes/agent-knowledge.pre-git.bak
git clone https://github.com/xotizwf-create/hermes-brain.git /root/.hermes/agent-knowledge
```
(Bootstrap transport before the clone exists = tar via `_deploy_helper.py new --put`, see git history.)

## Self-scaling: Hermes edits its own brain (autonomous, still approval-gated)
When Hermes (on the server) needs to add/update an instruction or skill:
1. Edit the file under `/root/.hermes/agent-knowledge/` (or add a new doc with valid frontmatter).
2. `python scripts/validate.py` in that dir — must pass. If a manifest changed, `build_registry.py`.
3. **Show the diff to the owner in Telegram and wait for "да/ок"** — this is the approval gate in the
   autonomous context (same rule, different channel). No silent self-edits.
4. After approval: `git add -A && git commit` (end message with the Co-Authored-By trailer) and
   `git push`. Append one line to `logs/changelog.md`.
5. Tell the owner it's live; the local copy picks it up on the next `git pull`.

If unsure whether a change is warranted, drop a note in `inbox/unsorted.md` and ask the owner instead
of editing core docs.

## Rule
No silent edits. Validate + diff + owner approval + changelog every time — locally or on the server.
