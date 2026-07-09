---
name: codex-delegation
description: Use whenever a task involves writing or changing code beyond a single trivial line — new functions, refactors, multi-file edits, fixing a stack trace, implementing a feature, writing tests. Hand the actual coding to the Codex CLI (`codex exec`) running in the repo, with Hermes acting as orchestrator (brief → review diff → test → deploy), and pick the reasoning mode per task — `high` by default, `xhigh` (maximum) for architecture/refactors/hard bugs — so the code comes out at Codex's best quality instead of being free-handed through generic tools.
---

# Skill: codex-delegation

## Why
Hermes' brain is `gpt-5.5` via `openai-codex` — the *same* engine as the Codex CLI — but Hermes runs
it at throttled reasoning, with session compression and a generic tool loop. The Codex CLI
(`@openai/codex`, already installed on prod, see `projects/albery/hermes.md`) runs the **purpose-built
coding harness**: high reasoning, `apply_patch`, repo awareness (`AGENTS.md`/`CLAUDE.md`), and an
edit→run-tests→fix loop. Delegating the coding to it gives "Codex out of the box" quality on the same
ChatGPT account, in a separate process whose context can't be corrupted by Telegram compression.

**Hermes stays the orchestrator. Codex writes the code.**

## When to use vs not
- **Delegate**: writing/changing functions, refactors, multi-file edits, debugging a stack trace,
  implementing a feature, writing tests, anything where code quality matters.
- **Don't delegate** (do it directly via `skills/small-prod-edit`): a single trivial text/config
  string change on a live service. Spinning up Codex for one line is overkill.

## Pick the reasoning mode per task (before writing the brief)
Canonical matrix lives in `engineering/agentic-coding.md` («Reasoning-mode matrix»). Short form:

- **`high` — дефолт для кода**: функция, багфикс по стектрейсу, тесты, правка в 1–3 файлах.
- **`xhigh` — максимальный режим**: архитектура/дизайн, многофайловый рефакторинг, гейзенбаги/
  гонки/async, миграции БД с данными, security-чувствительный код, или задача уже провалена на
  `high` (два противоречивых диффа → перезапуск одной чёткой задачей на `xhigh`, свежий контекст).
- **Никогда `medium`/`low` для кода.** Лимит экономим сужением задачи, не режимом.
- На первом боевом `xhigh`-прогоне сверь шапку вывода `codex exec` (`reasoning effort: xhigh`) —
  бэкенд не должен молча даунгрейдить.

## Precondition: Codex must be installed AND its token must actually work
1. Installed: `command -v codex && codex --version`. On `217.198.12.236`: `codex-cli 0.135.0` at
   `/usr/bin/codex`, `/root/.codex/config.toml` pins `model_reasoning_effort = "high"` (per-flag
   still wins), outbound via VPN-Estonia (no 403). On `186.246.7.32` codex CLI is present
   (0.134.0) but **not logged in** (verified 2026-07-09) — delegation there needs auth first.
2. **Auth — do NOT trust `codex login status`.** It only reads the local file: on 2026-07-09 it
   said «Logged in using ChatGPT» while every real call died with «access token could not be
   refreshed… sign in again» (token invalidated by a login elsewhere). Honest check = micro-exec:
   `echo ok | codex exec --skip-git-repo-check -` (копейки токенов, мгновенно видно 401).
3. If the token is dead: **tell the owner immediately** (needs `codex login` re-auth or a fresh
   `auth.json` from the PC, mode 600). Urgent fix that can't wait → do it by hand under
   `skills/karpathy-guidelines` discipline with extra-careful review; non-urgent → wait for re-auth.
   (`hermes -z` is NOT an equivalent fallback for quality: it has no per-run reasoning flag and
   runs at the global chat effort.)
If you land on a host where codex is absent, install + auth first (`npm install -g @openai/codex`,
copy `~/.codex/auth.json` from the PC to `/root/.codex/auth.json` 600, verify VPN/403, set
`config.toml` → `model_reasoning_effort = "high"`). See `projects/albery/hermes.md`.

## Workflow
1. **Locate & prep the repo** on the work host (clone/branch per `skills/project-onboarding`; branch
   off `main`, never code on `main`). Ensure the repo has `AGENTS.md`/`CLAUDE.md` if it carries one —
   Codex reads it.
   - For cleanup/refactor PRs, keep the first slice small and reviewable. If Codex cannot be used after a quick precondition check, do not stall a tiny low-risk cleanup: make the bounded change directly, preserve public APIs, and verify with the same rigor as a Codex-produced diff. See `references/pr-cleanup-and-audit.md`.
2. **Brief Codex precisely.** One task, concrete acceptance criteria, point it at the files/area.
   Run it in the repo dir so it has full context:

   ```bash
   cd /path/to/repo && codex exec --skip-git-repo-check \
   -c model_reasoning_effort="high" \   # или "xhigh" — по матрице режимов
   "Задача: <что сделать>. \
   Критерий готовности: <как понять что сделано>. Не трогай <запретные зоны>. \
   После правки прогони <тесты/линт>."
   ```

   - **Always pin the reasoning effort explicitly** — `high` by default, `xhigh` for hard tasks
     (see the mode matrix above / `engineering/agentic-coding.md`). Codex CLI's own default is
     `medium`, not high — the deep, careful thinking we want from gpt-5.5 during coding only
     happens if we set it. This is the whole point of delegating: Hermes stays at `medium`
     (chat, limit-friendly), Codex thinks at `high`/`xhigh` (code).
     Caveat: higher effort consumes more reasoning tokens → burns the shared ChatGPT 5h limit
     faster, so keep tasks scoped and don't fire Codex for one-liners (those go to `small-prod-edit`).

   - Heavy/long jobs need room: Codex sessions can run minutes. If invoked from a cron `--script`,
     respect `cron.script_timeout_seconds` (900s on prod); from a chat turn it's a code task (3600s
     budget — see classifier note in `engineering/agentic-coding.md`).
   - Codex uses the same `~/.codex/auth.json` / ChatGPT account; outbound must go via VPN (Estonia)
     or OpenAI returns 403 (see `hermes.md`).
3. **Review the diff** before anything ships: `git diff`. Hermes is responsible for the change — read
   it, don't rubber-stamp. Optionally run `skills/aislop-code-quality` on the diff to catch slop.
4. **Test locally**: project typecheck/lint/tests. Don't proceed on red.
5. **Deploy git-first** (backup → deploy script → restart only the target service → verify health),
   per `engineering/agentic-coding.md` and `engineering/deployment.md`. For a tiny live tail-end edit
   use `skills/small-prod-edit`.
6. **Report briefly**: what changed, tests result, what was restarted, health after. No tool internals.

## Rules
- Beyond a one-liner, code through Codex — don't free-hand multi-step edits through raw file/terminal
  tools (that's what produced the slow, low-quality 2026-05-31 edit).
- Run Codex at the effort the mode matrix dictates: `high` default, `xhigh` for hard/architectural/
  failed-on-high tasks. Never drop it to medium/low to save the limit — instead narrow the task.
  (Hermes' *own* knob stays `medium`; only the Codex subprocess goes high/xhigh.)
- Always review and test Codex's diff; you own the result.
- Never push to `main` without explicit ask; open a PR with a diff summary.
- Never let the orchestrating session `/compress` while a Codex job is mid-flight.
- Secrets: references only; never printed, committed, or passed as CLI args.

## Done when
Codex produced the change in a branch, Hermes reviewed the diff and ran tests green. For PR-only cleanup/refactor work, open the PR, verify GitHub checks, and report the PR URL/stack base without deploying. For requested live changes, deploy git-first with only the target service restarted, verify health, and give a short human report.
