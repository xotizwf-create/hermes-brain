---
id: mistakes
type: log
tags: [mistakes, postmortem]
updated: 2026-06-11
secret_refs: []
---

# Mistakes

Append-only, newest on top. Concrete mistakes + how to avoid repeating them. Pulled from
incidents and review feedback so the same error doesn't happen twice.

## 2026-06-11 — PDF "отправлен" 4 раза, но так и не дошёл: /root в denylist доставки вложений
- **What:** owner asked for a solved math problem as a PDF. The agent built the PDF at
  `/root/integral_solution_2026.pdf` and four times told the owner «отправил» — but the gateway
  silently dropped every attempt (`Skipping unsafe MEDIA directive path`), because in non-strict
  mode the **whole `/root` is on the hardcoded denylist** (root's home = credential territory);
  only `media_delivery_allow_dirs` subfolders are deliverable. The agent gets **no error signal**
  on a dropped MEDIA path, so it kept honestly believing — and claiming — delivery.
- **Why it slipped:** the 2026-06-06 fix added allow_dirs and a brain rule «write deliverables to
  the outbox», but a brain doc is not read every turn — the model wrote to `/root/` again; and the
  failure stayed invisible to the model (log-only warning), so it could not self-correct.
- **Fix (3 layers, 2026-06-11):** (1) gateway **rescue patch** — a location-only rejection of a
  fresh (≤30 min), non-credential, ≤50 MB file now copies it into `/root/.hermes/outbox` and
  delivers from there (`/root/.hermes/patches/media_rescue_patch.py`, re-applied via ExecStartPre,
  source `scripts/hermes_media_rescue_patch.py`); (2) **system_prompt rule** (read every turn):
  файлы — только в outbox, «отправил» — только после реальной отправки; (3) docs updated
  (`engineering/hermes-gateway-ux.md`). Stranded PDF hand-delivered via Bot API (`"ok":true`).
- **How to avoid (pattern):** a per-turn behavioural rule belongs in `system_prompt`, not only in
  the brain; and any safety check that silently swallows an agent's action MUST either feed an
  error back to the agent or auto-correct — otherwise the agent will confidently lie about success.

## 2026-06-10 — dotfile-blind listing → false "secrets store is empty" conclusion
- **What:** during the access audit the vault store was listed with
  `ls -la … | grep -v '^\.'` to drop `.`/`..` — which also silently dropped the `.env` files the
  store actually keeps secrets in. Conclusion "no ssh access for miramed32/liteexams, store is
  empty" went to the owner and into the changelog; the owner disproved it with the Vault UI
  (4 secrets per project were there all along).
- **Why it slipped:** the filter was written to clean cosmetic noise, and "empty output = empty
  dir" was accepted without a second look; secret stores *conventionally* keep values in dotfiles
  (`.env`), so the filter excluded exactly the expected payload.
- **How to avoid:** when checking whether a directory has content — especially a secrets/config
  store — use `find <dir> -maxdepth N` or `ls -A`, never a listing piped through a `^\.` filter.
  Before reporting "X is missing", ask: could my own filter have hidden X? Prefer a positive search
  (`find -name '.env*'`) over an eyeballed negative.

## 2026-05-30 — tar-sync didn't exclude `.env`, leaked secrets into server backups
- **What:** the early `update-knowledge` tar sync used `tar --exclude=.git .` but **not** `.env`.
  When a local `.env` (server password, etc.) appeared, it got tarred into the server and survived in
  the `agent-knowledge.*.bak` snapshots; one backup contained the prod root password in plaintext.
- **Fix:** removed all stale tar backups; the server brain is now a **git clone** where `.env` is
  `.gitignore`d, so syncs are `git pull`/`push` that physically cannot carry `.env`. Verified the
  server password now exists nowhere on the server; the Gmail App Password lives only in
  `/root/.hermes/secure/gmail_app_password` (600). Local `.env` never entered git tracked files or
  history.
- **How to avoid:** never tar the repo root without excluding secret files; prefer git transport
  (gitignore enforces it). If a tar is unavoidable, use `--exclude=.env --exclude='.env.*'` too.

## 2026-05-29 — legacy import marked "UTF-8 clean" but was mojibake
- **What:** the `agent.md` → `server-context.md` import was logged as "UTF-8 verified clean", but
  771 lines were actually double-encoded mojibake (`## Р РµРїРѕР·РёС‚РѕСЂРёР№` instead of `## Репозиторий`).
  The validator only greps for secret shapes, so garbled-but-valid UTF-8 passed silently.
- **Why it slipped:** "opens without error in UTF-8" was treated as "correct". Double-encoded text
  is still valid UTF-8 — it just renders as Cyrillic-looking noise (`Р`, `С‚`, `Рµ`…).
- **How to avoid:** when importing non-ASCII text, eyeball a known word in the result, and/or test the
  un-mojibake round-trip: if `utf8(cp1251_bytes(line))` yields cleaner text with no U+FFFD, the source
  was mojibake. Consider a `scripts/validate.py` heuristic that flags lines with a high `Р`/`С` density.
