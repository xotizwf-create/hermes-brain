---
id: changelog
type: log
tags: [changelog]
updated: 2026-06-14
secret_refs: []
---

# Changelog

Append-only, newest on top. Every approved change to the brain gets one line.
Ротация: записи прошлых месяцев уходят в `archive/changelog-YYYY-MM.md`, когда лог разрастается.

## 2026-06-15
- **Простые поставки — импорт входящих контрактов: нулевая цена.** Зафиксирован инцидент по MCP-обработке входящих документов: импортер мог сохранять цену в `form_snapshot.items[].price`, а backend ожидал её в `total`, из-за чего карточки показывали `items[].price = 0`. На production нормализованы контракты №424 и №0363300044326000058, backend поддерживает оба формата snapshot, кодовый коммит проекта: `93fd160`.

## 2026-06-14
- **Albery — наблюдаемость как у Hermes brain (self-check на 186).** У Albery были те же молчаливые
  сбои, но за ними никто не следил (за 7д: codex-лимит 11×, Groq unhealthy 78×, сжатие 8×, медиа-дроп 1× —
  диагностировали вручную). Перенёс `hermes_selfcheck.py` на 186 + ежечасный no-agent cron `self-check`
  (`4e496f64fade`, доставка Александру `telegram:1451982360`, тихо если чисто). В скрипт добавлена CRIT-
  сигнатура **codex usage-limit** (`usage_limit_reached`) — killer Albery (один аккаунт без фолбэка);
  полезно и для 217. Read-only диагностика 186 — preflight чист (~1.1ГБ free, swap, load 0.08).
- **Аудит всех прошлых ошибок (mistakes.md) — проверено вживую, что пофикшено.** Итог в шапке
  `logs/mistakes.md`: Росреестр ✅, медиа-дроп ✅ (rescue-патч + авто-переприменение, 0 дропов/7д),
  .env-утечка ✅ (gitignore, нет в истории/бэкапах), mojibake ✅ — **дореализована** эвристика
  `check_mojibake()` в `validate.py` (флагует доки, где `Р`+`С` >25% кириллицы; откалибрено,
  ложных нет). Каскад «модель долго работала» — фикс 06-11 живой, в норме 0 сбоев/неделю; все 53×
  «unhealthy» сегодня — это росреестровский шторм, чей триггер убран фиксом #1; остаточный
  амплификатор (Groq TPM→600с) — ограничение free-tier, нужен RU-прокси/платный провайдер сжатия
  или патч `_is_payment_error` (решение владельца).
- **Все навыки теперь в GitHub (бэкап «заводского» дерева).** Встроенная библиотека навыков Hermes
  (`/root/.hermes/skills/`, не в git) и наши правки в ней (кадастровый навык) могли пропасть при
  переустановке Hermes. Залиты в репозиторий под `vendor-skills/` (55 навыков, 151 .md; исключён
  мусор — `.archive`/бэкап-тарболы). `scripts/sync_vendor_skills.py` — пересинхронизация (rsync,
  запускать на сервере из `agent-knowledge/scripts/`, дальше коммит/вотчдог). `validate.py` пропускает
  `vendor-skills/` (чужой frontmatter не ломает проверку). Риск «правки в заводском дереве не
  версионируются» закрыт.
- **Агент «умнее»: ретрив + наблюдаемость + петля обучения (пп.1–4).**
  (#1) `scripts/brain_search.py` — единый поиск по ОБОИМ деревьям (versioned brain + bundled
  `/root/.hermes/skills`), SQLite FTS5 + триграммы, ранжирование по типу; INDEX.md велит искать
  ПЕРЕД выбором навыка. (#2) `scripts/hermes_selfcheck.py` + hourly cron `self-check`
  (`e473bdb3d674`, no-agent): ловит молчаливые сбои (SOUL-blocked / token_invalidated /
  provider-unhealthy / compression-fail / media-drop) → Telegram, тихо если чисто. (#3,#4)
  В `update-knowledge` зашита «петля само-улучшения»: искать перед действием, повторяемое
  оформлять СКРИПТОМ, сбои → mistakes.md с конкретным триггером/инструментом. Вывод по RAG:
  корпус ~650 док → лексика бьёт вектора; эмбеддинги отложены (как pgvector в Albery).
- **Росреестр/НСПД — полное извлечение участков в радиусе + разбор провальной сессии.** Агент
  1.5 ч искал участки в радиусе 100 м (`18:30:000423:1789`) и выдал 9: прямой nspd.gov.ru/pkk
  заблокирован для датацентровых IP (подтв. `http=000` даже через RU eth0), публичное зеркало
  capped на 81/квартал, геометрия считалась в сыром 3857 не тем python. Полное решение —
  `scripts/nspd_parcels_local.py`: официальный НСПД через `pynspd` с **российского резидентного IP**,
  пространственный поиск «в контуре» с **тайловым дроблением против молчаливого потолка 300**
  (`/intersects` режет на ~300 без ошибки), 3857/4326→UTM, буфер от границы. Проверено: **329
  объектов (299 ЗУ + 30 ОКС)** против 9/13. RU-IP добыт временным отключением AmneziaVPN на ПК
  владельца (detached capture по прямому IP, DNS-free); для автоматизации на сервере — RU
  резидентный/мобильный прокси (`client_proxy`). `scripts/nspd_parcels.py` (зеркало) оставлен как
  fallback. Постмортем в `logs/mistakes.md`; навык research-intelligence-workflows обновлён.
- **Albery — гибридный поиск по знаниям компании (ступень 1 RAG-плана, в проде).**
  `search_company_knowledge` был чистый `ILIKE` → не понимал русскую морфологию, часто возвращал
  пусто, хотя документ есть. Переписан на гибрид: русский FTS (`to_tsvector('russian', name||content)`)
  + триграммы `pg_trgm` (similarity) + ILIKE; ранжирование `ts_rank_cd` + similarity + бонус за точное
  имя; fallback на ILIKE до миграции. Миграция `026_company_folders_fts.sql` (stored `content_tsv` +
  GIN `idx_company_folders_content_tsv`), зарегистрирована в `ensure_postgres.py`. Albery-репо коммит
  `9b56146`. **Деплой backend-only** (git pull + `ensure_postgres.py` + рестарт `albery`, БЕЗ
  `update_server.sh`/сборки фронта — правило №7, бокс ~1 ГБ). Проверено на проде через реальный код:
  «фиксация результатов» 0→16 релевантных, топ `Регламент_фиксации_результата`. Обновлены
  `projects/albery/owner-reports.md` (правило 3) и `server-mcp-tools.md`. Ступень 2 (pgvector/эмбеддинги
  для синонимов) отложена по решению владельца.

## 2026-06-11
- **First CI contour for `prostye-postavki`** (PR #1, merged to main) — making the agent's coding
  verifiable instead of "looks right". `.github/workflows/ci.yml`: backend-smoke (a `postgres:16`
  service + `pytest backend/tests`: app boots against a real DB, `/api/health`, pure-helper units),
  frontend-build (`vite build` = typecheck), and a non-blocking legacy vitest job (step-level
  continue-on-error + `::warning`). All required checks green; verified frontend build locally and the
  backend suite in CI. Findings: backend is **FastAPI, not Flask** (corrected `overview.md`); module
  import does `ensure_*_schema()` so it needs Postgres; two legacy parsing tests
  (`contractParsing`/`specPipeline`) were already broken (assert quantity-like `price`, parser returns
  "") — surfaced, not papered over. New brain rule in `engineering/testing.md`: a coding task isn't
  done until CI is green; branch→PR→read `gh pr checks`→merge; never make CI green by weakening a test;
  heavy suites run off-box. This is the reference template for onboarding future projects.
- Albery agent crash-resilience (owner: no Gemini) — found the real crash-storm cause: the
  `hermes-gateway.service` unit on 186 declares `RestartSteps`/`RestartMaxDelaySec` (systemd ≥254),
  but the host runs **systemd 249** which silently ignores them → no restart backoff → on a codex
  `token_invalidated` 401 the gateway respawned every `RestartSec=5s` in a tight loop (= the "22
  crashes" of 06-08/09, not 22 separate incidents). Fix: removed the dead keys, `RestartSec=30`
  (gentle self-heal), backup `hermes-gateway.service.bak.nogemini_*`. Set
  `credential_pool_strategies.openai-codex: fill_first`. The codex account itself is healthy
  (dedicated, refresh-token auto-refreshing) — so it shouldn't 401 again from session conflicts.
- **Removed Gemini from the Albery project** per owner: dropped `GOOGLE_API_KEY` from
  `/root/.hermes/.env`, purged the cached `gemini` credential from `auth.json`, `fallback_providers:
  []`; verified "GEMINI GONE", codex intact, gateway stable. (Gmail/Workspace OAuth untouched — that's
  a separate credential.) Honest caveat recorded: with one account and no fallback, a genuinely revoked
  token still needs a manual re-add; resilience here = healthy dedicated account + gentle auto-restart.
- Audited & tuned the **dedicated Albery Hermes agent** — and corrected a long-standing brain error:
  it runs on **186.246.7.32** (Timeweb, 2 GB RAM), NOT 217 (m4s.ru/mcp.m4s.ru → 186 by DNS). 217 is
  the separate general Hermes Brain box. Fixed `projects/albery/servers.md`; access is in the 217
  vault `/opt/hermes/secure/projects/albery/.env` (reached via `sshpass -f` jump from 217).
- Applied the same audit fixes the 217 agent got (backup `config.yaml.bak.audit_*`, gateway verified
  stable 90 s post-change, RAM 1 GB free): **Telegram reactions ON** (`telegram.reactions: true` —
  the 👀→👍/👎 lifecycle the owner wanted; was `false`); auxiliary text tasks → groq custom endpoint
  (`${GROQ_API_KEY}` in a 600 secure env file + systemd drop-in `40-groq-env.conf`; key was
  commented-out/absent on 186, so compression/aux ran on broken `auto`); **STT** `local`
  (faster-whisper, RAM risk) → **groq** `whisper-large-v3-turbo`; **web search** empty → `ddgs`
  (installed). Caught & reverted my own bug: the apply loop had also pointed the `vision` aux task at
  text-only llama-3.3-70b (would break chat-OCR `process_chat_ocr`) — reverted `vision` → `auto`.
- Albery agent open risks (flagged, not yet fixed): single `openai-codex` account, no failover → a
  `token_invalidated` 401 crashes the gateway (22 crashes 2026-06-08/09); a **Gemini API key is
  present and unused** — adding it as `fallback_providers` would stop the crash-on-401. «Smarter»
  report quality lives in the Albery report contracts/prompts (business logic) — left untouched.
- Recorded in `projects/albery/servers.md`; resolves the CLAUDE.md open task «reconcile stale 217
  references in albery docs».

## 2026-06-10
- VK voice-message pitfall documented in `skills/vk-hermes-bridge-mvp`: TTS may produce `.mp3`, but VK voice bubbles need OGG/Opus via `docs.getMessagesUploadServer?type=audio_message`; convert with `ffmpeg` first and fail cleanly if VK returns an empty upload `file` instead of calling `docs.save` with a bad value.
- Documented Telegram status reactions (the 👀→👍/👎 lifecycle the owner loved): built-in, enabled by
  `telegram.reactions: true`; spec in `engineering/hermes-gateway-ux.md` («Реакции-статусы»).
- Voice stress: edge-TTS honors the U+0301 acute mark (verified — за́мок/замо́к render differently),
  so correct stress is now driven from the TTS text — SOUL voice rule asks the agent to mark
  homographs/ambiguous words. Tested `ruaccent` (ML accentuation) in an isolated memory-capped venv
  and rejected it for this 1 GB box: peak RSS 761 MB + ~92 s cold load = OOM risk / starves RAM, and
  tiny model still misreads homographs; removed. «Robotic» timbre is inherent to free edge — real
  upgrade = cloud TTS (ElevenLabs / Gemini free tier), offered as a next step. Documented in
  `engineering/hermes-gateway-ux.md` («Голос: ударения и натуральность»). SOUL backup `*.bak.stress_*`.
- VK ↔ Telegram parity audit + fix: control is identical (same Hermes agent behind the bridge). Added
  `upload_vk_audio_message` to `/opt/vk-hermes-bridge/vk_bridge.py` so the agent's `.ogg/.opus` TTS
  goes out as a VK **voice message** (was a plain doc) — matching the Telegram voice bubble; surgical
  edit, `py_compile` OK, only `vk-hermes-bridge.service` restarted, backup `vk_bridge.py.bak.audiomsg_*`.
  Remaining non-parity is platform-inherent (no VK reactions for community bots; VK is an external
  bridge, not a native gateway). Recorded in `skills/vk-hermes-bridge-mvp` («VK ↔ Telegram»).
- Voice replies enabled end-to-end: `tts.edge.voice` en-US-AriaNeural → **ru-RU-DmitryNeural**
  (edge, free, ffmpeg present); audio cache dirs added to `gateway.media_delivery_allow_dirs`
  (else MEDIA voice files are silently dropped — the 06-06 gotcha); SOUL rule «Голосовые ответы»
  (when asked, speak via `text_to_speech` → MEDIA .ogg; conversational text, <1 min, confirm
  delivery, fall back to text honestly). Verified live: generated Russian .ogg via the real tool and
  delivered to the owner's Telegram (`sendVoice` ok:true, msg 4686). Backups `config.yaml.bak.voice_*`,
  `SOUL.md.bak.voice_*`. Documented in `engineering/hermes-gateway-ux.md» («Голосовые ответы»).
- Subagents enabled in practice: the built-in `delegate_task` orchestrator–workers tool was never
  used (0 calls in 14 days — nothing told the agent when). Added a SOUL rule (when to
  delegate / when not / how to brief a worker: one goal, needed toolsets only, done-criterion,
  forbidden zones; parent owns the result) + `engineering/agent-team.md` §4.5 («Встроенные
  субагенты») — ephemeral workers instead of permanent bots/gateways (the 04.06 anti-pattern).
  Config: `delegation.child_timeout_seconds` 600→1800 (workers were being killed mid-task, same
  bug as the main loop), deep profile 600→1800, review 420→900. Bonus UX: `telegram.reactions:
  true`. Backup `config.yaml.bak.delegation_*`, `SOUL.md.bak.subagents_*`.
- Context management made fully automatic (no owner confirmations): `compression.threshold`
  0.5 → 0.2 so the compressor summarises early and silently (groq aux, last 20 messages verbatim);
  `telegram_context_guard.enabled: false` — the «Сжать контекст?» button prompt was a band-aid from
  the broken-compression era. Topic changes: no built-in detector exists; covered by `session_reset`
  (idle 30m + daily 04:00) and manual `/new`. Documented in `engineering/hermes-gateway-ux.md`
  («Context: автосжатие и жизнь сессий»). Backup `config.yaml.bak.autocompress_*`.
- Fixed «auxiliary compression provider 'groq' is unavailable»: Hermes has no first-class `groq`
  provider — all 9 `auxiliary.*` tasks now use `provider: custom` + `base_url:
  https://api.groq.com/openai/v1` + `api_key: ${GROQ_API_KEY}` (env reference expanded by the config
  loader; key stays only in `/root/.hermes/secure/hermes-gateway.env`, 600). Verified end-to-end via
  a direct `call_llm` test; new gateway process logs clean. Gotchas documented in
  `engineering/hermes-gateway-ux.md` («Auxiliary LLMs … on Groq»).
- CORRECTION to the access-audit note below: the per-project secrets DO exist — each
  `/opt/hermes/secure/projects/<slug>/` holds a `.env` (gov-exams-app, albery, prostye-postavki,
  hermes-brain; visible in the Vault UI). The earlier "store is empty / no ssh access" conclusion was
  an auditing mistake: the directory listing was piped through `grep -v '^\.'` to drop `.`/`..`,
  which also hid the `.env` files. Recorded in `logs/mistakes.md`; SOUL project rule now says
  explicitly that project secrets live as `.env` inside the project's vault folder.
- Autonomy rules pinned to SOUL.md (always-loaded layer, backup `SOUL.md.bak.projectrules_*`):
  (1) «Работа с проектами» — any task naming a project starts from `projects/registry.yaml` →
  `projects/<slug>/` card; access resolution order: card → `/opt/hermes/secure/projects/<slug>/` +
  `/root/.hermes/secure/` → gh → project MCP; ask the owner only for a concretely named missing
  credential and store it via `store-project-secrets` so it's the last time. (2) «Расширение системы =
  задокументировано» — a new channel/bot/service/integration/MCP/cron isn't done until the knowledge
  is written to the brain (nearest instruction or a skill in git) in the same dialog, unprompted.
  Reason: both rules existed only in skills the agent reads on-demand (chicken-and-egg, e.g. the VK
  bridge built 2026-06-09 was documented only after the owner asked).
- Migrated skill `vk-hermes-bridge-mvp` from the server-local skills dir into the brain
  (`skills/vk-hermes-bridge-mvp/`, canonical in git); local copy archived to avoid ambiguous skill
  matches; routed in `INDEX.md`. Gap found during access audit: the secure zone has gh/Gmail/Google/
  Groq credentials but NO ssh access for `miramed32.ru` (prostye-postavki) or `liteexams.ru`
  (gov-exams-app) — agent can reach code (GitHub) and data (MCP) but not those prod servers.
- Weekly `self-review` cron extended: also detect system changes from the past week that were never
  reflected in the brain and propose the missing docs/skills.
- Runtime audit applied to prod gateway (owner-approved, backup `config.yaml.bak.audit_20260610_102335`): `web.search_backend: ddgs` (instant keyless web search instead of hand-rolled scraping; Chrome stays for interactive logins like hh.ru), `task_wall_timeout_seconds` 600→2400 and `terminal.timeout` 180→300 (tasks were being killed mid-flight 5×/week), all auxiliary text chores (compression/title/skills_hub/approval/web_extract/triage/kanban/profile/curator) pinned to `groq llama-3.3-70b-versatile` with a fresh `GROQ_API_KEY` (key existed nowhere before — context compression and voice STT were silently broken), `skills.external_dirs → /root/.hermes/agent-knowledge/skills` (brain skills now natively visible to the skill matcher), `approvals.mode: smart` + cleared `command_allowlist` (it had pre-approved `git reset --hard`, recursive deletes, bare SQL DELETE), `sessions.auto_prune: true`, weekly `self-review` cron (Mon 10:00 МСК: digest of the week's agent errors → owner + proposed brain edits via approval flow), 25 stale `.bak` files moved to `_bak_archive_20260610`, `state.db` checkpointed/vacuumed, Telegram bot tokens removed from the OneDrive-synced local `.env` (canonical copies live in `/root/.hermes/profiles/*/.env`).

## 2026-06-06
- Fixed Telegram file/attachment delivery: `gateway.media_delivery_allow_dirs` was empty, so every attachment was silently dropped (`Skipping unsafe MEDIA directive path`) — the agent falsely reported «отправил» and hung on retries. Set allow-dirs to `[/root/audits, /root/.hermes/outbox, /tmp]`, documented the gotcha + a verify-delivery rule in `engineering/hermes-gateway-ux.md`, and pinned a SOUL rule (write deliverables to an allowed dir, never claim sent without confirmation; for hard-confirmed binaries use Telegram `sendDocument` and check `ok:true`).
- Corrected `projects/prostye-postavki/` documentation after production/GitHub reconciliation: source repo is `xotizwf-create/prostavki`, live code is `/var/www/prostye-postavki/app`, service is `prostye-backend.service`, and project deploy rules now require GitHub `main` to match the production checkout after any server-side change.

## 2026-06-05
- Added skill `skills/project-audit/`: audits an existing project (repo + live prod, read-only) and lays it out по полочкам — a plain-language human summary plus structured docs (overview/structure, architecture, database, api & integrations, runbook) with Mermaid diagrams, unknowns flagged `❓ не подтверждено`, secrets as references only, then registers via add-project. Approach informed by the community `codebase-onboarding` skill + brain `projects/_template/` and schema. Routed in `INDEX.md`.
- Added skill `skills/karpathy-guidelines/` (vendored from `multica-ai/andrej-karpathy-skills`, MIT): four behavioral rules to reduce common LLM coding mistakes — Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution. Derived from Andrej Karpathy's observations on LLM coding pitfalls. Routed in `INDEX.md`; pairs with `engineering/agentic-coding.md` and `aislop-code-quality`.
- Wired karpathy-guidelines into the agent's workflow so it knows when to apply it: sharpened the skill `description` with explicit triggers (use on any non-trivial write/edit/refactor/review/debug; skip trivial/non-code) + added a "When to use" section; added it as the first hard rule in `engineering/agentic-coding.md`; published to the native Hermes skill registry (`/root/.hermes/skills/software-development/karpathy-guidelines`) so it shows in `hermes skills list` and is auto-surfaced.

## 2026-06-04
- Recorded Albery's critical Bitrix dependency in `projects/albery/overview.md`: an active Bitrix Marketplace subscription is mandatory; without it, message delivery and pulling information from Bitrix may stop working.
- Implemented the notifications channel: all cron/reminder/watcher deliveries now route to the Telegram group «Уведомления» (`chat_id -5120862157`) via `TELEGRAM_HOME_CHANNEL` + per-job `origin` redirect; the owner's DM (`1451982360`) stays clean for dialogue. Verified `hermes send` → group = sent. Recorded in `engineering/agent-team.md`.
- Made the Уведомления group interactive: `require_mention: false` + `observe_unmentioned_group_messages: true` + `allowed_chats`/`group_allowed_chats` for `-5120862157` so the single main bot answers without `@` (natural «да, ставь» approvals); pinned a SOUL rule that reminders/cron/automations deliver only to that group and feedback happens there. Owner verified both chats work.
- Added `engineering/agent-team.md`: grounded multi-agent build guide synthesized from three authorities — Anthropic "Building Effective Agents", Microsoft Azure Architecture Center "AI Agent Orchestration Patterns" (2026-05), and 12-factor-agents — adapted to the Главный+Темур design (one workflow = one agent, orchestrator+workers, own-your-context, checklist before adding an agent). Records the 2026-06-04 decision: notifications = a delivery channel (separate Telegram chat, same main bot), not a second agent. Routed in `INDEX.md`.

## 2026-06-03
- Added Andigital remote-PC fast-search guidance: prefer focused MeshCentral RunCommand/PowerShell queries for windows, processes, files, and text before visual desktop browsing; recorded the owner PC display alias as `ПК-Александр`.
- Added Andigital MeshCentral internal-panel theming guidance: use `custom.css`/`custom.js` for a modern cosmetic layer only, without changing auth, websocket/agent paths, cookies, permissions, or local-consent safeguards.
- Closed the previously dirty `projects/albery/hermes.md` Zoom-watchdog documentation update: it records
  the live 5-minute no-agent check, detached protected worker, separate worker lock, 900-second retry
  cooldown, and "mark processed only after successful worker completion" behavior.
- Added a dirty-brain safety rule to `skills/update-knowledge`: every self-edit starts with a clean
  git-state check, resolves unrelated dirty files first, commits only intended files, pushes, and
  verifies the repo is clean before final response.
- Added server-side watchdog script `/root/.hermes/scripts/brain_dirty_watchdog.py`: silent when the
  brain repo is clean, Telegram alert when uncommitted brain changes remain, throttled per dirty state.


_Записи за май 2026 (bootstrap-эра, создание мозга) вынесены в [archive/changelog-2026-05.md](archive/changelog-2026-05.md) для компактности живого лога._

- 2026-06-03: Secured Andigital MeshCentral human UI behind `/andigital/pc/<secret>/` hash-check gate; root UI closed; secret URL stored only in project env secrets.
- 2026-06-05: Albery — authored a new owner-weekly report contract in the live AI-instruction layer
  (`Формирование отчетов / Еженедельный отчет по компании`, via `upsert_ai_instruction` → prod DB):
  team verdict + meeting-rhythm + regulation compliance + per-leader accept/partial/reject format.
  Encoded two hard rules from owner feedback — identity by transcription not Zoom metadata (no false
  "not under real name"), and owner (Александр) must never be the responsible in the decisions table.
  Also: read «О компании» by file name, not multi-word keyword search. Regenerated + saved test
  weekly report 01.06–05.06 (v3, current). Recorded in brain: new `projects/albery/owner-reports.md`.
- 2026-06-05: Albery Hermes — disabled the interactive command approval gate at owner's request:
  `/root/.hermes/config.yaml` `approvals.mode: manual` → `off` (yolo-equivalent), gateway restarted.
  codex no longer prompts «Command Approval Required»/Tirith security-scan; HARDLINE blocklist still
  unbypassable, agent still can't edit its own config.yaml/.env. Backup `config.yaml.bak.1780671169`.
  Documented in `projects/albery/hermes.md`. Also set global Claude Code permission policy
  (`~/.claude/settings.json`): allow all except external-send tools + `git push`.
- 2026-06-11: Hermes (217) «отправил PDF» 4 раза, файл не доходил — в нестрогом режиме весь /root
  в hardcoded-denylist доставки вложений, дроп молчаливый (модель не видит ошибку и врёт «отправил»).
  Fix: (1) rescue-патч шлюза — location-only-отказ свежего (≤30 мин) некредентного файла теперь
  копирует его в /root/.hermes/outbox и доставляет (`scripts/hermes_media_rescue_patch.py` →
  `/root/.hermes/patches/media_rescue_patch.py`, ExecStartPre, переживает hermes update; юнит-тест:
  свежий /root-файл спасается, config.yaml/.env/старые — нет); (2) правило в system_prompt: файлы
  только в outbox + не утверждать «отправил» без реальной отправки; (3) PDF довезён владельцу
  напрямую через Bot API (ok:true, message_id 5081). Документация: engineering/hermes-gateway-ux.md,
  logs/mistakes.md. Бэкапы на 217: config.yaml.bak-2026-06-11, patches/base.py.bak-2026-06-11.
- 2026-06-11: Разбор «модель очень долго работала» (prostavki MCP-сессия ~2 часа). Три причины, все
  log-only: SOUL.md целиком выпадал из промптов (exfil_curl на curl+$TOKEN-строке от 06-06);
  payload сжатия ~70k токенов никогда не влезал в Groq free (70b = 12k токенов/мин) → провайдер
  «unhealthy 600s» гасил все aux-задачи → fallback на codex со 120s-таймаутами, 13+ деградированных
  сжатий. Fix: SOUL переписан (scanner-clean), compression.threshold 0.2→0.05, protect_last_n
  20→10, aux compression timeout 45s; мелкие aux → llama-3.1-8b-instant, compression/web_extract →
  70b. Проверено вживую: compression 1.4s, titles 0.3s. Бэкапы: config.yaml.bak-speedfix-2026-06-11,
  SOUL.md.bak-speedfix-2026-06-11. Док: engineering/hermes-gateway-ux.md, logs/mistakes.md.
- 2026-06-11: Починена отправка почты («не смог отправить вакансии Тимуру»). Причина: хостер 217
  блокирует ВЕСЬ исходящий SMTP (25/465/587 к любым серверам) — himalaya send падал «Connection
  refused» после 135s; локальный файрвол ни при чём. Решение: Gmail API по HTTPS — добавлен скоуп
  gmail.send (re-consent на ПК, токен на оба пути, 600), новый скилл skills/send-email
  (scripts/gmail_send.py: --to/--cc/--bcc/--subject/--body/--attach/--html, успех = «SENT id=»);
  нативный скилл email/send-email в хабе + предупреждение в email/himalaya («отправка тут не
  работает»). Протестировано: текст и PDF-вложение доставлены (SENT id=19eb80d5…, 19eb80db…).
  INDEX-роутинг добавлен; google-account скилл обновлён (скоупы, паттерн добавления write).
- 2026-06-11: «Вечное уведомление про незакоммиченный мозг» — апгрейд brain-dirty-watchdog из
  алертера в автономного уборщика (standing approval владельца, зафиксирован в CLAUDE.md правило 1):
  грязное дерево, стабильное ≥25 мин (два прогона) + validate.py пройден → автокоммит со списком
  файлов, pull --rebase, push, короткий отчёт в Telegram; валидатор не прошёл (секрет/фронтматтер)
  или конфликт → алерт (как раньше, с троттлингом 6ч); чистое дерево → тихий двусторонний синк
  (ff-pull + push отставших коммитов). Исходник: scripts/brain_dirty_watchdog.py (бэкап старого:
  .bak-2026-06-11 на сервере). Протестированы все три пути. Сегодняшний алерт был ложно-серединным:
  поймал рабочее состояние в процессе задачи про почту, всё было закоммичено через 20 минут.
- 2026-06-11: Rich Messages в Telegram (Bot API 10.1, вышел в этот же день): Hermes теперь отвечает
  полноценным Markdown — нативные таблицы, заголовки, цитаты, сворачиваемые блоки, формулы, до 32k
  символов одним сообщением. Патч rich_messages_patch.py (sendRichMessage в send() + rich-edit в
  finalize до оверфлоу-сплита; raw Bot API на stdlib, fallback на старый MarkdownV2 при любой
  ошибке, kill-switch HERMES_TELEGRAM_RICH_DISABLE=1), правило форматирования в system_prompt.
  Бэкапы: patches/telegram.py.bak-2026-06-11, config.yaml.bak-rich-2026-06-11. Тест: таблица
  доставлена (msg 5112). Док: engineering/hermes-gateway-ux.md.
- 2026-06-12: Новый скилл iso-drawing — прямоугольная изометрия по ГОСТ 2.317 (запрос владельца
  после провального чертежа 11.06). Библиотека skills/iso-drawing/scripts/iso_gost.py: проекция с
  приведёнными коэффициентами, эллипсы из параметрических окружностей, перекрытие тел painter's
  algorithm (белая заливка снизу вверх), вертикальные цилиндры с силуэтом, открытые пазы, устья
  боковых отверстий истинной кривой, А4-рамка + основная надпись (ГОСТ 2.301/2.104), линии ГОСТ
  2.303, размеры/выноски ГОСТ 2.307. Эталон detail22_demo.py (деталь №22: Ø92/Ø50/Ø36, 4×Ø12,
  пазы 10, 2×Ø10) — итеративно выверен визуально, PDF доставлен владельцу (msg 5120, ok:true).
  SKILL.md с методикой, чек-листом качества и анти-ошибками; нативный скилл в хабе
  (diagramming/iso-drawing); маршрут в INDEX. Рендер только в venv с MemoryMax=350M (preflight).
- 2026-06-12: iso-drawing v2 — переработка после некачественного результата (владелец: «снова
  плохо»). Подтвердил ГОСТ 2.317 веб-поиском (эллипс 1,22d/0,71d) и проверил проекцию аналитически.
  Главные правки: паз-вилка теперь вдоль оси Y (две проушины видны раздельно, не сливаются в
  коробку) — новый метод clevis_y; боковое отверстие истинной кривой на цилиндре (hole_on_cyl);
  скрытый контур не рисуется; размеры через vdim с привязкой в поле листа (раньше уезжали за
  рамку); выноски разведены без пересечений. Личный контроль качества: рендер→скачивание PNG→
  визуальная проверка→правка, 3 итерации до чистого результата. PDF доставлен (msg 5122). SKILL.md
  переписан: методика, чек-лист «смотри PNG глазами», список частых ошибок.
- 2026-06-12: Rich Messages отключены (HERMES_TELEGRAM_RICH_DISABLE=1 в hermes-gateway.env): на
  Telegram Web ответы бота показывались как «This message is currently not supported on Telegram
  Web» — веб-клиент ещё не умеет тип rich_message (Bot API 10.1 от 11.06). Владелец читает с веба,
  поэтому откат на MarkdownV2 (работает везде; таблицы → буллет-группы). Патч и код-хуки на месте,
  выключатель работает на лету — вернуть rich = убрать строку из env + рестарт, когда Web научится.
  Шлюз перезапущен, флаг подтверждён в живом процессе. Док: engineering/hermes-gateway-ux.md.
- 2026-06-12: Added hh.ru AI/business automation job-search watcher context and approval-only application rules in personal/side-jobs.md.
- 2026-06-12: Новый скилл hh-auto-apply — автономные отклики на hh.ru (запрос владельца). Профиль:
  ТОЛЬКО внедрение ИИ/автоматизаций в бизнес (не ML/DS). Цикл: поиск по кластерам запросов через
  залогиненный Chrome (/opt/hh-browser, CDP 9225; API соискателя hh отключён 15.12.25 + 403 с
  серверного IP, поэтому DOM-скрейп) → префильтр по названию → LLM (Groq 70b) решает релевантность
  и пишет короткое человечное письмо (анти-ИИ-промпт) → отклик кликом → журнал hh_applies.json
  (applied/manual/skipped, без повторов) → отчёт в Telegram. Вакансии с опросом/тестом → в manual
  (владельцу руками). Стоп при 3 фейлах подряд/4 ошибках LLM, человеческие паузы, login-gate.
  Грабли: Groq отдаёт 403 на дефолтный urllib-UA — добавлен Mozilla-UA. Конфиг/журнал в
  /root/.hermes/state/ (не в git). SKILL.md + INDEX-маршрут. Проверено: поиск (243→173), LLM-фильтр
  (целевую пропускает с письмом, ML отсекает).
- 2026-06-12: Documented VK bridge per-event latency diagnostics after adding processing-duration logs to vk_bridge.py.

- 2026-06-12: hh-auto-apply v2 — ежечасный cron (cfbbc44317be): вся Россия (area=113) + ЗП от 100к
  (фильтр hh + питон-префильтр вилки + LLM-правило), фокус на внедрение ИИ/агентов; LLM → Groq
  openai/gpt-oss-120b (отдельный от гейтвея бакет лимитов, 429-backoff + пейсинг), дедуп клонов
  вакансий по городам; «просили сопроводительное» → отклик + копия письма владельцу; мониторинг ЛС
  hh.ru/chat (новые входящие → TG, отказы — молча, hh_msgs_seen.json). Ночь (вне 8–23 МСК) — только ЛС.

- 2026-06-12 (вечер): hh-auto-apply v2.1 — режим обучения по фидбеку владельца (ложные срабатывания:
  КСД Групп без ИИ/опыт 5+, HiPo PropTech — менеджмент). mode=review: кандидаты в TG c id, отклик
  только после «норм» (--apply-ids); «не норм» → hh_feedback.json (bad/good) подмешивается в промпт
  сильнее правил. Новые жёсткие правила: ИИ обязателен в сути роли, опыт 5+ лет — отказ, отраслевой
  менеджмент с ИИ-обёрткой — отказ. Ночь блокирует только автоотклики, review/ЛС — круглосуточно.

- 2026-06-12 — Обновлён навык hh-auto-apply: текущий режим — только дайджест новых вакансий hh.ru; владелец откликается сам, старые автоотклики и дублирующий вотчер поставлены на паузу.

- 2026-06-13: albery docs — разбил монолиты `hermes.md` (72KB/862 стр.) и `server-context.md`
  (52KB/1142 стр.) на лёгкие хабы + 6 тематических файлов: hermes-{setup,automations,operations}.md
  и server-{infra,mcp-tools,integrations-sync}.md. Хабы остались (4.7KB и 12KB) с картой ссылок —
  входящие ссылки из overview/owner-reports/скиллов живы; overview.md обновлён. Контент перенесён
  дословно (сверка построчно), validate.py зелёный, registry без изменений (индексирует проекты).
  Цель: роутер грузит нужную секцию 4–30KB вместо всего дослье. Оптимизация мозга, пункт 1 из
  плана (вектор-слой отклонён как преждевременный на корпусе ~60k слов).

- 2026-06-13: watchdog self-heal — `brain_dirty_watchdog.py` теперь перед автокоммитом
  регенерирует производные индексы (`build_registry.py` + `build_section_index.py`), чтобы
  `registry.yaml` / `section-index.md` не расходились с правками доков, которые автономный
  вотчдог коммитит сам. Генератор упал → alert (доки не коммитятся, индекс не разъезжается);
  dry-run использует `--check` (read-only). Задеплоено на 217 через git (`cp` из клона в
  `/root/.hermes/scripts/`, бэкап `.bak-selfheal`); протестированы оба пути (happy → would-commit,
  невалидный док → alert) в `WATCHDOG_DRY_RUN=1`. Завершает оптимизацию мозга (режим самолечения).

- 2026-06-13: albery docs — устранено противоречие хостов 186↔217 (давний open-task). Источник
  правды — `servers.md`: **186.246.7.32 = выделенный Albery + его Hermes/Codex**, `217 = отдельный
  общий Hermes Brain + andigital + Vault`. Поправлено: `server-context.md` («Active server / current
  prod / use 217» → 186; самый опасный — это «первый файл для чтения»), `hermes-operations.md`
  (`ssh root@217 update.sh` → 186 — команда вела на не тот сервер; config-снапшоты → 186),
  `hermes.md`/`vpn-gateway.md` (band-aid-блокноты переписаны на чистую правду), `overview.md`
  (DNS `m4s.ru → A` 217 → 186), `hermes-setup.md` (Codex-заметка и менеджер аккаунтов помечены как
  «общий бокс 217, не Albery»). Легитимные 217 (Vault/brain-store/`--target new`/hh.ru-IP) оставлены
  и явно помечены. Не find/replace — каждое упоминание классифицировано против servers.md. Это пункт
  #1 из аудита качества ответов (устаревший факт = неверное действие агента).

- 2026-06-13: Albery Hermes (186) — починена молчаливая пропажа PDF-вложений (срочный прод-фикс,
  та же болячка, что на 217 06-06/06-11). Причина: `gateway.media_delivery_allow_dirs: []` —
  PDF недельного отчёта пишется в `/root/.hermes/media_cache/…pdf`, который НЕ входит во встроенные
  `MEDIA_DELIVERY_SAFE_ROOTS` и попадает под hardcoded-денилист `/root` → `validate_media_delivery_path`
  возвращал None, вложение дропалось молча (журнал «Skipping unsafe MEDIA directive path»). Фикс:
  `media_delivery_allow_dirs: [/root/.hermes/media_cache, /root/.hermes/outbox, /tmp]` + рестарт
  только `hermes-gateway` (бэкап `config.yaml.bak.mediafix.1781345602`; preflight rule #7 ОК — 1GB
  свободно, swap 2GB, рестарт безопасен). Подтверждено: `run.py` транслирует config →
  `HERMES_MEDIA_ALLOW_DIRS` env при старте, и `validate_media_delivery_path(<тот PDF>)` теперь
  возвращает путь. Rescue-патч тут НЕ помог бы (исключает весь `~/.hermes`). Доступ к 186 — джамп
  через Vault на 217 (servers.md). Док: engineering/hermes-gateway-ux.md.

- 2026-06-13: Albery owner-weekly — переработан промпт отчёта (v4) + восстановлен Groq-aux на 186.
  (1) Глубина: кроновый промпт делал тонкую 7-секционную «записку», а не глубокий v3 (10 секций с
  пофамильной приёмкой). Переписал под v3-структуру. (2) По правкам владельца: пятница — выходной,
  контрольная встреча итогов — четверг (не помечать «пт нет созвона» как нарушение; период пн–чт);
  раздел 6 «Оценка руководителей» теперь ТАБЛИЦЕЙ по каждому (задача|факт|вердикт|артефакт);
  аномалия Битрикса — если новых задач нет, подсвечивать вероятную истёкшую подписку Bitrix
  Marketplace и НЕ выдавать устаревшие цифры как актуальные (+правило «всегда актуальные данные»).
  Деплой на 186: jobs.json owner-weekly + .txt (бэкапы .bak.v4). (3) Groq-aux на 186 падал
  `payment/credit` (протухший ключ) → заменил рабочим из 217 (current project), daemon-reload+рестарт,
  ошибки прекратились (0/45с). Отчёт по новым правилам генерит сам Albery-Hermes (cron run), доставка
  владельцу в TG. Контракт-док: projects/albery/owner-reports.md (правила 5–6).

- 2026-06-13: Albery Hermes (186) — внятные сообщения об ошибках провайдера. Симптом: при лимите
  codex (429 usage_limit) гейтвей писал «⚠️ Provider authentication failed. Check the configured
  credentials» — врущее (это не креды, а исчерпанная квота). Причина: `_gateway_provider_error_reply`
  в gateway/run.py проверял AUTH-регексп раньше rate-limit, а текст codex-транспорта содержит
  «authentication failed». Фикс: идемпотентный патч `scripts/hermes_provider_error_patch.py` —
  сначала ветка usage-limit (с парсингом resets_in_seconds → «сброс через Xч Yм»), потом rate-limit,
  потом auth/нет-аккаунта; чёткие русские сообщения (лимит / нет аккаунта / временный rate-limit).
  Деплой на 186: /root/.hermes/patches/provider_error_patch.py + ExecStartPre-дропин
  20-provider-errors.conf (переживает hermes update), бэкап run.py.bak.providererr. Проверено на
  сервере на всех трёх типах ошибок. Текущий блокер отчёта был именно лимит codex (не auth).

- 2026-06-13: Albery owner-weekly — найден корень «отчёт-говно» + чинён авторитетный контракт.
  Симптом: свежий недельный отчёт вышел в чужой 11-секционной Bitrix-центричной структуре («Красная
  зона», «Подчинённые без задач в Bitrix24», «Отделы», «Адресные вопросы») вместо нашей v3-структуры,
  и взял устаревшие «78 открыто/46 просрочено» как факт. Разбор: AI-инструкция в БД Albery
  `ai_instruction_folders / Еженедельный отчет по компании` (которую агент читает через
  start_here) ОКАЗАЛАСЬ правильной (v3: 10 секций, раздел 6 — пофамильная приёмка). Но «говно»-прогон
  её НЕ исполнил — сгенерён в окно дохлого Groq-aux (сжатие выкинуло инструкцию из контекста → агент
  сымпровизировал по сырым Bitrix-задачам). Плюс в инструкции не было 3 правок владельца. Фикс:
  обновил инструкцию в БД (13862→15072) — (1) рабочая неделя пн–чт, пятница выходной, контроль в
  четверг (не считать «нет созвона в пт» нарушением); (2) раздел 6 — ТАБЛИЦЫ по каждому руководителю
  (задача|факт|вердикт ✅/⚠️/🚫/❌|артефакт); (3) аномалия Bitrix Marketplace — при отсутствии новых
  задач подсвечивать вероятную истёкшую подписку, не выдавать старые цифры за актуальные. Бэкап старой
  инструкции: /root/.hermes/secure/weekly_instr.bak.*.md. Контракт-док owner-reports.md уже отражает
  правила. Перегенерация — на здоровых бэкендах, агентом.

- 2026-06-13: Albery owner-weekly — НАСТОЯЩИЙ корень «отчёт-говно» (после трёх неверных заходов).
  Оказалось: недельный отчёт имеет ДВА разных источника промпта, и я правил не тот. UI-генерация
  (`request_type=owner_weekly_report`) берёт АКТИВНЫЙ промпт из таблицы `ai_prompts` (категория
  owner_weekly_report, строка b941c658) — НЕ агентскую инструкцию `ai_instruction_folders`, которую
  я менял раньше. Старый b941c658 задавал 11-секционную Bitrix-структуру (красная зона/подчинённые
  без задач/отделы/системные изменения), период пн–вс, и тянул устаревшие «78 открыто» — отсюда
  «говно». App берёт `report_text` прямо из ответа LLM (функция `_build_owner_weekly_report_text` —
  только fallback на пустой). Фикс: переписал b941c658 под v3 (10 секций, раздел 6 — таблицы по
  руководителям, период пн–чт/пятница-выходной, аномалия Bitrix Marketplace, владелец-не-ответственный).
  Подтверждено в БД (маркеры). Тест-генерацию заблокировал sequential-guard (нужен отчёт за пред.
  неделю). owner-reports.md обновлён разделом «ДВА источника правды — не путать». Бэкап старого
  промпта: /root/.hermes/secure/owner_weekly_prompt.bak.*. (Колонки updated_at в ai_prompts нет.)

- 2026-06-14: Albery Hermes (186) — ОТКЛЮЧЕНО сжатие контекста (`compression.enabled: false`),
  по решению владельца. Корень нестабильности недельного отчёта: aux-сжатие шло через Groq free
  (llama-3.3-70b, ~12k токенов/мин), а контекст генерации отчёта — десятки тысяч токенов; пачка не
  влезала → Groq `payment/credit` → сжатие ломалось и ВЫКИДЫВАЛО детали инструкции (формат таблиц)
  из памяти модели → отчёт выходил без таблиц (то густо, то пусто, в зависимости от живости Groq).
  Без сжатия полная инструкция (~15KB с требованием таблиц) всегда остаётся в контексте → отчёт
  стабильно по v3 с таблицами. Безопасно: окно модели большое, плюс страховки `hygiene_hard_message_limit:
  50` и session_reset (idle 30м/04:00) не дают переполнения. Прочие мелкие aux (title/skills/web_extract)
  остались на Groq — они на маленьких пачках не падают. Бэкап: config.yaml.bak.nocompress.*. Рестарт
  gateway применил правку и очистил очередь (отменил ручной прогон отчёта).

- 2026-06-14: Albery — записан playbook `projects/albery/operations-playbook.md` (структурирована вся
  сессия 13–14.06): роль Groq (STT + aux, почему сжатие отключено), как генерится недельный отчёт
  (ДВА источника промпта — агентская инструкция vs UI `ai_prompts/b941c658`), эталон v3-структуры с
  таблицами и оговорками, диагностика «тупит/фигня» по журналу, золотые правила («диагностируй прежде
  чем менять», «помни про два источника», «проверяй бэкенды»). Ссылка добавлена в overview.md, section-index пересобран.

- 2026-06-15: Albery — поднят ИИ-бот в Bitrix24 на Мозге Гермеса (тест-портал b24-0xrp3s).
  Записан `projects/albery/bitrix-bot.md`. Ключевое: Bitrix не регистрирует бота из вебхука
  (нужно ЛОКАЛЬНОЕ ПРИЛОЖЕНИЕ); обработчик `POST /bitrix/imbot/app` в Albery `app.py`
  (регистрация на ONAPPINSTALL, ответы per-event access_token, состояние в .b24_testbot_state.json,
  bot_id=24); мозг = `hermes -z --continue bitrix-<dialog> -t albery-faq --yolo` (read-only,
  toolset жёстко ограничен — иначе команды на проде от root); подключён faq-MCP (`albery-faq`) к
  Гермесу. Реакции: typing + 👍 (произвольных эмодзи на портале нет). Коммиты Albery:
  819c2a7/3e43ded/f44e351/daa48b6 + реконсиляция прод-онли правок 8db738d. Open: лог взаимодействий,
  жизненный цикл сессий (автосжатие у Albery-Гермеса отключено), tiered full-доступ владельцам, дайджест.

- 2026-06-15 (продолжение): Albery Bitrix-бот — доведены реакции/доступ/сессии/аналитика.
  Реакции через IM v2 (`im.v2.Chat.Message.Reaction.add/delete`): 👀 на приём → 👍 на выполнение.
  Tiered-доступ: Евгений(14)/Александр(16) → полный MCP, остальные → faq (`B24_TESTBOT_FULL_USER_IDS`).
  Жизненный цикл сессий (`bitrix_bot_sessions`, миграция 028): epoch на диалог, idle>8ч → новая эпоха,
  лимит реплик (16) → ротация с переносом краткой сводки (summary-buffer; автосжатие Гермеса отключено).
  Лог `bitrix_bot_interactions` (027). Еженедельный дайджест `scripts/bitrix_bot_weekly_digest.py` →
  TG Александру (cron Пн 10:00 МСК, доставка проверена). Коммиты Albery: 0d4a6a5/da62889/03abf7e.

- 2026-06-16: Albery — RAG-чанкинг поиска по знаниям + управление TG-доступом из чата.
  **RAG (ступень A):** `search_company_knowledge` отдаёт топ-6 чанков-пассажей (~400 токенов, макс 2
  на документ), а не целые документы (было до 50×~24КБ → жгло лимит Codex). Миграция 029
  (`company_knowledge_chunks` + state/meta), чанкер `shared/knowledge_chunks.py` с self-refresh по
  сигнатуре корпуса (Drive-синк/правки подхватываются авто), `scripts/rebuild_knowledge_chunks.py`.
  Замер на проде: 42 дока → 971 чанк, экономия текста 98.8–99.2% (×86–130). pgvector не ставили.
  Ступень B (эмбеддинги/семантика) отложена — нужен API-ключ (Codex/подписка эмбеддинги не умеет).
  Док: `projects/albery/knowledge-rag.md`. Коммит Albery `e2b82ac`.
  **TG-доступ:** env `TELEGRAM_ALLOWED_USERS` = ровно Александр(1451982360)+Евгений(6514126096),
  остальным отказ. Управление из чата — skill `tg-access` + `scripts/tg_access.py` (env+config,
  бэкап, ОТЛОЖЕННЫЙ рестарт gateway, т.к. агент крутится внутри него). Не патч ядра (его стирает
  `hermes update`). Док: раздел в `projects/albery/hermes-operations.md`. Коммиты Albery da87823/e2b82ac.

- 2026-06-16: «Простые поставки» — уточнён workflow ожидаемых приходов: перед записью товара обязательно сверять позицию с активными складскими товарами и учитывать латиница/кириллица в кодах (`SM04`/`SM02` → `СМ04`/`СМ02`), чтобы не создавать дубли под английским написанием.

- 2026-06-16 (продолжение): Albery — гигиена RAG-индекса + аудит патчей gateway.
  RAG-индекс: чанкер исключает 5 артефактов `__sync_tmp__*` (дубли реальных доков от прерванного
  Drive-синка) и денойзит листы (`<br>`, `∅`, пустые ячейки, авто-заголовки `Колонка N:`). 884 чанка/
  33 дока. + query expansion (OR-broadening + подсказка агенту синонимами): «график зум созвонов»
  0→6 чанков. Коммиты Albery после `e2b82ac`.
  **Аудит gateway-патчей (Вариант C):** апдейт ~13.06 стёр ручные патчи; авто-восстановление
  (`apply_patches.py`) исчезло. ЖИВЫ нативно/через config: context guard, session_reset, compression,
  reasoning_effort. НЕАКТУАЛЕН фикс `event` NameError (баг-патч тоже стёрт). СТЁРТЫ: `/accounts`/`/limits`,
  wall-clock guard, RU-UX сжатия, `apply_patches.py`. Hermes ~2090 коммитов позади — не обновлять
  бездумно. Доки `hermes-operations.md` приведены в соответствие (таблица аудита).

- 2026-06-16 (фикс): Albery — молчаливый дроп вложений на 186 (self-check поймал).
  Агент под root писал файлы в `/root/…`, а `/root` в денилисте доставки → «файл отправлен», но не
  доходил. Патч 217 не подошёл (другая версия `base.py`, анкоры не совпали). Фикс нативный, без патча
  кода: `mkdir /root/.hermes/outbox` + ENV `HERMES_MEDIA_ALLOW_DIRS=/root/.hermes/outbox` в
  `hermes-gateway.env` (код читает именно ENV, не config-ключ `media_delivery_allow_dirs`) + правило в
  `memories/USER.md` (файлы для отправки класть в outbox). Проверено в runtime-env + `validate_media_
  delivery_path`. Переживает `hermes update`. Док: `hermes-operations.md`.

- 2026-06-16 (железобетон): Albery — rescue-патч против дропа вложений на 186.
  Поверх outbox+правила доведено до bulletproof: `scripts/hermes_media_rescue_patch_186.py` →
  `/root/.hermes/patches/media_rescue_patch.py` + ExecStartPre `25-media-rescue.conf`. Заменяет
  финальный `return None` в `validate_media_delivery_path` на `_rescue_media_path_to_outbox`: любой
  свежий (≤30мин) некредентный файл из денилист-пути (`/root/…`) копируется в outbox и доставляется;
  `~/.ssh`/`/root/.hermes`/`/etc`/… остаются заблокированы. Анкоры 217 не подошли (другая версия
  base.py). Killer-тест: `/root/x.pdf`→спасён, `~/.ssh/key`→None. Живучесть к `hermes update` доказана
  (restore base.py → рестарт → ExecStartPre переприменил, marker 0→2). Док: `hermes-operations.md`.

- 2026-06-16: Albery Bitrix-бот — кнопка/команда «🆕 Новая сессия» (сброс контекста).
  Память бота инжектится из `bitrix_bot_interactions` по dialog_id (не по эпохе), поэтому сброс =
  смена эпохи + НОВЫЙ `history_floor_id` (миграция 030): `_b24_recent_history` берёт только id>floor →
  контекст реально чистый. Сброс без вызова модели. Триггеры: keyboard-кнопка под ответами,
  бот-команда `/new` (ленивый `imbot.command.register`, `ONIMCOMMANDADD`), ключевые слова
  (`B24_RESET_TRIGGERS`, матч по всему сообщению). Набор `/new`/«новая сессия» проверен на проде
  (history после сброса=[]); кнопка/команда best-effort. Коммит Albery: см. app.py + 030.
