---
id: hermes-brain-incidents
type: project
project: hermes-brain
tags: [incidents]
updated: 2026-06-20
secret_refs: []
---

# Hermes Brain — incidents

## 2026-06-20 — `claude-tg` bot spent Claude Code limit and stayed silent

Owner reported that the Telegram bot connected to Claude Code on the 217 Hermes Brain server accepted prompts, consumed the Claude limit, and did not answer/progress-report.

Findings:
- The live side service is PM2 app `claude-tg`, script `/root/claude-agent/bridge.js`.
- The bridge previously ran Claude Code with `--model opus --output-format json` and only sent Telegram typing actions until the process exited.
- A live minimal Claude Code check returned a 5-hour rate-limit event with reset at `2026-06-21 02:40 MSK` and zero new token usage.
- The local state showed only two bridge requests, but large cached-token usage; the problem was heavy Claude Code sessions rather than Telegram polling itself.

Fix applied:
- Corrected the bridge back to the owner-required Claude Code default: Opus + medium effort + `stream-json` + request budget cap.
- Added a cheap account-limit preflight before the expensive Opus run so an exhausted account returns a clear message instead of burning another coding session.
- Forward short assistant progress text from the stream to Telegram, in addition to tool-use based status messages, so the owner sees what Claude is doing before the final answer.
- Persist Claude Code `session_id` as soon as any stream event contains it; this keeps `/new`, `/sessions`, `/switch`, and follow-up context closer to the Hermes-style session model even if the run ends via limit/error.
- Added second-layer quota protections after the post-incident review: block new expensive runs when account utilization is already dangerously high, warn at high utilization, cap oversized Telegram text prompts, auto-start a fresh Claude session when the active session becomes too context-heavy, and return an explicit timeout message instead of staying silent.
- Verified `node --check` passes and PM2 app is online after restart. A live account-limit check still returned 5-hour status `rejected` until `2026-06-21 02:40 MSK`, so a full Opus end-to-end test must wait for reset.
