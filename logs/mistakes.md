---
id: mistakes
type: log
tags: [mistakes, postmortem]
updated: 2026-06-14
secret_refs: []
---

# Mistakes

Append-only, newest on top. Concrete mistakes + how to avoid repeating them. Pulled from
incidents and review feedback so the same error doesn't happen twice.

## 2026-06-14 — Status audit (are past mistakes actually fixed?)
Reviewed every entry below + verified live on the server:
- **Росреестр/НСПД (06-14)** — ✅ fixed: tools shipped (`nspd_parcels_local.py` complete via tiling,
  `nspd_parcels.py` fallback), verified 329 objects. Only the server-side 24/7 automation is open
  (needs a RU residential proxy — owner decision, not a bug).
- **«Модель долго работала» cascade (06-11)** — ✅ fixed for normal ops, ⚠️ residual. Verified: the
  06-11 config fix is live (`compression.threshold 0.05`, `protect_last_n 10`, `compression.timeout
  45`, aux split 8b/70b). The 53× "unhealthy" + 28× compression-fail counts in the journal are **all
  from one day** — today's Росреестр storm — and **zero on every other day**, i.e. normal operation
  has been clean for a week. The storm's trigger (the agent flailing into a pathological huge context)
  is now removed by `brain_search` + ready tools. **Residual amplifier:** a Groq free-tier TPM/size
  rejection is still classified as a "payment error" and disables the WHOLE Groq aux for 600 s — a
  free-tier limitation, not a blind-patchable bug. Full elimination needs either a paid/larger
  compression provider or a tested patch to `auxiliary_client._is_payment_error` — owner's call.
- **PDF /root denylist (06-11)** — ✅ fixed & robust: rescue patch present AND **re-applied on every
  start** via `ExecStartPre` (`apply_patches.py` + `media_rescue_patch.py`); 0 media drops in 7 days.
- **dotfile-blind listing (06-10)** — behavioural lesson, no code to fix; guidance stands (use
  `find`/`ls -A`, never a `^\.` filter when checking if a store has content).
- **.env tar leak (05-30)** — ✅ fixed: `.env`/`.env.*` gitignored, absent from git history, server
  clone tracks 0 `.env`, no stale `.bak` snapshots. Git transport physically can't carry it.
- **Mojibake import (05-29)** — ✅ now fully closed: the "consider a validate.py heuristic" to-do is
  **implemented** — `check_mojibake()` flags any doc where `Р`+`С` exceed 25 % of Cyrillic (real
  Russian <7 %, mojibake ~90 %); calibrated + tested both ways, no false positives on the real brain.

## 2026-06-14 — Росреестр/НСПД: 1.5 часа на участки в радиусе 100 м, выдал 9 вместо десятков
- **What:** owner asked for all land parcels within 100 m of `18:30:000423:1789` (Сарапул) as an
  Excel. The agent flailed for ~1.5 h across several compaction-split sessions, delivered a table
  with only **9 участков**, then kept retrying: dozens of dead DDGS web-searches, `web_extract`
  errors (ddgs backend can't extract URLs), `pynspd` cache-arg crash, direct `nspd.gov.ru`/
  `a.nspd.su`/`pkk.rosreestr.ru` hits and a `browser_navigate` — all timing out (300/240/80 s each)
  — and finally hit the tool-iteration cap with no usable result.
- **Why it failed (root causes):**
  1. **nspd.gov.ru / pkk.rosreestr.ru are IP-blocked for our servers.** Confirmed 2026-06-14:
     `http=000` even via the Russian `eth0` (217.198.12.236). НСПД blocks datacenter IPs in
     general; the owner's hunch "route not through the эстонский IP" doesn't help. (217 egresses
     through the `awg0` VPN → `95.85.243.43`, geo CZ.) The official site is simply unreachable
     from the box — every direct probe is a guaranteed multi-minute timeout.
  2. **The agent never opened its own skill** `research-intelligence-workflows /
     references/russian-cadastral-parcel-extraction.md`, which already documented the working
     public mirror. It opened `document-production-workflows` instead.
  3. **No ready-to-run tool** → it hand-built the geometry/Excel pipeline from scratch each turn
     under the iteration cap, and ran scripts with `/usr/bin/python3` (the terminal tool's python,
     which has **no shapely/pyproj/openpyxl** — only the hermes venv does), so geo steps died.
  4. **Method bug:** distances/buffer in raw EPSG:3857 (×1.8 scale error at 56°N → "100 m" ≈ 55 m)
     and from the centre, not the boundary → undercount.
- **Public mirror = partial only.** `scripts/nspd_parcels.py` uses the `kadastrmapp.online`
  mirror (the one source reachable from the VPN egress) with the 3857→UTM + boundary-buffer
  method. But the mirror's `api.php` is **hard-capped at 81 objects/quarter and ignores
  pagination**, while the quarter actually holds 173 land parcels + 156 buildings + ... — so it
  can only ever return a slice (~13 land / 28 objects here). Keep it as a best-effort fallback,
  not the source of truth.
- **The COMPLETE solution (done + verified 2026-06-14): official НСПД spatial search via `pynspd`,
  run from a Russian RESIDENTIAL IP.** See `scripts/nspd_parcels_local.py`.
  - НСПД blocks datacenter/foreign IPs, so it needs a RU residential/mobile egress. We don't have
    one on the server; for this run we used the **owner's home PC with AmneziaVPN turned off for
    ~2 min** (its real RU home IP). A detached "armed" capture script polled НСПД by DIRECT IP
    (`2.63.246.75`, DNS-free — DNS dies when the VPN drops) and ran the instant the path opened, so
    the Claude session dropping during the VPN-off window didn't matter. (A route-only split-tunnel
    does NOT work: WireGuard's kill-switch WFP blocks untunneled traffic.)
  - **Critical gotcha — silent 300 cap:** `pynspd.search_*_in_contour` sends ONE
    `/api/geoportal/v1/intersects` POST and НСПД **silently truncates at ~300** (no error, so the
    library's built-in recursive splitter never triggers). You MUST tile yourself: recursively
    split the bbox into quadrants, re-querying any tile that returns ≥~250 or raises `TooBigContour`,
    dedupe by `cad_num`, then filter by real boundary distance. `nspd_parcels_local.py` does this
    (`collect_complete`). Result: **329 objects = 299 land parcels + 30 buildings** within 100 m
    (vs the capped 300 / the mirror's 13 / the agent's original 9).
  - `pynspd` returns lon/lat (EPSG:4326); reproject to local UTM (Удмуртия = 32639) for metres.
    Use `Nspd(client_dns_resolve=True, client_retry_on_blocked_ip=True)` in IP-mode.
- **To automate on the server (any user, 24/7):** give the agent a RU residential/mobile **proxy**
  and call `Nspd(client_proxy=...)`; store the proxy secret in the secure zone. A RU VPS/datacenter
  proxy will NOT work (still blocked).
- **Avoid next time:** for Росреестр/кадастр/НСПД — use `nspd_parcels_local.py` (pynspd, tiled,
  from a RU residential IP/proxy), venv python; treat the mirror script as fallback only; never
  trust a single intersects call (cap 300); never probe nspd.gov.ru directly from a datacenter IP;
  never measure in raw 3857.

## 2026-06-11 — «модель ОЧЕНЬ долго работала» на prostavki-MCP: каскад из трёх невидимых поломок
- **What:** the owner's prostavki MCP-надстройка session crawled for ~2 hours. Journal showed the
  cascade: (1) every prompt logged `Context file SOUL.md blocked: exfil_curl` — the 06-06 advice
  line in SOUL (`curl … bot$TOKEN/sendDocument`) tripped the threat scanner, which **silently drops
  the whole SOUL.md from every prompt** (so the agent also lost the «файлы в outbox» rule → the PDF
  incident the same day); (2) context compression payloads (~70k tokens at `threshold: 0.2`) can
  NEVER fit Groq free tier (llama-3.3-70b = 12 000 tokens/MIN; one oversized request is rejected
  outright) — the aux client read that as a payment error and marked the whole Groq provider
  unhealthy for 600 s, killing titles/approval too; (3) compression then fell back to the codex aux
  (the main ChatGPT brain) which hit its 120 s stream timeout per attempt, session «compressed»
  13+ times degraded — each turn dragged an ~86k-token prompt plus minutes of summary timeouts.
- **Why it slipped:** all three failures are log-only — chat looked normal, just slow; and the
  06-06 «fix» (delivery advice in SOUL) introduced failure (1) itself: nobody re-ran the threat
  scanner over SOUL after editing it.
- **Fix (2026-06-11):** SOUL line reworded (no curl+$TOKEN shape; scanner-verified clean);
  `compression.threshold` 0.2→0.05 и `protect_last_n` 20→10 (small fast working context, payload
  fits Groq), `auxiliary.compression.timeout` 120→45; aux split: small tasks → llama-3.1-8b-instant,
  compression/web_extract → 70b. Live-verified: compression call 1.4 s, titles 0.3 s.
- **How to avoid (patterns):** (1) после правки SOUL/контекстных файлов прогоняй threat-scanner;
  (2) any aux task's worst-case payload must fit the provider's per-minute token cap — проверяй
  `x-ratelimit-*` headers, не только «ключ работает»; (3) «агент тупит/тормозит» → first grep the
  journal for `blocked:`, `unhealthy`, `Failed to generate context summary`, `Preflight compression`.

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
