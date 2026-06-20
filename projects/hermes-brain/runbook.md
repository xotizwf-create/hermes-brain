---
id: hermes-brain-runbook
type: project
project: hermes-brain
tags: [runbook, ops]
updated: 2026-06-20
secret_refs: []
---

# Hermes Brain — runbook

## Adding/updating projects
Use the brain skill `skills/add-project/`: create/update `projects/<slug>/`, regenerate `projects/registry.yaml`, validate, then commit after approval/explicit instruction.

## Updating instructions
Prefer the nearest existing instruction/skill. If no close instruction exists, create a small new one. Keep durable procedures in skills/instructions, not in chat memory.

## Validation
Run the repository validation script before finalizing changes. Fix frontmatter and secret-leak warnings before committing.

## Troubleshooting
- Bad project registry → regenerate from manifests, do not hand-edit registry.
- Missing project context → load `projects/registry.yaml`, then the specific project folder only.
- Risky Hermes config/gateway change → use the Hermes Agent skill and avoid changes that could disconnect Telegram without rollback.

## Side service: `claude-tg` Telegram → Claude Code bridge on the 217 box
This is a separate PM2 Node bridge, not the main Hermes gateway. It lives at `/root/claude-agent/bridge.js` and runs as PM2 app `claude-tg` with cwd `/root/claude-agent`.

Operational notes:
- Always run the server preflight before touching it: this host is small (~1 GB RAM), so avoid builds/heavy tests on-box.
- Diagnose with `pm2 describe claude-tg`, `pm2 logs claude-tg --nostream --lines 100`, and a syntax check `node --check /root/claude-agent/bridge.js` before restart.
- The bridge uses the Claude Code OAuth token from the local secure store and must never print token values in logs or chat.
- Keep the Telegram mode responsive: send an immediate acknowledgement, stream/forward short human-readable Claude progress statuses from `stream-json`, and send an explicit Claude limit message instead of waiting silently for the final result.
- This bot is a Claude Code coding agent: keep the default model at Opus for code quality. Save limits with medium effort, `stream-json` output, a per-request budget cap, and a cheap account-limit preflight before starting the expensive Opus run.
- Quota safety rails are mandatory: block new tasks when the Claude account is already above the configured danger threshold, warn when it is high, stop long runs by timeout, and automatically start a fresh Claude session when the active session has accumulated too much token footprint. Do **not** cap, trim, or summarize owner Telegram input before handing it to Claude Code: input data may be any size and should behave like the current Hermes project. These rails protect against silent quota burn without changing the user's request.
- Preserve conversation context by reusing Claude Code `session_id` with `--resume`; write a new `session_id` to state as soon as it appears in any stream event, not only after a normal final result.
- Claude Code stream-json can emit `rate_limit_event` and a synthetic assistant message like “You've hit your session limit”; the bridge should translate that to a clear Russian message with reset time if known, not treat it as a normal final answer.
