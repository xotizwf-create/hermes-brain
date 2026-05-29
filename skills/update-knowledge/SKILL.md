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

## Sync to Hermes
```powershell
# from the brain repo root (C:\hermes-brain)
tar -cf tmp_brain.tar --exclude=.git .
python _deploy_helper.py new --put tmp_brain.tar /tmp/agent-knowledge.tar
python _deploy_helper.py new "rm -rf /root/.hermes/agent-knowledge && mkdir -p /root/.hermes/agent-knowledge && tar -xf /tmp/agent-knowledge.tar -C /root/.hermes/agent-knowledge && rm -f /tmp/agent-knowledge.tar"
Remove-Item -LiteralPath tmp_brain.tar
```
(_deploy_helper.py lives in the albery working copy; run from there, or adapt to your transport.)

## Rule
No silent edits. Diff + approval + changelog every time.
