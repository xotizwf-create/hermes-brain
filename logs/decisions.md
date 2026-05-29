---
id: brain-decisions
type: log
tags: [decisions, adr]
updated: 2026-05-29
secret_refs: []
---

# Brain decisions (ADR)

Append-only, newest on top. Architecture choices about the brain itself.

## 2026-05-29 — Files-in-git as canonical store, pluggable retrieval
- **Decision:** canonical knowledge = versioned files; retrieval layer (INDEX/tags → later RAG)
  is separate and upgradeable without rewriting content. Strict frontmatter from day one.
- **Why:** scales for years/many projects; keeps diff/history/review; no premature database.

## 2026-05-29 — Isolated repo, secrets server-side
- **Decision:** brain is its own private repo (`C:\hermes-brain`), decoupled from any project.
  Secrets stay in `/root/.hermes/secure/` (access-map + secrets, root-only). Brain holds refs only.
