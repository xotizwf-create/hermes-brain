---
name: codex-delegation
description: Use whenever a task involves writing or changing code beyond a single trivial line — new functions, refactors, multi-file edits, fixing a stack trace, implementing a feature, writing tests. Hand the actual coding to the Codex CLI (`codex exec`) running in the repo, with Hermes acting as orchestrator (brief → review diff → test → deploy), so the code comes out at Codex's own out-of-the-box quality instead of being free-handed through generic tools.
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

## Workflow
1. **Locate & prep the repo** on the work host (clone/branch per `skills/project-onboarding`; branch
   off `main`, never code on `main`). Ensure the repo has `AGENTS.md`/`CLAUDE.md` if it carries one —
   Codex reads it.
2. **Brief Codex precisely.** One task, concrete acceptance criteria, point it at the files/area.
   Run it in the repo dir so it has full context:

   ```bash
   cd /path/to/repo && codex exec --skip-git-repo-check "Задача: <что сделать>. \
   Критерий готовности: <как понять что сделано>. Не трогай <запретные зоны>. \
   После правки прогони <тесты/линт>."
   ```

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
- Always review and test Codex's diff; you own the result.
- Never push to `main` without explicit ask; open a PR with a diff summary.
- Never let the orchestrating session `/compress` while a Codex job is mid-flight.
- Secrets: references only; never printed, committed, or passed as CLI args.

## Done when
Codex produced the change in a branch, Hermes reviewed the diff and ran tests green, it was deployed
git-first with only the target service restarted, health verified, and a short human report given.
