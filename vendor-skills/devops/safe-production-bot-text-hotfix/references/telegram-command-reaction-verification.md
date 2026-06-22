# Telegram command reaction verification

Use this note when a hotfix changes Telegram bot command handling, reactions/likes, or progress acknowledgements.

## Why
Telegram bots often handle slash commands in early-return branches (`/new`, `/help`, `/session`, etc.) while ordinary messages flow through a different handler. A fix that adds a reaction/👍 to normal replies can still miss command replies if command branches return before the shared finalization code.

## Verification pattern
1. Search for all command branches and early `return send...` calls.
2. Ensure the same completion helper/reaction path runs before every successful command return, or centralize it in a helper such as `sendDone(...)`.
3. Verify mechanically:
   - helper is defined once;
   - every command success path calls it or otherwise reacts;
   - obsolete preflight/limit text is absent if the desired UX is reaction-only progress;
   - no duplicate user-visible acknowledgements remain.
4. Restart the actual bot supervisor (`pm2`, `systemd`, Docker, etc.) and check recent logs.
5. If possible, test at least one slash command and one normal text request from the real Telegram chat.

## UX rule learned
For owner-facing command actions, prefer: immediate lightweight reaction/typing signal -> one final result -> 👍/completion reaction. Avoid sending both an "accepted/checking" text and the actual answer unless the owner explicitly asked for progress text.
