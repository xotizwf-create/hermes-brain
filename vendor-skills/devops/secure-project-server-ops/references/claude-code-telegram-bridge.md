# Claude Code Telegram bridge debugging notes

Use this when a custom Telegram bridge shells out to Claude Code / Claude CLI and behavior looks wrong even though the PM2/systemd process is online.

## Durable pitfalls from 2026-06 bridge fix

1. **Do not classify limits by substring-searching the raw event stream.** Claude Code can emit non-error `rate_limit_event` / usage telemetry during a successful response. Treat the final structured result first: if the final `result` has `subtype: success` and `is_error: false`, deliver the answer. Only report a real account/provider limit when the final result is an error/abort or the API headers/CLI error explicitly say the request is blocked.
2. **Separate three different concepts in user-facing text:**
   - real Claude/account/provider limit;
   - local per-answer safety budget / timeout;
   - context/session management.
   Do not tell the owner “упёрлись в лимит Claude Pro” when only the bridge’s local budget fired.
3. **Never auto-reset/switch conversation sessions just because cumulative cached/read tokens are high.** Cache-read and cumulative usage counters are not the same as the live context window. Let Claude report real context overflow; use `/new` only when the owner explicitly wants a clean thread.
4. **Two-step Telegram commands need explicit pending state.** If `/switch` displays numbered sessions and expects the next message to be a number, persist a `pendingSwitchChat`/equivalent state before returning. Otherwise the next message like `3` is forwarded to Claude as a prompt.
5. **Verify the CLI independently before blaming the bridge.** Run a minimal Claude Code/CLI prompt and inspect the structured stream/result, not just stderr text. A successful direct result plus a failed bot response means the bridge parser/state machine is suspect.
6. **After patching, verify both layers:** `node --check` or equivalent syntax check, PM2/systemd status, bridge state file (`active`, known sessions, pending flags), and a lightweight provider/API header check showing account status allowed.

## Minimal verification shape

- Syntax: `node --check bridge.js`
- Process: `pm2 describe <app>` or `systemctl status <unit>`
- State: read and summarize only non-secret fields such as active session, session ids, pending switch flag
- Provider: make a tiny authenticated request or CLI ping, but print only HTTP status and rate-limit status/percent headers, never tokens

## What to tell the owner

Keep the report practical and short: what was broken, what changed, what was verified, and the exact command to retry (`/switch` then `3`, for example). Avoid dumping raw event streams or secret paths unless explicitly requested.
