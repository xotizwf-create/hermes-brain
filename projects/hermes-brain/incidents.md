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
- Changed bridge execution to Sonnet + medium effort + `stream-json` + request budget cap.
- Added immediate acknowledgement, 30-second progress messages, tool-use based status messages, and explicit Russian handling for Claude limit/rate-limit responses.
- Verified `node --check` passes and PM2 app is online after restart.
