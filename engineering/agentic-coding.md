---
id: agentic-coding
type: engineering
tags: [hermes, coding, codex, quality, reasoning, compression, prod-edit, delegation, modes]
updated: 2026-07-09
secret_refs: []
---

# Agentic coding — make Hermes code like Codex, not like a throttled generic agent

The brain (Hermes) and the model it runs on are the **same** engine — `gpt-5.5` via the
`openai-codex` provider (= the ChatGPT account, see `projects/albery/hermes.md`). So when Hermes
writes worse code than `codex` on the CLI, the model is **not** the cause. The gap is the **harness
around the model**. Codex "out of the box" is good because it: (a) thinks at high reasoning, (b) runs
a tight read→edit→verify loop with a real patch tool, (c) keeps full working context for the task,
(d) isn't killed by a short time budget. The prod Hermes is configured the opposite way for cost
reasons, and that — not the model — is what produced the slow, repetitive, prod-rattling one-line
edit on 2026-05-31.

## Root causes (mapped to that incident)
| Symptom | Real cause | Lever |
|---|---|---|
| Worse code than Codex | Hermes runs a throttled global `reasoning_effort` (chat-friendly; at one point it drifted all the way down to `low` — caught 2026-07-09) | **Delegate the actual coding to `codex exec` pinned at `high`/`xhigh` per the mode matrix above** — a separate high-reasoning loop on the same account. Codex CLI's own default is `medium`, so the effort must be set explicitly (see `skills/codex-delegation`). Don't raise Hermes globally beyond `medium` (burns the shared limit on chat). |
| Long, repetitive, "противоречивый результат" | Context **compressed mid-task** (twice); the model lost precise working state and re-derived it | Code work runs in a **separate process** (`codex exec` / `hermes -z`) with fresh, uncompressed context. Never `/compress` inside an active code task. |
| Task killed after 10 min | Wall-clock guard classified a server edit as **general (600s)**, not code (3600s) | Fix the classifier so file/SSH/systemctl/config edits count as code. |
| Knocked prod around, restarted clumsily | Live surgery over SSH + restart without health discipline | **Git-first** edit→validate→deploy, and the `small-prod-edit` skill for tiny live changes. |
| Over-diagnosed (checked site/DB/nginx for one string) | No "scope discipline" rule | `small-prod-edit`: don't diagnose subsystems that aren't reported broken. |

## Reasoning-mode matrix — под каждую задачу свой режим (canonical, 2026-07-09)

Режим ума — это не одна ручка, а **выбор исполнителя + выбор `reasoning_effort` под задачу**.
Правило: **чат дёшево, код дорого, сложный код — максимально дорого.** Перед любой кодинг-задачей
явно выбери строку из этой таблицы (и скажи владельцу, в каком режиме работаешь, одним словом).

| Задача | Исполнитель | Режим |
|---|---|---|
| Чат, вопросы, отчёты, оркестрация, cron-дайджесты | Hermes gateway | глобальный `reasoning_effort: medium` в `~/.hermes/config.yaml` (**не** `low` — на `low` агент заметно тупит; дрейф low обнаружен и исправлен 2026-07-09) |
| Однострочная правка текста/конфига на живом сервисе | напрямую, `skills/small-prod-edit` | режим не трогаем — Codex не нужен |
| Обычный кодинг: функция, багфикс по стектрейсу, тесты, правка в 1–3 файлах | `codex exec` | `-c model_reasoning_effort="high"` (дефолт для кода) |
| Сложный кодинг: архитектура/дизайн, многофайловый рефакторинг (напр. распил `app.py` Альбери), гейзенбаги/гонки/`asyncio`, миграции БД с данными, security-чувствительный код, задача уже провалена на `high` | `codex exec` | `-c model_reasoning_effort="xhigh"` — **максимальный режим** |

Правила эскалации/де-эскалации:
- **Эскалация**: если Codex на `high` дважды не решил задачу или диффы выходят противоречивые —
  не дробить на переписку, а перезапустить **одной чёткой задачей на `xhigh`** со свежим контекстом.
- **Никогда не де-эскалировать код до `medium`/`low`** ради экономии лимита — вместо этого сузить
  задачу. Экономия режима на коде = переделки, которые стоят дороже (урок 2026-05-31).
- `xhigh` жжёт общий 5h-лимит ChatGPT заметно быстрее `high` — используем его по матрице, а не
  «на всякий случай»; задачи держим узкими. (`xhigh` принимается codex-cli 0.135.0; проверен
  синтаксически 2026-07-09, первый боевой прогон сделать после re-auth и убедиться, что бэкенд
  не молча даунгрейдит — сверить `reasoning effort` в шапке вывода `codex exec`.)
- Ручки у `hermes` CLI **нет**: `hermes -z` не принимает per-run reasoning-флаг, он всегда идёт на
  глобальном значении из `config.yaml`. Поэтому per-task режимы реализуются только через Codex.

**Честный preflight перед делегированием** (обязателен): `codex login status` **врёт** — 2026-07-09
он показывал «Logged in using ChatGPT», а реальный вызов падал с «access token could not be
refreshed… sign in again» (токен инвалидирован входом с другого устройства). Честная проверка —
микропрогон: `echo ok | codex exec --skip-git-repo-check -` (копейки токенов). Если токен мёртв:
1) сразу сообщить владельцу — нужен `codex login` заново (или свежий `auth.json` с ПК, mode 600);
2) срочный фикс, который нельзя ждать, делать вручную по `skills/karpathy-guidelines` +
   `skills/small-prod-edit`-дисциплине, с удвоенным ревью; несрочное — дождаться re-auth.

## The core rule: delegate real coding to Codex
For anything beyond a one-line text/config change — writing functions, refactors, multi-file edits,
debugging stack traces — **Hermes should not free-hand code through its generic terminal/file
tools.** It should hand the job to the purpose-built Codex coding loop and stay the orchestrator
(understand the task → brief Codex → review the diff → test → deploy). See `skills/codex-delegation`.

Why this is the single biggest win:
- **Quality**: Codex has `apply_patch`, repo awareness (`AGENTS.md`/`CLAUDE.md`), and a real
  edit→run-tests→fix loop — that's where "out of the box" quality comes from.
- **Reasoning**: Codex is pinned to `high` (`-c model_reasoning_effort="high"`) for coding — deep,
  careful thinking from gpt-5.5 — independent of Hermes' `medium` chat throttle.
- **Context**: it's a separate process, so Telegram session compression can't corrupt mid-task state.
- **Cost is unchanged**: same ChatGPT account/quota, just used through the better harness.

## Git-first over live SSH
Default flow for project code (mirrors `project-onboarding` + the brain's own deploy scripts):
1. Edit in the repo (branch off `main`), not by hand on the live box.
2. Validate locally — typecheck/lint/tests, project `validate` if present.
3. Deploy with a script that **backs up first** and **restarts only the target service**.
4. Verify health, then report.

Touch the live server directly only for genuinely tiny, well-scoped changes — and then via
`skills/small-prod-edit`, which enforces backup → exact replace → verify count → restart only that
service → check logs.

## Server config for coding quality
These live in `~/.hermes/config.yaml` and the `run.py` task-classifier patch (server-only, 600; the
brain documents, the server holds). Apply per `skills/update-knowledge` + `hermes_apply_patches.py`,
back up first, restart the gateway from **outside** a chat turn. Current values: see
`projects/albery/hermes.md`.

1. **Do not compress mid code-task.** Compression rewriting the transcript is the main quality
   killer. Preferred fix: code runs in a separate process (delegation / `hermes -z`), so the
   Telegram session guard never fires on it. If a code task must run in-session, raise
   `compression.protect_last_n` and do not trigger `/compress` until it finishes.
2. **Classify edits as code.** The wall-clock guard's keyword classifier (in `gateway/run.py`,
   re-applied by `hermes_apply_patches.py`) must treat these as code → 3600s budget: file path,
   `.env`, config, `systemctl`/service, SSH/server edits, "правка"/"замени"/"замени текст"/"на
   сервере"/"в боте"/"в коде". A tiny support-text edit that ends in a service restart is a code
   task, not a 10-minute chat task.
3. **Reasoning.** Keep Hermes' own `reasoning_effort: medium` for chat (limit-friendly; **never
   `low`** — that's the "агент отупел" setting, drift caught & fixed 2026-07-09); get deep reasoning
   for code by **delegating to Codex with the effort chosen per the mode matrix above** (`high`
   default, `xhigh` for hard tasks; Codex's own default is `medium`, so it must be set explicitly),
   not by raising the global knob. Trade-off: `high`/`xhigh` spend more reasoning tokens against the
   shared 5h limit — accepted for coding quality; keep tasks scoped. The server-wide Codex default in
   `/root/.codex/config.toml` is `model_reasoning_effort = "high"` (the per-invocation flag still
   wins and is the canonical guarantee). Only consider raising Hermes' global knob — or an API-key
   instance with no 5h cap — if delegation isn't enough.

## Hard rules
- Before any non-trivial code task (write/edit/refactor/review/debug), load and follow
  `skills/karpathy-guidelines`: think before coding (surface assumptions, ask), simplicity first,
  surgical changes (don't touch unrelated code/comments), verifiable success criteria.
- Beyond a one-liner, code through Codex (`skills/codex-delegation`), not free-hand tool calls.
- Before delegating: pick the reasoning mode from the **mode matrix** above (`high` default, `xhigh`
  for hard/architectural/failed-on-high tasks) and run the honest auth preflight (micro-exec, not
  `codex login status`).
- Backup before any live edit; restart only the affected service; verify health before reporting.
- Don't diagnose subsystems that aren't reported broken (`small-prod-edit` scope discipline).
- Never let a session compress while a code task is in flight.
- Secrets: references only — never printed, committed, or passed as CLI args.
