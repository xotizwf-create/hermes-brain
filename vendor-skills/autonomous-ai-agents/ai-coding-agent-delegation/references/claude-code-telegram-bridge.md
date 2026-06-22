# Claude Code Telegram bridge operational notes

Use this when the owner asks to change how a Telegram wrapper around Claude Code behaves (limits, duplicate messages, progress spam, bridge restarts). This is a class-level pattern; project-specific hostnames, paths, secrets, and service names still come from the project brain/secure store.

## Safe workflow

1. Read the project/runbook first for the exact server, checkout path, PM2/systemd service, and secret references.
2. Inspect the last user-facing failure/context before editing. For Telegram bridges this often means reading recent bot logs and the bridge source/config that builds the Claude CLI command.
3. Prefer a tiny, auditable edit:
   - backup the live bridge/config file;
   - patch only the constants/flags/message-send path in scope;
   - leave unrelated dirty files untouched.
4. Validate before restart:
   - syntax check (`node --check`, `python -m py_compile`, etc.);
   - grep/programmatic checks that the intended constants/flags are present/absent.
5. Restart only the affected bridge service and verify it is online plus logs are clean.
6. Report what actually changed and what was verified; mention any unrelated dirty files you deliberately left alone.

## Limit-removal / duplicate-message pattern

For wrappers that stream Claude Code output to Telegram, two common local causes of owner frustration are bridge-side pseudo-limits and partial-message echoing:

- If the bridge has local warning/block thresholds for account usage, do not claim to remove the real upstream Anthropic limit. Raise/disable only the bridge-local thresholds and state that upstream limits can still stop execution.
- If the owner says the bot writes twice or duplicates itself, inspect streaming/partial-output handling. Disable Telegram sends for partial assistant chunks/progress updates and keep only the final assistant/result message.
- If the wrapper passes a partial-streaming flag to Claude (for example a flag that includes partial messages), remove that flag unless the owner explicitly wants live streaming.
- For user-facing Telegram agents, set progress/status message counts to zero or otherwise suppress routine progress spam when the desired behavior is a single final reply.

## Verification probes

Use deterministic checks rather than eyeballing only:

- source contains the new local threshold values;
- source no longer contains the partial-streaming flag;
- source no longer calls the Telegram send helper from the partial-chunk branch;
- syntax check passes;
- process manager reports the bridge online;
- fresh logs have no startup/runtime errors.
