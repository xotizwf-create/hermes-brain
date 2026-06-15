---
name: small-prod-edit
description: Use for a tiny, well-scoped change on a live production service — replacing a support-text string, flipping a config value, fixing one line — where spinning up a full coding session is overkill. Enforces a fast, safe discipline (backup → exact replace → verify match count → restart only the affected service → check logs → short report) and forbids diagnosing subsystems that aren't reported broken. Built after the 2026-05-31 incident where a one-line edit took far too long and rattled prod.
---

# Skill: small-prod-edit

## When to use
A genuinely small live change: one support-text string, a config flag, a single line. For anything
larger (functions, refactors, multi-file, debugging) use `skills/codex-delegation` instead. The whole
point of this skill is **speed with safety** — after access is in hand, the edit should take a couple
of minutes, not an open-ended diagnostic expedition.

## The scope rule (this is the important one)
**Do not diagnose subsystems that aren't reported broken.** A one-string change in the bot does not
require checking the site, the database, nginx, or full server load. Touch only what the task is
about. Diagnose wider **only if** something you actually need is failing (e.g. the service won't
restart). The 2026-05-31 over-diagnosis (site/DB/nginx checks for one string) is exactly what to
avoid.

## Workflow (do these in order, fast)
1. **Identify** the exact file and the one service that serves it. Don't guess broadly.
2. **Backup** the file first: `cp file file.bak.$(date +%s)`.
3. **Replace exactly.** Use an exact, unambiguous match. If the old string appears N times and you
   mean all N, say so; if you mean one, target one.
4. **Verify the result deterministically**, not with a loose search:
   ```bash
   grep -c 'NEW STRING' file   # expected count
   grep -c 'OLD STRING' file   # must be 0
   ```
   If a quick search gives a contradictory result, trust an exact `grep -F` / `diff`, don't loop.
5. **Restart only the affected service**, time-boxed, from outside any chat turn:
   `timeout 60 systemctl restart <service>`. Do **not** restart the site, DB, or the whole box.
6. **Check health**: `systemctl is-active <service>` + ~20 lines of its log for errors. For a bot,
   confirm it talks to its API (without printing tokens).
7. **Report briefly**: file, replacements made, service restarted, logs clean. Nothing else.

## If the restart hangs / SSH stops responding
- An open SSH port that doesn't return a prompt usually means SSH is busy/hung, **not** that the app
  is down and **not** a wrong password. Check the app from outside (HTTP) before assuming an outage.
- Don't escalate to rebooting the whole server on a guess. Wait briefly, reconnect with short
  timeouts, confirm the service is actually the problem before any heavy action.

## Rules
- Backup before editing; restart only the affected service; verify health before reporting.
- Stay in scope — no subsystem fishing.
- Prefer git-first (`engineering/agentic-coding.md`) when the file lives in a repo; direct live edit
  is for the truly tiny tail-end case.
- If a hotfix touches live data and the API/UI still shows the bug after the DB looks correct, treat it as a data+serializer issue: verify through the same outward layer and patch the smallest serving code path too. See `references/live-data-plus-serializer-fix.md`.
- Secrets: references only; never printed or committed.

## Done when
The exact change is in place (verified by count), only the target service was restarted, its logs are
clean, and the owner got a short report — without unnecessary diagnosis of unrelated subsystems.
