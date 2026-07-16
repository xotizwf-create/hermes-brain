---
id: mistakes
type: log
tags: [mistakes, postmortem]
updated: 2026-07-16
secret_refs: []
---

# Mistakes

Append-only, newest on top. Concrete mistakes + how to avoid repeating them. Pulled from
incidents and review feedback so the same error doesn't happen twice.

## 2026-07-16 — Спроектировал «умную память» (дайджесты), когда владелец хотел простую механику
**Symptom (owner):** «тут ты вообще полную фигню сделал… никаких дайджестов не надо» — переделка
свежевыкаченного мягкого idle-сброса (`177fdbd`) в тот же день (`2c0381c`).
**Root cause:** жалобу «агент теряет контекст» я превратил в собственный дизайн (мягкий сброс
30м–24ч + детерминированный дайджест хвоста), не спросив владельца, какую механику он хочет.
Владелец хотел противоположное: предсказуемый полный сброс (3 ч) + ЯВНОЕ уведомление пользователю
с путём возврата («найдите сообщение → Ответить»).
**Avoid next time:** видимое поведение системы (память, сбросы, уведомления, форматы) — сначала
1-2 предложения дизайна владельцу («сделаю так: …, ок?») ЛИБО минимальная механика с явным
сигналом пользователю; «умные» неявные механизмы — только по явному запросу. Диагноз ≠ мандат на
собственный дизайн.

## 2026-07-16 — Доверился ридерам и «успеху» инструмента без пруфа записи (комментарий-результат исчез)
**Symptom:** закрыл Bitrix-задачу с result_text, инструмент вернул `comment_added=true` — а
комментария в задаче не было; ридеры (`get_task_comments`, raw `getlist`) показывали 0 и для
существующих комментариев.
**Root cause (code):** `tool_add_bitrix_task_comment` не проверял `result` id из ответа портала —
маскированный false success (тот же класс F09, который я в этот день чинил у агента). Плюс на
этом портале ридеры комментариев врут нулём в первые минуты.
**Fix:** Albery `c6195fb` — нет id → McpError с текстом портала; правило проверки обновлено в
`projects/albery/change-tracking.md`: верить ТОЛЬКО `comment_id` из ответа записи.
**Avoid next time:** каждый автоматизированный флоу, который «пишет и отчитывается», обязан
проверять пруф записи из ответа ЗАПИСЫВАЮЩЕГО вызова — не чтением вслед и не полем-успехом без id.

## 2026-06-28 — Длинный Telegram-ответ продублировался из-за retry после частичной доставки
**Symptom (owner):** одно и то же длинное финальное сообщение пришло повторно; владелец справедливо
попросил не спамить промежуточными статусами во время диагностики.
**Root cause (verified in code/tests):** Telegram adapter splits a final reply above the Telegram
message limit: edits chunk 1, then sends continuation chunks. If a continuation fails after chunk 1 is
already visible (`overflow_continuation_failed` / flood-control / transient send failure), the adapter
returned `retryable=True`. Runtime could then retry the **entire** final response, duplicating the
already delivered prefix and potentially amplifying flood-control.
**Fix (applied):** persistent idempotent startup patch
`/root/.hermes/patches/telegram_overflow_dedup_patch.py` changes that partial-overflow result to
`retryable=False` in `plugins/platforms/telegram/adapter.py` (marker: "Retrying the whole final reply
duplicates..."). Regression test updated so partial continuation failure is non-retryable while the
stream consumer still sends only the missing tail in fallback.
**Verified:** `py_compile` for the adapter/patch passes; `pytest tests/gateway/test_telegram_overflow_partial.py -q`
passes (`4 passed`). Gateway was **not** restarted blindly; restart only if a live process lacks the
marker after an update.
**Avoid next time:** any delivery path that has already made user-visible side effects must not be
reported as a generic retryable failure. Prefer partial-failure metadata + missing-tail fallback; never
retry the whole final answer after a visible prefix lands.

## 2026-06-18 (afternoon) — `compression.threshold: 0.05` was the real codex-burner (corrects the entry below)
**Symptom (owner):** «кодекс на 217 расходуется слишком быстро, ненормально». The morning fix (entry
below) moved compression back to Groq 70b but **kept `threshold: 0.05`** and claimed >12k payloads "fail
gracefully via `abort_on_summary_failure: false`". Live diagnosis on 217 showed that claim is **false**.
**Root cause (verified in the journal + `agent/context_compressor.py`):**
- `threshold: 0.05` × 320k context ≈ a **16k trigger** → the middle handed to the summarizer is ~16–17k
  tokens (observed payloads up to **17632**) → 413 **even on the 70b** (12k TPM). 0.05 can never fit 12k.
- The failure is **not** graceful: on the first aux-summary error the compressor calls
  `_fallback_to_main_for_compression`, which sets `summary_model = ""` and it **sticks for the rest of the
  session** → every subsequent compaction runs on the **main model (codex `gpt-5.5`)**.
- With codex itself at `usage_limit_reached`, compaction never succeeds → context never shrinks → the turn
  **death-spirals** (caught live: "Session compressed 40 times", "Iteration budget exhausted 60/60", 22×
  `usage_limit_reached` in 8h). That spiral — not the model id — is what burned codex.
**Fix (applied, 217):** `compression.threshold` **0.05 → 0.025** (backup `config.yaml.bak.threshold025.*`,
gateway restarted). ≈8k trigger → payload ~5–9k → fits Groq 12k → summary succeeds → codex untouched. A
smaller window also shrinks the codex context per turn = **less** codex burn, so it is strictly *more*
efficient (not "less context for nothing").
**Sizing law (hard, do not regress):** keep `auxiliary.compression` on 70b (12k) AND keep
`compression.threshold ≤ ~0.025` so the payload fits 12k. **0.05 is incompatible with free Groq and has
re-broken this twice (06-11, 06-18). Raise it only with a paid Groq Dev tier.**
**Residual:** a single >12k message in the middle can still 413 → one codex fallback (the 2026-06-16
"internal minimum" concern). Bulletproof fix = a gateway patch to fall back to the static deterministic
summary instead of codex; deferred (patch fragility). Trip-wire: `self-check` `compression_fail`.
See `engineering/hermes-gateway-ux.md` (compression section, CORRECTION block).

## 2026-06-18 — `auxiliary.compression` silently demoted to the 6k-TPM model
**Symptom (owner):** «Гермес неправильно сжимает контекст» — agent dumb/slow, chat spammed with
"Compacting context…" / "Session compressed N times — accuracy may degrade".
**Root cause:** an aux-config pass on 16-06 (`config.yaml.bak-aux-auto-20260616`) reset *every*
`auxiliary.*` task to `llama-3.1-8b-instant` (**6 000** TPM), including `compression`. Compaction
payloads are 9–12k tokens → `413 Request too large … Limit 6000` on every attempt → the middle never
summarized → context grew unbounded → repeated failed re-compaction. The journal failures were
log-only (`WARNING agent.context_compressor: Failed to generate context summary … 413`), so the chat
just "felt slow". The agent's own emergency fix (06:46) — switch `compression` → `openai-codex/gpt-5.5`
— stopped the 413s but is the documented anti-pattern (couples compaction to the main brain = blocker
#1, slow up to its 360s timeout).
**Fix (applied, 217):** `auxiliary.compression` → `provider: custom, model: llama-3.3-70b-versatile`
(12k TPM, free, decoupled), `timeout: 45`, `api_mode: ''`. `compression.threshold` kept at 0.05
(owner: prefer keeping context); 70b's 12k cap covers the typical 9–10k payload, and the rare 12k+
(real failed payloads 9892/12183/9291/12099 — half >12k) fails gracefully via
`abort_on_summary_failure: false` (skip one cycle, no message loss) — vs old 8b where *every* attempt
413'd. **⚠️ SUPERSEDED 2026-06-18 (afternoon, entry above): this is wrong — 0.05 still 413s on the 70b
(payloads up to 17632 > 12k), and the failure does NOT skip gracefully, it sticks the session onto codex.
`threshold` lowered to 0.025.** Verified the 70b id is live via openai-SDK (raw urllib → Cloudflare 1010 = false negative).
**Reconciled with the 2026-06-16 entry below** (which moved compression OFF Groq → `provider: auto`):
that call was driven by the old amplifier where a Groq TPM-reject got misclassified as a *payment*
error and disabled the WHOLE Groq aux for **600 s**. Re-checked on 217 on 2026-06-18 — today's many
413s produced only the compression-specific **60 s** pause and **zero** `marking … unhealthy` lines:
the 600 s cascade no longer fires. And `auto` here resolves to the **single openai-codex account**
(no openrouter/paid key on 217 → blocker #1, slow up to 360 s). Owner's complaint was *speed*, so on
2026-06-18 the **owner chose to keep compression on Groq 70b** (fast/free/decoupled) over `auto→codex`.
**Trip-wire:** if `marking … unhealthy (600s)` from a Groq compaction ever reappears in the journal,
revert `auxiliary.compression` → `provider: auto`.
**Avoid next time:** `auxiliary.compression`/`web_extract` (big payloads) MUST stay on 70b (12k),
never 8b (6k); after any aux-config/`hermes update` pass, re-check `grep -A2 'compression:' config.yaml`
and that compression isn't silently demoted. `self-check` already flags the `compression_fail` signature.
See `engineering/hermes-gateway-ux.md` (compression section).

## 2026-06-16 — Groq снова ломал auxiliary/compression: free-tier 12k TPM несовместим с тяжёлым сжатием
> **Обновление 2026-06-18:** этот вывод пересмотрен — амплификатор «600s unhealthy» больше не
> срабатывает (413 даёт лишь паузу 60с), а `auto` на 217 резолвится в единственный codex (медленно).
> По решению владельца сжатие возвращено на Groq 70b. Детали — в записи 2026-06-18 выше.
- **What:** hourly `hermes_selfcheck.py` alerted: `Auxiliary: marking ... unhealthy for 600s (payment /
  credit error)` and then `Failed to generate context summary: Codex auxiliary Responses stream exceeded
  45.0s total timeout`. Live config still had `auxiliary.compression` and `auxiliary.web_extract`
  on Groq `llama-3.3-70b-versatile`; real compression requests in ordinary long Telegram sessions
  exceeded Groq's free-tier 12k tokens/min cap, so Groq returned a hard 413/rate-limit style error.
- **Why the 06-11 fix was insufficient:** lowering `compression.threshold` and `protect_last_n` reduces
  frequency/size, but Hermes still has an internal minimum context window for compression. Therefore a
  long enough session can still produce a payload above Groq free-tier TPM. Do **not** keep trying to
  fix this by shaving percentages.
- **Fix applied:** removed Groq from heavy auxiliary roles (`auxiliary.compression` and
  `auxiliary.web_extract` now use `provider: auto`), kept Groq only for small auxiliary tasks/titles;
  `hermes config check` passes. Also changed `hermes_selfcheck.py` so after a config repair it starts
  its journal window no earlier than the config mtime, avoiding one extra stale hourly alert while still
  catching new post-fix failures.
- **Operational note:** before restarting Hermes gateway, run server preflight. This incident also found
  `/` at 99%; cleaned old `/tmp` workdirs and vacuumed journal, freeing ~1.7 GB. Low disk can masquerade
  as agent flakiness too.
- **How to avoid:** if Groq free-tier appears in any heavy auxiliary path (compression, large extraction,
  summarisation), treat it as misconfigured unless there is a paid/larger-limit key and a live long-context
  test. Groq 8b/70b is fine for short title/approval helpers, not for guaranteed compression reliability.

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
