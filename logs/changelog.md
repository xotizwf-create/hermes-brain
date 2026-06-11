---
id: changelog
type: log
tags: [changelog]
updated: 2026-06-10
secret_refs: []
---

# Changelog

Append-only, newest on top. Every approved change to the brain gets one line.

## 2026-06-11
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

## 2026-05-31
- Added bounded release retention to deployment guidance: keep the active release, the immediately
  previous rollback release, and only a small history (usually last 3–5 timestamped releases); after
  successful verification, prune older release dirs so servers do not accumulate unlimited copies.
- **Voice messages now work in Telegram (STT via Groq).** Root cause of the "endless thinking" on a
  voice note: `stt.provider` was `local` (faster-whisper) but the package wasn't installed, so
  `_transcribe_local` tried a runtime `pip install faster-whisper` + model download + CPU inference
  on a 957 MB / ~330 MB-free box → hang/OOM risk (hard-rule #7). Fixed by switching to cloud STT:
  set `stt.provider=groq` + `stt.groq.model=whisper-large-v3-turbo` in `/root/.hermes/config.yaml`,
  added `GROQ_API_KEY` to `/root/.hermes/.env` (600), restarted gateway. Documented in
  `projects/albery/hermes.md` (incl. the Cloudflare-1010-on-urllib gotcha — validate the key via the
  openai SDK path, not curl/urllib). Backups: `config.yaml.bak.*`, `.env.bak.*`.
- Added **universal scale-adaptive server preflight** `engineering/server-preflight.md` (assess →
  plan a memory budget from current headroom → protect live services → execute within the budget),
  same protocol for a 512 MB VPS or a big dedicated box. Made it the mandatory first step for any
  server work: rewrote `INDEX.md` core principle #6 + added a routing line (so it's in Hermes'
  runtime system_prompt, which loads INDEX.md), and pointed `deployment.md` + `CLAUDE.md` rule #7 at
  it. Key mechanics: reserve = max(20% RAM, 512 MB); on-box heavy work only if peak fits the budget
  and only inside `systemd-run -p MemoryMax=… + nice/ionice` (runaway dies, app survives); else
  off-box; `OOMScoreAdjust=-900` on critical services; never run build/test/migration on the live DB.
- Added hard rule #7 (`CLAUDE.md`) + "Production resource safety (never OOM the box)" section
  (`engineering/deployment.md`): treat every prod host as fragile/memory-constrained, preflight
  `free -m`/`swapon` before heavy steps, build `dist/` + run tests/typecheck OFF the box, ship a
  prebuilt tested release (`npm ci` + light smoke + atomic switch with rollback), and NEVER point a
  trial/dev/test instance or migration at the live production DB. Standing rule behind the 2026-05-31
  LiteExams incident (server-side `vite build` OOM-killed on a 1 GB box → dropped DB connections →
  wave of "bound to another device" lockouts). Diagnosed gov-exams-app/LiteExams: token/device code
  is byte-identical to old prod (deploy did NOT change auth logic); the lockouts are deploy-window
  instability on 95 strict `server_cookie` tokens, subsiding once the box stabilised.
- Installed Codex CLI on prod `217.198.12.236` (`codex-cli 0.135.0` → `/usr/bin/codex`), copied
  `auth.json` from the PC to `/root/.codex/auth.json` (600), pinned `/root/.codex/config.toml`
  → `model_reasoning_effort = "high"`. Verified: `codex login status` = Logged in using ChatGPT,
  outbound IP 95.85.243.43 (VPN-Estonia, no 403), `codex exec` ran at `model gpt-5.5` / `high`.
  Corrected the stale "Codex installed on prod" docs (it was the old host 186.246.7.32, not 217).
  Delegation (`skills/codex-delegation`) now works on 217.
- Documented self-serve prod access from the `hermes-brain` repo: gitignored `.env` (root SSH for
  `217.198.12.236`) + paramiko path, so the agent reaches prod directly without the "Сайт мой"
  deploy helper (`engineering/secrets-access.md`).
- Pinned delegated coding to high reasoning: `codex exec` now always runs with
  `-c model_reasoning_effort="high"` (`skills/codex-delegation`, `engineering/agentic-coding.md`).
  Corrected the prior claim that Codex CLI defaults to high (it's `medium`) — high is now explicit.
  Hermes' own `reasoning_effort` stays `medium`; only the Codex subprocess goes high. Noted the
  5h-limit cost trade-off and the optional server-wide `/root/.codex/config.toml` default.
- Added skill `hermes-self-repair` (diagnose-first runbook to fix the gateway runtime safely:
  verify before touching, idempotent self-patchers, code-task classifier 3600s, config de-dup, one
  observed restart with rollback) + routed in `INDEX.md`; logged the 2026-05-31 one-line-edit
  incident in `projects/albery/incidents.md`. Lets the agent self-repair without blind prod restarts.
- Added `engineering/agentic-coding.md` + skills `codex-delegation` and `small-prod-edit`; routed in
  `INDEX.md` — why: a trivial one-line prod edit (2026-05-31) was slow, repetitive and rattled prod.
  Root cause is the harness, not the model (Hermes IS gpt-5.5/Codex): throttled reasoning, mid-task
  context compression, mis-classified time budget, live-SSH over-diagnosis. Fix = delegate real
  coding to the Codex CLI (`codex exec`, high reasoning, separate uncompressed context, real patch
  loop), git-first deploys, a strict tiny-edit workflow, and server-config notes (don't compress
  mid code-task; classify file/SSH/config edits as code → 3600s budget).
- Published `aislop-code-quality` into the native Hermes skill registry as
  `/root/.hermes/skills/software-development/aislop-code-quality` in addition to the git-tracked
  `agent-knowledge/skills/aislop-code-quality`. This makes it visible in `hermes skills list`; the
  related code-quality builtin skills (`test-driven-development`, `systematic-debugging`,
  `requesting-code-review`, `writing-plans`, `plan`, `spike`, `subagent-driven-development`,
  `github-code-review`, `github-pr-workflow`, `codebase-inspection`, `python-debugpy`,
  `node-inspect-debugger`, `codex`, `claude-code`, `opencode`) were already installed and enabled in
  `/root/.hermes/skills`.

## 2026-05-30
- Added `aislop-code-quality`: Hermes can now run scanaislop/aislop (`aislop@0.10.1`) after code edits
  or before PRs to detect AI-code slop and apply only safe mechanical cleanup. Added
  `aislop_guard.py`, INDEX/CLAUDE routing, local CLI install, and validation notes.
- Added `markitdown-docs`: local PDF/Word/Excel/PowerPoint files now route through Microsoft
  MarkItDown into compact Markdown first (`convert_document.py` writes `.markitdown.md` + short
  preview), reducing token spend and improving document context before analysis. INDEX + CLAUDE routing
  updated.
- **Hermes Vault — web UI for per-project secrets** (`skills/secure-access/vault/`). Dependency-free
  stdlib app (`secrets_ui.py`): lists the owner's GitHub repos (REST), stores/edits a `.env` per project,
  tied to repos. Live at `https://www.andigital.ru/andigital/secret/<token>/` over the existing
  Let's Encrypt TLS. Security: two factors (unguessable URL token in the path → 404 if wrong + scrypt
  password), HMAC `httponly`/`Secure`/`SameSite` session, CSRF on forms, per-IP login lockout, token kept
  out of nginx logs. **Runs unprivileged** (`hermesvault`, systemd-hardened, bound 127.0.0.1, nginx-proxied).
  Secret store **relocated & unified** at `/opt/hermes/secure/projects` (`2770 hermesvault:hermessec`,
  setgid) — shared by the root agent + the web UI; `save_project_secrets.py`/`secret_push.py` repointed
  (660/2770). Deployed + tested end-to-end (wrong token→404, correct→setup page over public HTTPS).
  URL token never went through chat/LLM (written server-side, SFTP-delivered to the owner's PC). Turnkey
  for resale: all branding in `config.json`/nginx `base_path`, install steps in the vault README. systemd
  unit + nginx snippet versioned in the brain. Validator allowlists the code-only `vault/` dir.
- Secure secret **intake without chat/LLM exposure**. Owner's point: a secret pasted into Telegram has
  already left the server (Telegram + the LLM provider see it). Added `secret_push.py` (workstation tool):
  SFTPs a local `.env`/file straight into `/root/.hermes/secure/projects/<slug>/` over SSH via the server
  helper, confirms with variable NAMES only — the value never touches Telegram or any model. Made this the
  **primary** path in `store-project-secrets`; demoted chat-paste to a discouraged fallback ("treat as
  exposed, rotate"). Tested end-to-end (upload → 600/700 perms, staging shredded, names-only). Storage of
  record stays the server secure zone (root-only). Updated `engineering/secrets-access.md`.
- New capability **store-project-secrets**: owner pastes a project's `.env` (or prod-server password)
  → Hermes finds the repo via `gh`, locks the values into the secure zone
  `/root/.hermes/secure/projects/<slug>/` (`.env`/`server_password`/`server_key` 600, dir 700, root-only,
  never echoed/committed), confirms with variable **NAMES only**, and remembers the project secret-free
  in `projects/<slug>/` (repo, prod host/user, var names, refs `proj/<slug>/env`, `proj/<slug>/ssh/root`).
  Helper `skills/secure-access/scripts/save_project_secrets.py` (stdin/`--from`, shreds the temp paste,
  value-free Russian output) — tested end-to-end on prod (save-env/save-server/show, perms 600/700, no
  leaks). Documents the deliberate "pasted-secret" exception in `engineering/secrets-access.md`. INDEX +
  CLAUDE updated. ⚠ The paste still lives in Telegram → Hermes reminds the owner to delete it.
- Google OAuth app **published to Production** (owner did it) → re-ran the PC consent once and
  re-minted the token, so the refresh token is now **long-lived** (no more ~7-day Testing expiry).
  Delivered to the secure store + compat path (600, old backed up); read re-verified. The durability
  caveat on the Calendar entry below is now resolved.
- Google **Calendar upgraded to read/write** (owner asked Hermes to see AND edit). Changed the Calendar
  scope in `read-links/scripts/google_oauth_login.py` (`calendar.readonly` → `calendar`), re-ran the
  PC browser consent with the owner's existing Desktop OAuth client, minted a new token (refresh +
  4 scopes: drive/sheets/gmail readonly + **calendar read/write**), delivered it over SFTP to
  `/root/.hermes/secure/google_oauth_token.json` AND the bundled-tool compat path
  `/root/.hermes/google_token.json` (both 600; old token backed up). Verified end-to-end with the
  bundled `google_api.py calendar`: list (read) ✓, create ✓, delete ✓ (test event added then removed,
  calendar left clean). Hermes now creates/edits/deletes events via `google_api.py calendar
  create|delete` (ISO+TZ; edit = delete+create); keep writes behind owner confirmation. Updated
  `skills/google-account`. ⚠ Still pending for durability: **publish the OAuth app to Production**
  (Testing-mode refresh tokens for sensitive scopes expire ~7 days) — else weekly re-login.
- GitHub account access for Hermes (prod). Before: server had only the single-repo `hermes-brain`
  deploy key + no `gh` → couldn't see/clone the owner's other repos. Now: installed `gh` CLI on prod
  (`/usr/bin/gh` 2.93.0) and authed it as **`xotizwf-create`** by **reusing this PC's gh OAuth token**
  (owner's choice: speed over a dedicated token; scope `repo, read:org, gist` = read/write to ALL the
  owner's repos). Token pushed to `/root/.hermes/secure/github_token` (600) over SFTP (never printed) +
  `/root/.config/gh/hosts.yml`; `gh auth setup-git` wired git's credential helper; git identity set.
  Verified: `gh repo list` (10 repos), `gh repo view <private>`, `GIT_TERMINAL_PROMPT=0 git ls-remote
  <private>` all OK. Brain holds no token — ref `agent/github/token`. Docs: `engineering/secrets-access.md`
  ("Server GitHub access" + broad-token/PC-coupling caveat), `skills/new-repo` prerequisites, server
  `access-map.yaml` github entry. ⚠ Same token as the PC — PC re-login may rotate it and break the server.
- UX round 2 — kill technical noise, keep human narration. Owner saw raw tool bubbles
  (`📚 skill_view`, `💻 terminal: "git …"`) after round 1: those come from tool progress, which is
  exactly the technical text he rejects. Reverted **`display.platforms.telegram.tool_progress: off`**.
  Also turned **`long_running_notifications: false`** (the `⏳ Working — N min` heartbeat is hardcoded
  English + leaks the current tool name). The real "live progress" is the model's own Russian
  narration (`interim_assistant_messages`, already on) — strengthened the system_prompt: send a brief
  natural status ~every 30s («Проверяю токен…»), never show tool names/commands/paths/iteration.
  Corrected `engineering/hermes-gateway-ux.md` (round 1 wrongly recommended tool_progress=new) +
  `profile/communication.md`. Config backed up, gateway restarted from SSH, healthy.
- Hermes UX made visible & honest (config, not code — no run.py patch). Telegram **tool progress
  turned on** (`display.platforms.telegram.tool_progress: new`) so the owner sees live step bubbles;
  native Telegram "typing…" indicator already auto-resumes = the "Думаю…" cue. **system_prompt
  expanded** with hard rules: only Russian, narrate steps briefly, honest "не нашёл" instead of
  made-up answers, no English/technical system strings in chat, business tone. `show_reasoning` left
  OFF on purpose (English `💭 Reasoning` block + raw CoT fights Russian-only); no `ru` UI locale ships
  so `language` stays `en`. Noted `display.personality: kawaii` as a tone risk (left as-is). Config
  backed up server-side; gateway restarted from SSH (external) and verified healthy. New brain doc
  `engineering/hermes-gateway-ux.md` + INDEX route.
- MCP "обнови" fix: refresh/restart no longer kills the active chat turn. `hermes_mcp.py` gained
  `detached_restart()` (restart dispatched to a separate `systemd-run --on-active` transient unit so
  the reply flushes first); `cmd_refresh` + `apply_live` route through it. Was the root cause of the
  garbled "Gateway shutting down — task interrupted" replies on "обнови". Made "обнови" an explicit
  trigger in `connect-mcp` (→ `refresh --apply`); reinforced in `connectors/mcp-servers.md`. Profile:
  Russian-only in chat, honest "не нашёл" instead of made-up answers, never restart the gateway mid-turn.
- Google Workspace compatibility documented: when bundled Hermes Google tools expect `/root/.hermes/google_token.json`, reuse the existing secure OAuth token at `/root/.hermes/secure/google_oauth_token.json` via `install -m 600 ...`, verify with `setup.py --check`, and install missing Google API deps with `uv pip install --system ...` if normal `pip` is unavailable. Updated `google-account`, `connectors/google-workspace`, and `update-knowledge` with the owner preference to auto-document new non-trivial procedures.
- Google account CONNECTED (OAuth, owner's account, read-only). Added skill `google-account` (the
  full instruction: how it was set up, usage, keep-alive, rotation, adding write) +
  `google-account/scripts/gcal_read.py` (Calendar agenda). Cloud project `gen-lang-client-0802797266`;
  enabled Drive/Sheets/Calendar/Gmail APIs; OAuth Desktop client; PC browser login (token has
  refresh_token + 4 read scopes); token delivered to `/root/.hermes/secure/google_oauth_token.json`
  (600, gitignored, ref `agent/google/oauth-token`). Verified live on prod: Calendar API call
  succeeded (auto-refresh works). Scopes widened to drive/sheets/calendar/gmail readonly (also in
  `gauth_read.py` + `google_oauth_login.py`). Fixed login script's Windows-console print crash.
  ⚠ Pending: owner should **publish the OAuth app to Production** (else sensitive-scope refresh tokens
  expire ~7 days); re-auth after publishing. Transport gotcha noted: Git-Bash `/root` path mangling →
  `MSYS_NO_PATHCONV=1` / base64-over-SSH.
- read-links Google profile (owner chose **OAuth = own account, read-only**): `gauth_read.py` reads
  the owner's Google Docs/Sheets/Slides via an OAuth refresh token at
  `/root/.hermes/secure/google_oauth_token.json` (600, gitignored — ref `agent/google/oauth-token`,
  scopes `drive.readonly`+`spreadsheets.readonly`) — no per-doc sharing; Sheets → all tabs as CSV.
  Service account kept as an alternative. `fetch_url.py` prefers the token, falls back to public export
  when absent; no-access message branches OAuth vs SA. Added `scripts/google_oauth_login.py` (PC-side
  browser consent → refresh token; Google blocks the consent screen from the server IP, so login is
  done on the PC and the token copied over, like Codex). `connectors/google-workspace.md` documents the
  one-time Cloud OAuth-client + login + token delivery. Token files gitignored. Google libs already in
  the venv. Pending: owner creates the OAuth client in Cloud + we run the PC login + drop the token.
- Added skill `read-links` + `scripts/fetch_url.py` (stdlib): read the content behind a pasted link.
  Google Docs/Sheets/Slides/Drive → share-link converted to the export URL (Docs→txt, Sheets→csv,
  Slides→txt) and fetched in full (no browser, no LLM/Firecrawl summarization, no token cost); normal
  pages → HTML reduced to readable text (capped ~20k). Private Google docs are detected and reported
  in Russian (need link-sharing or Google auth — offered as a follow-up). Skill routes JS-heavy/login
  pages to the native `browser_*` tools and "найди в интернете" to `web_search` (both already enabled
  on prod). All owner-facing output Russian, no technical noise. INDEX + CLAUDE key-skills updated.
  Grounded in prod inspection: web/browser/vision toolsets enabled; server reaches the internet
  (example.org 200); Google export endpoints reachable.
- connect-mcp auto-reload: after add/enable/disable/remove the live Telegram session now picks up the
  tool changes **by itself** — the owner no longer needs to send `/reload-mcp`. Implemented as an
  idempotent gateway patch (`skills/connect-mcp/patches/mcp_autoreload_patch.py`): before each agent
  turn the gateway hashes the `mcp_servers` block and, if it changed since last seen, calls its own
  `_execute_mcp_reload(event)` (the `/reload-mcp` path, which also refreshes cached agents so the
  active session sees new tools next turn). Cheap on the no-change path (stat); fires once per change.
  Self-heals across `hermes update` via systemd `ExecStartPre` drop-in
  `skills/connect-mcp/systemd/20-mcp-autoreload.conf`. Manager message updated (no more «отправь
  /reload-mcp»). Grounded in the live gateway source (anchors verified unique; patch validated by
  py_compile; never breaks run.py).
- connect-mcp fixes after the first real connection (`prostye_postavki` = "Простые поставки",
  miramed32, 19 tools). (1) **Hard rule: never auto-name a connector** — after `probe`, STOP and ask
  the owner; `probe` now ends with «Как назовём этот сервер?» and the skill forbids deriving a name
  from the URL/domain. (2) **All owner-facing manager output is Russian, no technical noise** (no
  paths/commands/ids/stack traces); errors print human Russian. Added the same rule globally to
  `profile/communication.md`. (3) Manager now **slugifies a human name** ("Простые поставки" →
  `prostye_postavki`) and echoes the human name in messages; enable/disable/remove accept the human
  label. Recorded the live connector in `connectors/registry.yaml` (+ `label`) and added
  `connectors/prostye-postavki.md`.
- MCP connectors subsystem (grounded in the live Hermes source on prod). Added skill `connect-mcp` +
  manager `skills/connect-mcp/scripts/hermes_mcp.py`. Hermes' native `hermes mcp add` is interactive
  (TTY prompts), so the manager writes the **same canonical `mcp_servers` schema** (`{url, headers?,
  enabled}`, from the bundled `native-mcp` skill) non-interactively into `~/.hermes/config.yaml` — so
  the owner can paste a URL to the bot and Hermes connects itself. Switching = the **native `enabled`
  flag** (not a custom park key). Apply live via **`/reload-mcp`** in Telegram (reconnect, no restart,
  no lost session); `--restart` is the heavy fallback. Default dry-run; every write backs up config;
  `rollback` restores it. Secrets (URL path / bearer token) stay only in `config.yaml`/`~/.hermes/.env`
  (600), redacted everywhere else; registry gets a secret-free `url_template`. Added
  `connectors/registry.yaml` + `connectors/mcp-servers.md` (model). INDEX + CLAUDE updated.
  **Discovered prod had 0 MCP servers** (`mcp_servers: {}` on 217 — Albery hands were missing); re-wired
  Albery as the live test (URL built server-side from `/var/www/albery/.env`, `hermes mcp test` =
  tools discovered).
- Added `chatgpt-sub-watch` (daily 10:00 МСК, no-agent): warns before each ChatGPT account expires and
  **auto-removes** it the day after expiry (`hermes auth remove openai-codex <id>`), keeping the last
  account as a safety net. Dates registry `/root/.hermes/chatgpt_accounts.json` (acct #1 13.06, acct #2
  abc9@btwwin.sbs 30.05). Fixed the remove-call to pass the provider arg.
- Added `logs/session-2026-05-30.md` — session retrospective + "how Hermes is trained / how it scales
  itself" + a map of where everything lives. Refreshed `CLAUDE.md` state and `INDEX.md` so both the
  next Claude session and Hermes itself find it.
- Added a `reminders-and-watchers` note for ChatGPT/Codex account-pool checks: how to identify the
  active entry vs temporarily limited entries, explain email/no-email account switching to the owner,
  convert cooldowns to МСК, and avoid exposing emails/tokens.
- Activation (mail watcher): installed `himalaya` v1.2.0 on prod, configured the Gmail account
  (App Password in `/root/.hermes/secure/gmail_app_password`, 600, referenced via `auth.cmd` — not in
  repo/config). Created cron `mail-watch` (every 2h, `--skill himalaya`, deliver telegram). IMAP
  verified (folder list) and a live run returned `[SILENT]` (no important mail → no spam). Updated
  `reminders-and-watchers` skill with the deployed setup. Also corrected the stale telegram-toolset
  note in `hermes.md` (toolsets are enabled, not disabled).
- Activation: (1) verified reminders → Telegram live (test cron fired + `delivered to telegram:…`);
  (2) **two-way git**: server brain converted to a git clone via a repo-scoped read-write deploy key
  (`hermes_brain_deploy`), identity `hermes-server`; round-trip verified (server commit `651473c`
  pushed → pulled locally). Server is **UTC** → reminders use UTC−3 for Moscow times. Updated
  `update-knowledge` + `reminders-and-watchers` skills with the deployed reality.
- Phase B (teach Hermes): added skills `project-onboarding` (repo + prod/git/env access via secure
  store, then code per standards) and `reminders-and-watchers` (`hermes cron` one-shot/recurring +
  `himalaya` mail watcher → Telegram, grounded in the live `hermes cron create` interface). Reworked
  `update-knowledge` to a two-way git model (server brain = clone; Hermes self-edits → approve in
  Telegram → commit/push). Added INDEX routing + CLAUDE.md key-skills + decisions.md ADR. Grounded in
  server inspection: Hermes v0.15.0, builtin skills (himalaya/github-auth/codex), currently 0 MCP servers.
- Task 3 (single source of truth): in the "Сайт мой" repo, the legacy `agent.md` (186 KB) and old
  `agent-knowledge/` were untracked; archived both into `_legacy_agent_archive/` (chosen over delete)
  with a README pointing to hermes-brain. No tracked file referenced them; Hermes system_prompt
  already reads our `INDEX.md`. Updated CLAUDE.md state/tasks.
- Task 2 (sync): mirrored the brain to prod `217.198.12.236:/root/.hermes/agent-knowledge` via
  tar + `_deploy_helper.py` (per `update-knowledge`). Backed up the old structure to
  `agent-knowledge.bak.20260529_210928` first. New tree (profile/engineering/projects/…, 65 files)
  in place; `INDEX.md` preserved (the only path Hermes `config.yaml` system_prompt references).
  Confirmed prod outbound IP = `95.85.243.43` (VPN/Estonia active on 217).
- Task 1 (split): extracted two big subsystems out of `projects/albery/server-context.md` into
  focused docs — `vpn-gateway.md` (AmneziaWG outbound-via-Estonia) and `hermes.md` (Hermes agent:
  Codex provider, cron, Telegram, sessions, training, RBAC roadmap). `server-context.md` now holds
  the app/server reference + Bitrix MCP tools + fetch_url/bug notes. Updated its frontmatter/intro,
  `overview.md` "Full reference", added cross-links. IP `186.246.7.32` left in legacy commands with a
  banner (current prod `217.198.12.236`) — to reconcile live during brain sync (Task 2).

## 2026-05-29
- Fixed mojibake in `projects/albery/server-context.md`: 771 legacy lines were double-encoded
  (UTF-8 bytes read as CP1251 then re-encoded). Repaired in place via per-line round-trip
  (`cp1251.GetBytes` → `utf8.GetString`), kept already-clean lines, normalized CRLF→LF. 0 residual
  U+FFFD. Earlier "UTF-8 verified clean" claim was wrong (see mistakes.md).
- `scripts/validate.py`: also skip `CLAUDE.md` (landing/instruction file, no frontmatter needed).
- Created isolated `hermes-brain` repo. Built areas: profile, engineering (migrated + new
  coding-standards/code-review), projects (template, manifest schema, registry generator,
  validator), connectors (gmail/calendar/drive/bitrix/zoom), personal, skills, logs.
- Migrated albery as first reference project.
- Imported legacy `agent.md` (site repo) → `projects/albery/server-context.md` as the full
  operational reference (UTF-8 verified clean, scanned for secrets — none). Curated docs link to it.
- Hardened `scripts/validate.py`: skip README, expand secret-placeholder allowlist (getpass/env/...).
- 2026-05-31: Added project map entries for Простые поставки, Лёгкие экзамены/LiteExams, Hermes Brain; updated Albery description with dedicated Albery Hermes-agent note.
- 2026-05-31: Hardened reminder workflow: Moscow time by default, explicit timezone verification, active reminder list, and missed-reminder audit watchdog.
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
