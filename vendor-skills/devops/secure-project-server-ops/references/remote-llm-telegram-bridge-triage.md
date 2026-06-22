# Remote LLM Telegram bridge triage: silence, streaming, and limit burn

Use this reference when a small Telegram bridge on a project server accepts messages, consumes LLM/provider quota, but sends no useful response back to Telegram.

## Durable diagnosis pattern

1. **Protect the main agent/gateway first.** Identify the exact bridge process/app (PM2, systemd, Docker) and restart only that bridge unless the owner explicitly asked for wider work.
2. **Inspect runtime shape before editing.** Check process manager status, app path, command line, recent logs, and the bridge source/config. Redact tokens and long key-like strings from any output.
3. **Look for the silent-expensive pattern:**
   - model defaults to a premium/high-quota mode (for example Opus/high reasoning) for ordinary chat;
   - Telegram only receives `typing` or a single final answer after full completion;
   - provider CLI/API returns JSON only at the end, so rate limits or long runs look like total silence;
   - errors are logged locally but not surfaced to the Telegram user.
4. **Fix behavior, not just status.** A healthy process can still be a bad bot. Prefer:
   - role-appropriate model defaults: use cheaper defaults for ordinary chat, but if the owner identifies the bot as a coding-agent, keep the coding model (for Claude Code, Opus may be intentional) and save quota with medium/lower effort, preflight checks, and hard request limits instead of silently downgrading capability;
   - a cheap provider-limit preflight before starting an expensive coding-agent session when the CLI/API exposes enough signal;
   - streaming/line-by-line CLI mode where available;
   - immediate “accepted/started” acknowledgment;
   - periodic progress messages for long runs;
   - clear user-facing rate-limit/exhaustion message with reset time if the provider exposes it;
   - early session/context persistence as soon as the CLI/API emits a session id, so context survives even if the run later hits a limit or errors;
   - per-request guardrails such as max turns/tokens/time so one prompt cannot burn the whole account.
5. **Verify both paths:**
   - process is online and logs are clean after restart;
   - when quota is exhausted, the Telegram user receives a clear failure instead of silence;
   - after provider reset, run a short real Telegram smoke test and confirm visible progress/final answer.
6. **Persist process-manager state.** For PM2 bridges, run `pm2 save` after a successful restart so reboot does not resurrect the old command/env. If a verification helper fails because it parsed manager output incorrectly, repeat the verification with a simpler command before reporting success.
7. **Document the incident in the project brain/runbook** if this is a recurring owner/project bot, including the exact bridge app name, source path, process manager, and safe restart command. Do not put secrets in the brain.

## Provider limit preflight and visible progress guardrails

For Claude/Anthropic coding-agent bridges, a durable safety pattern is:

- Before launching the expensive CLI/agent run, make a tiny API probe and inspect `anthropic-ratelimit-unified-*` headers. If `5h-status` is `rejected` or utilization is already at/above the hard threshold, do not start the coding agent; send a clear Telegram message with the reset time/status instead.
- Treat the 5-hour window as the immediate burn-risk window and the 7-day window as weekly quota context. A request can be blocked by the 5-hour window while the 7-day window is still healthy.
- Keep the model appropriate to the job. For an owner-designated coding agent, do not silently downgrade from Opus just because quota was burned; reduce effort, add preflight, enforce max turns/tokens/time, and surface status instead.
- Use machine-readable/streaming output when the CLI supports it (for Claude Code, prefer `stream-json` style output over waiting for one final blob) and convert tool-use/status events into short Telegram progress updates.
- Do **not** claim to show hidden chain-of-thought. If the owner asks to see “what it is thinking,” expose operational reasoning/status instead: accepted task, current check, command/tool being run, blocker found, next action, and final result.
- Truncate or summarize oversized Telegram prompts before sending them to the provider. Preserve the beginning/end and tell the user if the middle was omitted; ask for a file/document workflow for large specs.
- Be careful with “context size” guards: cumulative cache-read/cached-token counters are not the same as the active prompt/context footprint. Do **not** auto-start a new provider session solely because cached-token totals accumulated across turns; that makes the bot look like it lost memory while the real provider quota may still be healthy. If the bridge needs a safety guard, base it on the active session's actual prompt/context footprint or an explicit provider error, and offer manual `/sessions`/`/switch` recovery for old conversations.
- Distinguish real account/provider limits from a local per-response budget. If the CLI/API exits due to `max budget`/`budget exceeded`/local cost cap, tell the user it is a single-answer guardrail and that continuing in the same session is possible. Reserve “Claude Pro/account limit” wording for real rate-limit/account headers or provider rate-limit errors, ideally with reset time.

## PM2 quick checks

```bash
pm2 describe <app> --no-color | awk '/status|pid|restarts|memory/{print}'
pm2 logs <app> --nostream --lines 50 --raw 2>/dev/null \
  | sed -E 's/[A-Za-z0-9_=-]{32,}/[REDACTED]/g' \
  | tail -80
```

If `pm2 jlist`/JSON parsing fails, do not treat it as service failure. Fall back to `pm2 describe` and redacted logs.
