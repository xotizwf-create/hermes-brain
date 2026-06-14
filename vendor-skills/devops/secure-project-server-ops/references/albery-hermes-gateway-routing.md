# Albery Hermes gateway routing notes

Use this note when debugging or reconfiguring the live Albery Telegram bot/gateway. Keep secrets redacted; this file is only for non-secret routing and verification lessons.

## Live server identity pitfall

The live `@albery_ai_bot` Hermes gateway may not be on the newer Andigital host. Prefer the secure project access file for Albery and verify the actual live service before editing:

1. Load project access via `/opt/hermes/secure/projects/albery/.env` or the current secure access map; do not print values.
2. Connect to the host from that secure project file and discover the active systemd Hermes gateway service and Hermes home/profile from the service definition.
3. Verify the bot token belongs to the expected bot with Telegram `getMe` before interpreting logs or changing config. Multiple local profiles/bots can have similar names.
4. If a manual Telegram `getUpdates` call is empty while the bot visibly answered in a group, assume the running gateway may already have consumed the update. Use gateway logs, session/channel-directory files, and `getChat`/`sendMessage` checks instead.

## Group dialog access checklist

For an Albery owner group that should answer without mentioning the bot:

- prove the live token is `@albery_ai_bot` using `getMe`;
- prove the bot can see/send to the group with `getChat` and a harmless `sendMessage`;
- verify both `config.yaml` **and the live `/root/.hermes/.env` overrides**. On Albery, Telegram settings in `.env` can override `config.yaml`, so fixing only `config.yaml` may leave the running gateway using stale `TELEGRAM_ALLOWED_CHATS`, `TELEGRAM_GROUP_ALLOWED_CHATS`, `TELEGRAM_ALLOWED_USERS`, and missing `TELEGRAM_FREE_RESPONSE_CHATS`;
- verify the group/chat is in the allowed chat configuration;
- verify `require_mention` / free-response group listening allows ordinary messages in that group;
- if logs show the owner as unauthorized, check sender-level allowlists as well as group-level access;
- do **not** add ordinary group participants to global `TELEGRAM_ALLOWED_USERS` unless they must be allowed to DM the bot. Global allowed users can message the bot directly in DM;
- distinguish two Albery group access modes before editing: (A) **all members of an allowed group may talk to the bot** — keep only the owner account(s) in `TELEGRAM_ALLOWED_USERS`, put the group ids in `TELEGRAM_ALLOWED_CHATS` + `TELEGRAM_GROUP_ALLOWED_CHATS` + `TELEGRAM_FREE_RESPONSE_CHATS`, and leave `TELEGRAM_GROUP_ALLOWED_USERS` unset/commented; this keeps DM access owner-only while allowing group members through the group gate. (B) **only specific people inside the group may talk** — set `TELEGRAM_GROUP_ALLOWED_USERS` explicitly, but then include every owner Telegram account/id there too because this sender gate can reject the owner even when they are in global `TELEGRAM_ALLOWED_USERS`. Do not mix these modes accidentally;
- verify `platform_toolsets.telegram` is not a tiny custom list such as only `clarify`/`kanban`/`memory`. Use the normal Telegram toolset when the bot must access Albery MCP tools; otherwise the agent can answer text but business tools may fail as `Unknown tool`;
- verify Albery MCP discovery from the same `HERMES_HOME` registers `mcp_albery_*` tools and that `mcp_albery_health` succeeds;
- restart only the Albery Hermes gateway service and verify it stays active after a few seconds;
- finish by asking for a real owner message in the group if Telegram API tests passed but end-to-end human dialog still needs confirmation.

## Reporting

Tell Александр the practical result: which group was authorized, whether replies without `@bot` are enabled, whether notifications remain separate, and what real Telegram/service checks passed. Do not expose token values, full `.env`, SSH details, or internal config dumps.