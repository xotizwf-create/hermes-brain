---
id: mistakes
type: log
tags: [mistakes, postmortem]
updated: 2026-05-29
secret_refs: []
---

# Mistakes

Append-only, newest on top. Concrete mistakes + how to avoid repeating them. Pulled from
incidents and review feedback so the same error doesn't happen twice.

## 2026-05-29 — legacy import marked "UTF-8 clean" but was mojibake
- **What:** the `agent.md` → `server-context.md` import was logged as "UTF-8 verified clean", but
  771 lines were actually double-encoded mojibake (`## Р РµРїРѕР·РёС‚РѕСЂРёР№` instead of `## Репозиторий`).
  The validator only greps for secret shapes, so garbled-but-valid UTF-8 passed silently.
- **Why it slipped:** "opens without error in UTF-8" was treated as "correct". Double-encoded text
  is still valid UTF-8 — it just renders as Cyrillic-looking noise (`Р`, `С‚`, `Рµ`…).
- **How to avoid:** when importing non-ASCII text, eyeball a known word in the result, and/or test the
  un-mojibake round-trip: if `utf8(cp1251_bytes(line))` yields cleaner text with no U+FFFD, the source
  was mojibake. Consider a `scripts/validate.py` heuristic that flags lines with a high `Р`/`С` density.
