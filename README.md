# hermes-brain

Isolated, versioned knowledge base for the agent — the single source of truth for what it
knows and how it acts across all projects. Decoupled from any individual project repo.

**Start at [`INDEX.md`](INDEX.md).**

## Layout
- `profile/` — user, preferences, communication, hard rules
- `engineering/` — universal how-to-build (standards, security, testing, db, deploy, optimization)
- `projects/` — one folder per project + generated `registry.yaml`
- `connectors/` — MCP connectors + usage rules
- `personal/` — education, side-jobs, life knowledge
- `skills/` — repeatable procedures (`add-project`, `update-knowledge`, `new-repo`, …)
- `logs/` — changelog, decisions (ADR), learning-log, mistakes
- `schema/` — frontmatter + project manifest contracts
- `scripts/` — `build_registry.py`, `validate.py`
- `secrets-templates/` — secret **model** (references only; real values stay server-side)

## Rules
1. Secrets never live here — only references (`proj/<slug>/<service>/<credential>`).
2. Changes are approval-gated: diff → confirm → commit → `logs/changelog.md`.
3. Every doc carries frontmatter (`schema/frontmatter.schema.yaml`).
4. `registry.yaml` is generated — run `python scripts/build_registry.py`, never hand-edit.
5. Validate before committing: `python scripts/validate.py`.
