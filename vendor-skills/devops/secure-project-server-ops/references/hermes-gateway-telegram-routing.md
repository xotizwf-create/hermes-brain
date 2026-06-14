# Hermes Gateway Telegram routing on project servers

Use this reference when the owner asks to make a project-specific Hermes bot behave like the main assistant: normal conversation in one Telegram chat, while operational notifications, approvals, cron outputs, and service-control prompts go to a dedicated notifications chat/topic.

## Scope

This is production server work. Apply the server preflight first, then make only light config edits and restart only the Hermes gateway service that owns the bot.

## Discovery without leaking secrets

1. Resolve the target server and Hermes home from project docs or the secure access map.
2. Resolve credentials from the secure store; if docs mention a gitignored `.env`, inspect candidate files for key names only and never print values.
3. If SSH credentials are not present, stop and ask for the credential location or for the owner to place them in the secure store. Do not guess passwords or continue by describing unverified changes.
4. On the server, read-only discovery first:
   - resource preflight (`free`, `swapon`, load, disk)
   - running services matching `hermes`, `gateway`, project slug, bot/app names
   - active Hermes home/profile used by the systemd service
   - current Telegram config keys, redacted: `allowed_chats`, `group_allowed_chats`, `home channel`, `dm_topics`, `gateway_restart_notification`, `display.platforms.telegram`, `approvals`

## Config migration checklist

Before editing, copy the active config to a timestamped backup next to the original and record the service name for rollback.

For a split-chat notification model, verify and set the project agent's config to the same logical shape as the main assistant:

- Conversation routing:
  - the normal chat/group remains authorized for direct conversation if needed;
  - the notifications chat/group or topic is authorized and used as the delivery target for unattended outputs.
- Telegram noise control:
  - `display.platforms.telegram.tool_progress: false`
  - `display.platforms.telegram.busy_ack_detail: false`
  - `telegram.gateway_restart_notification: false` unless the owner explicitly wants restart pings.
- Background/system outputs:
  - keep long-running/background process notifications enabled only at the useful level for the owner;
  - route cron/watchdog deliveries explicitly to the notifications chat when jobs are meant to notify the owner.
- Approvals and control prompts:
  - if approvals are enabled for the project agent, test that inline buttons appear in the notifications destination and callback authorization still works;
  - do not move destructive-action approvals into an unmonitored chat.
- Human-facing prompt:
  - ensure the agent is instructed to keep owner messages human-readable in Russian, without raw command names, tool IDs, paths, or stack traces unless explicitly asked.

## Verification

After restart, verify all of these with real output, not assumptions:

1. `systemctl is-active <hermes-service>` returns active.
2. Gateway logs show Telegram connected and no token/polling conflict.
3. A normal message in the conversation chat gets a normal answer.
4. A safe notification path reaches the notifications chat/topic (for example a harmless cron dry-run or a non-destructive background notification test).
5. If approvals are enabled, trigger a safe approval prompt and confirm the button resolves the waiting action.
6. If any test fails, restore the config backup and restart only the same gateway service.

### Telegram chat-ID and delivery pitfalls

- Do not treat a configured `TELEGRAM_HOME_CHANNEL` / `TELEGRAM_APPROVALS_CHANNEL` as proof that the bot can send there. Before making cron deliveries explicit, verify the destination with the active bot token using `getChat` and a harmless `sendMessage` test. If Telegram returns `chat not found`, the bot is not in that chat or the ID is stale/wrong.
- If the owner says they mentioned the bot in a chat but `getUpdates` is empty, check whether you are using the same bot token as the live gateway. A project may have multiple similarly named bots/profiles; use `getMe` on the active token and inspect the live `.env`/systemd home, not a local profile copy. Also remember that a running Hermes gateway may consume updates before your manual `getUpdates` call sees them; in that case use gateway logs/session files/channel directory instead of concluding the chat did not send anything.
- A newly created Telegram group may be invisible to Hermes even when the bot has permission to write: if `allowed_chats` is non-empty and contains only an old/dead group ID, Hermes can silently discard the new group's messages before it records a session. Check `telegram.guest_mode` together with `telegram.require_mention`: setting `guest_mode: true` while keeping `require_mention: true` is a safe discovery bridge, because the bot can answer direct `@bot` mentions from non-allowlisted groups without listening to the entire chat. After the new group answers, read the fresh channel/session entry and pin the real chat ID for notifications.
- Authorization can be two-level: the group/chat must be allowed, and in some configs the sender may also need to be allowed unless group-level authorization grants access to all participants. When logs show `unauthorized` for a real owner message inside an otherwise valid group, add or verify the sender ID in the appropriate allowlist (or confirm the group-level access rule is active), then restart only the gateway and retest a normal message without `@bot`.
- When diagnosing a silent Telegram group, do not stop at BotFather permissions. Verify, in order: `getMe` on the live token (`username`, `can_join_groups`, `can_read_all_group_messages`), `getWebhookInfo`/polling mode, `getChat` for every configured chat ID, `channel_directory.json` / gateway sessions for the new chat, and recent gateway logs. `getChat` returning `chat not found` for the configured group ID means that ID is stale or the live bot is not in that chat.
- If a test send fails after you changed cron jobs from `deliver: telegram` to `deliver: telegram:<chat_id>`, do not leave scheduled jobs pinned to the unreachable chat. Revert those explicit delivery targets to the previous safe value (usually `telegram`) or restore the cron backup, then retry only after the correct chat ID is proven.
- Secure project `.env` files can contain a legacy host IP while project docs name a newer production host. Test credentials against the host from the secret file and the documented host separately, and report which one actually accepts the credentials without printing values. Do not assume the docs or the `.env` are fresher.
- When using `sshpass`, ensure the password is actually passed in the subprocess environment (`SSHPASS=...` or `env={'SSHPASS': ...}`); setting a Python variable named `password` is not enough. A missing env var can look like an incorrect password.

## Reporting to the owner

Report in practical terms: which chat now handles dialog, which chat handles notifications/approvals, that the service is active, and what verification messages were observed. Do not paste bot tokens, chat secrets, full config, or credentials.