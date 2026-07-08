# LLM bot auth vs limit-probe diagnostics

Use when a Telegram bot wraps an LLM CLI/provider and a command such as `/account`, `/limits`, or `/usage` returns an auth-looking error while normal prompts may still work.

## Lesson

Do not conclude “the bot is disconnected from Telegram” or “the model is down” from a single diagnostic command. Limit/account commands often call a different endpoint or use different headers than the normal inference path.

Example pattern observed with a Claude Code Telegram bridge:

- `/account` called Anthropic `/v1/messages` directly to read rate-limit headers.
- The direct OAuth probe returned `401 Invalid authentication credentials`.
- The same token still worked through the official `claude` CLI (`claude -p ...` returned `OK`).
- Telegram `getMe` succeeded and the PM2 bot process stayed online.
- Correct fix was to change the `/account` user-facing message to explain that only the limit probe is unavailable, not to rotate secrets or claim Claude/Telegram is disconnected.

## Triage sequence

1. Verify the bot process/supervisor is alive (`pm2 list`, `systemctl status`, Docker, etc.).
2. Verify Telegram connectivity with `getMe`, loading the bot token server-side and never printing it.
3. Verify the normal model path through the same executable the bot uses, e.g. `CLAUDE_CODE_OAUTH_TOKEN=$(cat secure-token-file) claude -p '...' --output-format text`.
4. Separately probe the diagnostic/account/limit endpoint and record only status/type, redacting tokens and response IDs if needed.
5. If normal prompts work but the diagnostic probe fails, patch the diagnostic command UX: say “limit status unavailable” and tell the user to test a normal prompt. Do not present the diagnostic failure as model outage.
6. Restart only the affected bot process and verify fresh logs after restart.

## Secret handling

- Never print OAuth tokens, Telegram bot tokens, API keys, or full `.env` contents.
- When showing commands in a report, replace token values with `[REDACTED]` or describe “token loaded from secure file”.
- If credentials truly need rotation, ask for/perform the rotation explicitly; do not rotate as a reflex when the official CLI path still works.
