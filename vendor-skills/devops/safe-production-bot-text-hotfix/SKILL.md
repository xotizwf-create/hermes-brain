---
name: safe-production-bot-text-hotfix
description: Safely apply a small text-only hotfix to a production Telegram bot without disturbing the web app or database.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [production, telegram-bot, hotfix, systemd, safety]
---

# Safe Production Bot Text Hotfix

Use this when applying a small text-only change to a production Telegram bot and the user asks to be maximally careful.

## Rules

- Never print secrets, tokens, passwords, connection strings, or environment file contents.
- Do not restart the whole server unless the service is unreachable and no softer control path exists.
- Restart only the bot service, not the web app, database, nginx, or the host. The service may be `systemd`, `pm2`, Docker, or another supervisor — identify the actual supervisor before restart.
- Prefer exact-match replacement and exact count verification over broad regex edits.
- Always keep a reversible file backup before editing.
- For Telegram command UX changes, verify the exact command path separately from the normal text-message path: slash commands often return early and can bypass reactions/likes, typing indicators, or final acknowledgements.
- For LLM wrapper bots, distinguish diagnostic/account/limit commands from the normal model path. A `/account` or `/limits` 401 can be a broken limit probe while the official CLI/inference path still works; verify both before saying the bot/model is disconnected.
- Do not send two user-visible acknowledgements for one action. Prefer one lightweight reaction/typing signal while work runs, then one final result message; remove redundant "accepted/checking" text unless the owner explicitly wants it.

## Workflow

1. Identify the target host and credentials from the approved secure store.
2. Verify external availability first:
   - public site responds;
   - SSH banner or management channel responds;
   - distinguish full host outage from only SSH slowness.
3. Connect with short timeouts and no secret values in command arguments.
4. Gather baseline state:
   - active services;
   - bot process/service name;
   - current resource pressure;
   - recent bot logs;
   - public site/API status.
5. Locate the exact file and exact text occurrences.
6. Create a timestamped backup beside the edited file.
7. Replace only the exact old text with the exact new text.
8. Verify:
   - old exact text count is zero;
   - new exact text count equals expected count;
   - backup exists;
   - git status shows only the intended change if the tree is a git repo.
9. Check whether the live bot process started before the edit. If yes, a restart is required for code loaded in memory.
10. Restart only the Telegram bot service with a bounded timeout. Use the actual supervisor (`systemctl restart`, `pm2 restart`, `docker compose restart`, etc.), not a generic host restart.
11. Verify after restart:
   - bot service active/running;
   - main PID/restart count changed if restart was expected;
   - recent logs have no new warnings/errors;
   - Telegram API `getMe` succeeds using token loaded inside the server, never printed;
   - command handlers and normal message handlers both show the intended UX (e.g. reaction/👍 appears where expected, no duplicate "accepted" message);
   - web app, nginx, and database remain active only if they are part of the affected deployment and checking them is in scope.
12. Report the result in human terms: what changed, backup exists, bot status, and any remaining caveats.

## Pitfalls

- A service can be active but still running old code if it has not restarted since the file edit.
- SSH port open with no banner often means temporary SSH/host load; wait and retry with short timeouts before escalating.
- Grep in shell can produce misleading results with quoting/Unicode; use a small Python exact string count when the result is contradictory.
- Telegram callback timeout errors right before a restart may be stale user callbacks, not necessarily a broken bot. Check for new errors after restart.
- In LLM bots, an account/limit diagnostic can fail independently of the normal response path; see `references/llm-bot-auth-vs-limit-probes.md` before rotating credentials or reporting an outage.
- For slash-command reaction/like fixes, see `references/telegram-command-reaction-verification.md`.
