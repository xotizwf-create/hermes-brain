---
id: brain-decisions
type: log
tags: [decisions, adr]
updated: 2026-05-29
secret_refs: []
---

# Brain decisions (ADR)

Append-only, newest on top. Architecture choices about the brain itself.

## 2026-05-30 — Server brain becomes a git clone (two-way sync) for self-scaling
- **Decision:** `/root/.hermes/agent-knowledge` will be a git clone of `hermes-brain`, not a one-way
  tar mirror. Hermes edits its own brain on the server → validate → owner-approve in Telegram →
  commit → push; the local copy pulls. GitHub canonical stays the single source of truth.
- **Why:** the user wants Hermes to update instructions and scale itself; a one-way mirror loses
  server-side edits. Two-way git keeps history/review and lets the agent persist its own learning.
- **Guard:** approval gate preserved (diff shown in Telegram before commit); secrets never enter the
  repo. Needs GitHub auth on the server (`github-auth` / fine-grained PAT). See `update-knowledge`.

## 2026-05-29 — Files-in-git as canonical store, pluggable retrieval
- **Decision:** canonical knowledge = versioned files; retrieval layer (INDEX/tags → later RAG)
  is separate and upgradeable without rewriting content. Strict frontmatter from day one.
- **Why:** scales for years/many projects; keeps diff/history/review; no premature database.

## 2026-05-29 — Isolated repo, secrets server-side
- **Decision:** brain is its own private repo (`C:\hermes-brain`), decoupled from any project.
  Secrets stay in `/root/.hermes/secure/` (access-map + secrets, root-only). Brain holds refs only.
