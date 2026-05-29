---
id: learning-log
type: log
tags: [learning]
updated: 2026-05-30
secret_refs: []
---

# Learning log

Append-only, newest on top. Durable lessons that improve future work (patterns that worked,
gotchas, preferences confirmed in practice). Link to the file they refine.

## 2026-05-30 — two-way git brain sync is live (verified from the server)
- The prod brain `/root/.hermes/agent-knowledge` is now a git clone of `hermes-brain` (deploy key
  `hermes_brain_deploy`, read-write). This entry was authored and pushed **from the server** to
  verify the self-scaling pipeline end-to-end. Hermes can now edit → validate → (Telegram approval)
  → commit → push; the local copy pulls. See `skills/update-knowledge`.

