---
id: agentic-coding
type: engineering
tags: [hermes, coding, codex, quality, reasoning, compression, prod-edit, delegation]
updated: 2026-05-31
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
| Worse code than Codex | Hermes runs `reasoning_effort=medium` (lowered to save the 5h limit); Codex CLI defaults to high | **Delegate the actual coding to `codex exec`** — it runs its own high-reasoning loop on the same account. Don't raise Hermes globally (burns the shared limit). |
| Long, repetitive, "противоречивый результат" | Context **compressed mid-task** (twice); the model lost precise working state and re-derived it | Code work runs in a **separate process** (`codex exec` / `hermes -z`) with fresh, uncompressed context. Never `/compress` inside an active code task. |
| Task killed after 10 min | Wall-clock guard classified a server edit as **general (600s)**, not code (3600s) | Fix the classifier so file/SSH/systemctl/config edits count as code. |
| Knocked prod around, restarted clumsily | Live surgery over SSH + restart without health discipline | **Git-first** edit→validate→deploy, and the `small-prod-edit` skill for tiny live changes. |
| Over-diagnosed (checked site/DB/nginx for one string) | No "scope discipline" rule | `small-prod-edit`: don't diagnose subsystems that aren't reported broken. |

## The core rule: delegate real coding to Codex
For anything beyond a one-line text/config change — writing functions, refactors, multi-file edits,
debugging stack traces — **Hermes should not free-hand code through its generic terminal/file
tools.** It should hand the job to the purpose-built Codex coding loop and stay the orchestrator
(understand the task → brief Codex → review the diff → test → deploy). See `skills/codex-delegation`.

Why this is the single biggest win:
- **Quality**: Codex has `apply_patch`, repo awareness (`AGENTS.md`/`CLAUDE.md`), and a real
  edit→run-tests→fix loop — that's where "out of the box" quality comes from.
- **Reasoning**: Codex runs at its own high reasoning regardless of Hermes' throttle.
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
3. **Reasoning.** Keep Hermes' own `reasoning_effort=medium` for cheap chat (limit-friendly); get
   high reasoning for code by **delegating to Codex**, not by raising the global knob. Only consider
   global `high` (or an API-key instance with no 5h cap) if delegation isn't enough.

## Hard rules
- Beyond a one-liner, code through Codex (`skills/codex-delegation`), not free-hand tool calls.
- Backup before any live edit; restart only the affected service; verify health before reporting.
- Don't diagnose subsystems that aren't reported broken (`small-prod-edit` scope discipline).
- Never let a session compress while a code task is in flight.
- Secrets: references only — never printed, committed, or passed as CLI args.
