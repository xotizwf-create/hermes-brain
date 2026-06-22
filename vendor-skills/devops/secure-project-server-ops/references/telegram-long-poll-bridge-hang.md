# Telegram long-poll bridge appears online but is silent

Use this when a production Telegram bot/bridge is managed by PM2/systemd and the process is `online`, but user messages are not answered.

## Durable symptom pattern

- Process manager shows the bridge as healthy/online.
- Telegram `getWebhookInfo` shows pending updates (for a long-poll bot this can mean the bot is not advancing its update offset).
- The bridge's local state file/offset does not advance after the user sends test messages.
- Logs may be quiet if the long-poll HTTP request has no timeout or network/JSON parse errors are swallowed.

## Read-only checks

1. Confirm process health, but do not stop there:
   ```bash
   pm2 list
   pm2 logs <name> --lines 80
   ```
2. Check Telegram queue without printing the bot token:
   - read the token from the secure file into a local variable or memory only;
   - call `getWebhookInfo` and inspect `pending_update_count` / `last_error_message`;
   - compare pending update count with the bridge's persisted offset/state file.
3. If safe and needed, call `getUpdates` with the stored offset only to inspect update ids/text metadata; redact private content in the user-facing report.

## Fix pattern

- Add a hard timeout slightly longer than the long-poll timeout (example: Telegram long_poll 50s -> HTTP request timeout ~65s).
- Log Telegram network failures and JSON parse failures; do not let the poll loop fail silently.
- Restart only the affected bridge (`pm2 restart <name>` or the specific systemd service).
- Verify the queue drains, the persisted offset advances, and a fresh user message receives a response.

## Pitfalls

- `online` is not sufficient: a Node/Python process can be alive while its Telegram long-poll request is hung forever.
- Testing a CLI manually can be misleading if the bridge injects auth via environment variables. Reproduce the exact service environment before concluding the provider auth is broken.
- Avoid inline shell snippets that interpolate secrets or JavaScript/Python fragments through multiple shells; use a small local Python/paramiko script or a temporary redacted patch payload instead.
