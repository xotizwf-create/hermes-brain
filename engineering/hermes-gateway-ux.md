---
id: hermes-gateway-ux
type: engineering
tags: [hermes, gateway, telegram, ux, config, display, reasoning, progress, media, attachments]
updated: 2026-06-11
secret_refs: []
---

# Hermes gateway UX — indicator, live progress, tone

How the owner-facing behaviour ("Думаю…", live step updates, language, honesty) is controlled.
**It's config, not code** — these are built-in gateway features toggled in `~/.hermes/config.yaml`
(`gateway/run.py`), so never patch `run.py` for them. Config is server-only (600); the brain just
documents what's set.

## What was wrong (2026-05-30)
- "Странные/обрывистые сообщения" on "обнови" = the gateway restarting itself **mid-turn** (the MCP
  refresh ran `systemctl restart` in-process). Fixed in `skills/connect-mcp` — restart is now
  detached (`detached_restart()` via `systemd-run --on-active`). See `connectors/mcp-servers.md`.
- No visible "what is it doing": on Telegram **tool progress was off**
  (`display.platforms.telegram.tool_progress: false`).

## The knobs (in `config.yaml` → `display:` unless noted)
| Want | Knob | Set to |
|---|---|---|
| "Печатает…" indicator | native Telegram `send_chat_action("typing")` — always on, auto-resumes during a reply | (built-in, nothing to set) |
| Raw tool-call bubbles (`📚 skill_view`, `💻 terminal: "git …"`) | `platforms.telegram.tool_progress` | **`off`** — these dump tool names + commands/args = exactly the technical noise the owner rejects. Keep OFF. (`new`/`all` turn them on; `off` is bare-`off`→`False`→normalised to "off".) |
| Natural mid-turn updates in RU ("Проверяю токен…") | `interim_assistant_messages` | `true` (already) — **this is the real "live progress"**: the *model* narrates in plain Russian, driven by the system prompt. Content-aware, no tool internals. This carries the whole indicator story. |
| Busy ack when a msg arrives mid-work | `busy_ack_detail` / env `HERMES_GATEWAY_BUSY_ACK_ENABLED` | on (already) |
| Generic "⏳ Working — N min" heartbeat | `long_running_notifications` | **`false`** — OFF: the text is hardcoded **English** and appends the current **tool name** (`_status_detail`), so it leaks technical noise and breaks Russian-only. The model's `interim_assistant_messages` are the Russian substitute. (Interval would be `agent.gateway_notify_interval`, default 180s, but it's off now.) |
| Show raw model reasoning | `show_reasoning` | **`false`** — deliberately OFF: it prepends an English `💭 Reasoning:` block (raw chain-of-thought, EN + technical), which fights Russian-only. |
| UI language of gateway strings | `language` | `en` — **no `ru` locale ships**, so leave it; don't expect RU from this knob. RU comes from the system prompt, not here. |

**Design rule:** the "Думаю…/что делаю" signal is the native typing indicator + the **model's own
Russian narration** (`interim_assistant_messages` + system_prompt). Every gateway-generated
status string is English and often leaks tool names, so they stay OFF. Don't "turn on tool progress"
to make work visible — that brings back the `💻 terminal: "…"` noise. If a hard, guaranteed Russian
heartbeat every N seconds is ever needed (model goes silent inside one long tool call), it requires a
small `run.py` patch to translate `_heartbeat_text` + drop `_status_detail` — not a config toggle.

## Tone / behaviour
- The hard rules (only Russian; narrate steps briefly; honest "не нашёл" instead of made-up answers;
  no technical/English system strings in chat) live in **`config.yaml` `agent.system_prompt`** (read
  every turn) *and* in `profile/communication.md` (loaded via `INDEX.md`). The system_prompt is the
  reliable lever; the profile is the canonical long form.
- `display.personality` was `kawaii` (a cutesy persona). If the tone ever feels off / сюсюкающим,
  switch it to a neutral persona (e.g. `concise`) or empty. Left as-is 2026-05-30 — the system_prompt
  "деловой тон, без сюсюканья" line should dominate.

## File / attachment delivery (don't silently drop files)
The gateway sends a file/attachment **only if its path passes `validate_media_delivery_path()`**
(`gateway/platforms/base.py`). A rejected path is dropped **silently** with a log-only warning
`Skipping unsafe MEDIA directive path: …`: the model emits a MEDIA directive, the file never
arrives, and the agent gets no error signal — so it falsely reports «отправил» and may hang on
retries. Hit twice: 2026-06-06 (empty `media_delivery_allow_dirs`, project-audit `.zip`) and
2026-06-11 (PDF written to `/root/…pdf`).

How validation actually works (non-strict mode, our case — `gateway.strict: false`):
1. allowlist `gateway.media_delivery_allow_dirs` is always honored first;
2. otherwise any existing file is accepted UNLESS it is under a hardcoded denylist — and that
   denylist includes **the whole of `/root`** (root's home = credential territory), plus
   `/etc /proc /sys /dev /boot /var/*`, `~/.ssh`-style dirs and `~/.hermes/{.env,auth.json,credentials,config.yaml}`.
   So «файл лежит в /root — значит не уйдёт», даже свежий. `trust_recent_files` applies only in
   strict mode and does NOT override the denylist.

Defenses now in place (217, 2026-06-11):
- **Rescue patch** `/root/.hermes/patches/media_rescue_patch.py` (ExecStartPre in
  `hermes-gateway.service.d/10-reapply-patches.conf`, survives `hermes update`; source of truth:
  `scripts/hermes_media_rescue_patch.py` in this repo). When validation rejects a path purely for
  its location, but the file is real, ≤50 MB, **created within the last 30 min** (session-trust
  signal) and NOT under a credential/system location, it is **copied to `/root/.hermes/outbox` and
  delivered from there** (journal: `Rescued MEDIA path outside allowlist: …`). Credentials
  (`config.yaml`, `.env`, `~/.ssh`…) and stale files stay rejected — verified by unit test in venv.
- **system_prompt rule** (read every turn): файлы для владельца сохранять ТОЛЬКО в
  `/root/.hermes/outbox`; никогда не утверждать «отправил», пока вложение реально не ушло.
- `gateway.media_delivery_allow_dirs: [/root/audits, /root/.hermes/outbox, /tmp, audio caches]`.
- **Always verify delivery — never claim «отправил» without confirmation.** For a hard-confirmed
  binary attachment, bypass the agent loop and use the Telegram Bot API directly:
  `curl -s -F chat_id=<id> -F document=@<path> "https://api.telegram.org/bot<токен>/sendDocument"` →
  check `"ok":true` (token in `/root/.hermes/.env`, chat id in `telegram.allowed_chats`).
  Note: `hermes send --file` sends a **text body**, not an attachment.

**⚠️ Never put shell examples with secret-looking env vars into SOUL.md** (or any per-turn context
file). The prompt threat scanner (`tools/threat_patterns.py`) flags `curl …$TOKEN`-shaped text as
`exfil_curl` and **silently drops the ENTIRE file from every prompt** (journal:
`Context file SOUL.md blocked: exfil_curl`). Exactly this happened 2026-06-06→11: the
delivery-verification advice added to SOUL contained the literal curl/$TOKEN example, SOUL stopped
loading at all, and the agent lost все свои правила поведения (включая «файлы только в outbox»).
Keep concrete commands in the brain docs; in SOUL — only a reference. After editing SOUL, verify:
`scan_for_threats(open('/root/.hermes/SOUL.md').read())` in the venv must return nothing.

## Auxiliary LLMs (compression, titles, web-extract, approval-judge…) on Groq
The gateway runs ~10 auxiliary mini-tasks (`auxiliary.*` in config.yaml) on a side model. Gotchas
found 2026-06-10 when moving them to Groq (free, fast):

- **Groq free-tier limits are per-MINUTE token caps and they are SMALL** (verified 2026-06-11 via
  `x-ratelimit-*` headers): `llama-3.3-70b-versatile` = **12 000 TPM**, 1 000 RPM;
  `llama-3.1-8b-instant` = **6 000 TPM**, 14 400 RPM. A single request bigger than the TPM cap is
  rejected outright — and the aux client classifies that as a *payment/credit error* and marks the
  whole custom provider **unhealthy for 600 s**, killing ALL Groq aux tasks (titles, approval…)
  for 10 minutes. This cascaded all day 2026-06-11: compression payloads ~70k tokens → instant
  reject → fallback to the codex aux (the main ChatGPT brain) → 120 s stream timeouts per attempt →
  «model is very slow» for the owner. **Sizing rule: every aux task's worst-case payload must fit
  the model's TPM cap.**
- **Split (2026-06-11):** small tasks (`title_generation`, `skills_hub`, `approval`,
  `triage_specifier`, `kanban_decomposer`, `profile_describer`, `curator`) → `llama-3.1-8b-instant`
  (faster, huge RPM); `compression` + `web_extract` (bigger payloads) → `llama-3.3-70b-versatile`
  (12k TPM). `auxiliary.compression.timeout: 45` (was 120) so a broken summarizer fails fast to the
  deterministic static-fallback summary instead of stalling the turn.

- **There is NO first-class provider named `groq`.** `provider: groq` →
  `resolve_provider_client: unknown provider 'groq'` → compression silently degrades to
  "drop middle turns without a summary" (and on 2026-06-10 this crashed the gateway at 04:10).
  `hermes auth add groq` fails the same way. Valid aux providers: `openrouter`, `nous`,
  `openai-codex`, `custom`, `auto`, …
- **The working shape is a custom endpoint** — per `auxiliary.<task>`:
  `provider: custom`, `model: llama-3.3-70b-versatile`, `base_url: https://api.groq.com/openai/v1`,
  `api_key: ${GROQ_API_KEY}`. The config loader expands `${ENV}` references, so no plaintext key
  lives in config.yaml (references only, per the secrets policy).
- **The key itself** sits in `/root/.hermes/secure/hermes-gateway.env` (600) and is loaded via
  `EnvironmentFile=` in `hermes-gateway.service`; the same `GROQ_API_KEY` also feeds voice STT
  (whisper on Groq). Note: aux `custom` does NOT read `GROQ_API_KEY` by itself (only
  `explicit api_key or OPENAI_API_KEY`), hence the `${GROQ_API_KEY}` reference in each task block.
- **Verify after a change** with a direct in-venv call (no gateway restart loops):
  `call_llm(messages=[…], task='title_generation')` from `agent.auxiliary_client` — and check the
  journal of the NEW pid only; the draining old process still logs old-config warnings.

## Context: автосжатие и жизнь сессий (2026-06-10)
Three mechanisms manage a growing dialog; know which is which:

- **Auto-compression** (`compression.*` + `context.engine: compressor`) — fully automatic, no owner
  confirmation: when the session passes `threshold` (fraction of the model's context length) the
  middle of the dialog is summarised by the auxiliary model into ~`target_ratio`, keeping
  `protect_first_n: 3` and the last `protect_last_n` messages verbatim. History: 0.5 → 0.2
  (2026-06-10) → **0.05, protect_last_n 10** (2026-06-11). Rationale for 0.05 (~16k tokens with the
  320k window): (а) the main model's working context stays small → every turn is fast and cheap;
  (б) the compression payload (the summarized middle) stays well under Groq's 12k-TPM cap, so the
  LLM summary actually succeeds instead of cascading into provider-unhealthy + codex-timeout (see
  the Groq section — this is what made the 2026-06-11 prostavki MCP session crawl for ~2 hours).
  Requires a working `auxiliary.compression` provider; without it compression degrades to a
  deterministic static summary / dropping middle turns.
- **`telegram_context_guard`** — the «Сжать контекст?» inline-button prompt in Telegram. It was a
  band-aid added while auto-compression was broken (no aux model). **Disabled 2026-06-10**
  (`enabled: false`): with working auto-compression it only added manual confirmations. Re-enable
  only if sessions ever blow up again despite the compressor.
- **`session_reset`** — fresh session after `idle_minutes: 30` of silence and daily at
  `at_hour: 4` (mode `both`). This is the "topic change" proxy: came back after a pause → clean
  context. There is **no built-in topic-change detector** in Hermes (checked 2026-06-10); an
  LLM-based one would need a gateway patch — don't (patch fragility, see `hermes-self-repair`).
  For an instant mid-conversation switch the owner sends `/new`.

## Реакции-статусы в Telegram (2026-06-10)
Включаются одним флагом `telegram.reactions: true`. Встроенный lifecycle (`gateway/platforms/
telegram.py`, `on_processing_start`/`on_processing_complete`): 👀 (U+1F440) ставится на сообщение
владельца, как только агент начал его обрабатывать → 👍 (U+1F44D) при успешном завершении, 👎
(U+1F44E) при ошибке; при отмене (`/stop`) реакция снимается. Один вызов `set_message_reaction`
заменяет предыдущую. Бесплатно, нативно, ничего больше настраивать не нужно. (ВК-аналога нет — см.
`skills/vk-hermes-bridge-mvp`.)

## Голос: ударения и натуральность (2026-06-10)
- **edge honors знаки ударения**: острое ударение U+0301 на гласной (`за́мок` vs `замо́к`) edge
  рендерит по-разному — проверено (три варианта = три разных аудио). Поэтому ПРАВИЛЬНАЯ постановка
  ударения решается на уровне **текста**, который агент отдаёт в TTS: SOUL-правило просит ставить
  знак ударения на омографах и редких словах (LLM снимает неоднозначность из контекста). Ноль
  инфраструктуры, ноль задержки.
- **Почему НЕ ML-расстановка** (`ruaccent`): протестирована изолированно с лимитом памяти
  (2026-06-10) — пик RSS **761 МБ** и загрузка модели **~92 с** на холодную. На 1 ГБ box это либо
  OOM-риск (нарушает правило «не перегружать прод»), либо при персистентном сервисе навсегда съедает
  весь запас RAM; плюс tiny-модель всё равно ошибается на омографах. Вердикт: не ставить здесь.
  Удалено. Если появится бюджет — либо +RAM (тогда персистентный сервис ruaccent turbo), либо
  облачный TTS (см. ниже).
- **Натуральность («роботизированность»)** — врождённое свойство бесплатного edge-TTS, локально не
  лечится. Настоящий апгрейд = облачный TTS с хорошей русской просодией: ElevenLabs multilingual
  (платно, лучшее качество) или Gemini TTS (есть бесплатный лимит). Меняется через `tts.provider` +
  ключ — отдельным шагом по решению владельца. Альтернативный женский голос edge:
  `ru-RU-SvetlanaNeural`.

## Голосовые ответы (2026-06-10)
Полная цепочка живёт из коробки и проверена end-to-end:
- Инструмент `text_to_speech` (tools/tts_tool.py), провайдер `edge` (бесплатный, без ключа),
  голос `tts.edge.voice: ru-RU-DmitryNeural` (был английский en-US-AriaNeural — поменян).
  Альтернатива: `ru-RU-SvetlanaNeural` (женский). Требует ffmpeg (стоит) для .ogg.
- Инструмент возвращает `MEDIA:<путь>` — Telegram-адаптер шлёт `.ogg/.opus` как голосовой кружок
  (`send_voice`). **Аудио-кэш добавлен в `gateway.media_delivery_allow_dirs`**
  (`/root/.hermes/cache/audio`, `/root/.hermes/audio_cache`) — без этого вложение молча дропается
  (грабли от 06-06).
- Правило в SOUL: просят голосом → `text_to_speech` (.ogg) → MEDIA; текст разговорный без
  markdown/списков, длинное сократить (<1 мин); доставку подтверждать, при сбое — честно текстом.
- Входящие голосовые уже расшифровываются (STT groq whisper, `GROQ_API_KEY`).

## Applying changes
Edit `config.yaml` (back it up first), then restart the gateway **from outside it** (SSH / systemd),
never from a chat turn: `systemctl restart hermes-gateway`. Most `display.*` settings are re-read per
turn; `system_prompt` and a few init-time ones need the restart. Verify: `systemctl is-active
hermes-gateway` + check the new process PID is fresh in `systemctl status`.
