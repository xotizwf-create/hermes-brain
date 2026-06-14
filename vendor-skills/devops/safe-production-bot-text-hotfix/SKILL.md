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
- Restart only the bot service, not the web app, database, nginx, or the host.
- Prefer exact-match replacement and exact count verification over broad regex edits.
- Always keep a reversible file backup before editing.

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
10. Restart only the Telegram bot service with a bounded timeout.
11. Verify after restart:
   - bot service active/running;
   - main PID changed if restart was expected;
   - recent logs have no new warnings/errors;
   - Telegram API `getMe` succeeds using token loaded inside the server, never printed;
   - web app, nginx, and database remain active.
12. Report the result in human terms: what changed, backup exists, bot/site/db status, and any remaining caveats.

## Pitfalls

- A service can be active but still running old code if it has not restarted since the file edit.
- SSH port open with no banner often means temporary SSH/host load; wait and retry with short timeouts before escalating.
- Grep in shell can produce misleading results with quoting/Unicode; use a small Python exact string count when the result is contradictory.
- Telegram callback timeout errors right before a restart may be stale user callbacks, not necessarily a broken bot. Check for new errors after restart.
