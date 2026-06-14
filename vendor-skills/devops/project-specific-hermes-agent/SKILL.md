---
name: project-specific-hermes-agent
version: 1.0.0
description: "Create a dedicated Hermes profile-agent for one project with scoped MCP access, role instructions, project skill, repo workspace, and verification."
created_by: agent
---

# Project-specific Hermes agent

Use when Александр wants a named agent for one project or domain, e.g. Темур for Albery, Никита for reminders, Сергей for DevOps.

## Steps

1. Load `hermes-agent` skill first.
2. Inspect current profiles and relevant MCP/tool availability:
   - `hermes profile list`
   - `hermes tools list`
   - `hermes mcp list` or `hermes -p <profile> mcp list`
3. Create a dedicated profile:
   - prefer a short lowercase Latin profile name without spaces;
   - use `hermes profile create <name> --clone --description '<role>'` when the new agent needs existing credentials/MCP config;
   - avoid `--clone-all` unless session/state cloning is explicitly desired.
4. Scope access immediately:
   - in the new profile config, enable only the MCP servers relevant to the role;
   - disable unrelated project MCP servers;
   - set `terminal.cwd` to the agent's project workspace if it will edit code;
   - keep Telegram output quiet if the profile later gets a gateway;
   - after cloning, search the new profile's `memories/` for stale user preferences copied from older agents and patch them immediately when the owner has corrected a preference in the current session.
5. Prepare a safe workspace if the agent edits code:
   - clone the project repo into a dedicated local directory;
   - do not work directly on production;
   - use branches for changes and follow project deployment rules.
6. Write the profile `SOUL.md`:
   - identity and role;
   - sources of truth;
   - allowed/forbidden actions;
   - confirmation rules;
   - self-learning rules: memories for stable facts, skills for procedures, no temporary logs in memory;
   - response style expected by Александр;
   - a distinct agent voice/personality for this role, especially in shared chats;
   - an explicit ban on shared boilerplate openings such as `Готово:` unless the owner reintroduces that format.
7. Add a project-specific skill inside the new profile's skills directory:
   - trigger conditions;
   - startup context;
   - project MCP workflow;
   - code workflow;
   - reporting/automation workflow;
   - self-learning and natural final-answer style without a mandatory `Готово:` prefix;
   - for dispatcher/reminder agents, explicitly document routing rules: which work the agent performs itself, which profile owns each delegated domain, and which MCP/toolsets must stay disabled.
8. If the profile should be a live Telegram bot, provision a dedicated gateway service instead of reusing the main bot:
   - **check the approved secure stores first** (`/root/.hermes/secure/{access-map.yaml,secrets.yaml}` and relevant `/opt/hermes/secure/projects/<slug>/.env` entries) before asking Александр for a BotFather token; if a token exists there, use it without echoing it;
   - validate the token with Telegram `getMe`, but print only `bot_username`/`bot_id`, never the token;
   - write only the needed env/config into the new profile, backing up `.env` and keeping mode `600`;
   - create a separate `hermes-gateway-<profile>.service` with the profile selected explicitly;
   - beware `hermes -p <profile> gateway install` may prompt interactively and not create/start the unit in non-interactive runs; if so, create the systemd unit manually from the known-good profile pattern, then `daemon-reload`, `enable`, `restart`, and verify logs;
   - start/restart that service and keep the default gateway untouched;
   - use BotFather/API setup for name, description, commands, and optional botpic.e needed env/config into the new profile, backing up `.env` and keeping mode `600`;
      - create a separate `hermes-gateway-<profile>.service` with the profile selected explicitly;
      - beware `hermes -p <profile> gateway install` may prompt interactively and not create/start the unit in non-interactive runs; if so, create the systemd unit manually from the known-good profile pattern, then `daemon-reload`, `enable`, `restart`, and verify logs;
      - start/restart that service and keep the default gateway untouched;
      - use BotFather/API setup for name, description, commands, and optional botpic.
9. If multiple project agents share one Telegram group, configure group routing deliberately:
   - keep `TELEGRAM_REQUIRE_MENTION=true` so agents do not answer every group message;
   - keep `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` so `@AgentBot` wakes only that bot;
   - optionally set `TELEGRAM_OBSERVE_UNMENTIONED_GROUP_MESSAGES=true` so allowed group chatter can be stored as context without triggering responses;
   - get the technical group chat id from a command/mention event such as `/start@BotName` or `@BotName ping`, then add that exact id to `TELEGRAM_GROUP_ALLOWED_CHATS` (and `TELEGRAM_ALLOWED_CHATS` when using a response allowlist);
   - ask the owner to disable BotFather → Bot Settings → Group Privacy if the bot must see ordinary unmentioned group messages.
10. When moving or auditing cron jobs for a profile, treat the profile cron store as the source of truth:
   - inspect `hermes -p <profile> cron list --all` and `/root/.hermes/profiles/<profile>/cron/jobs.json`, not just the default `/root/.hermes/cron/jobs.json`;
   - old registration scripts often target the default profile or an obsolete host/path; if a prompt/script exists in the project but the job is absent from the profile cron list, patch the profile cron explicitly or update the registrar before trusting it;
   - set LLM cron jobs with `profile: <profile>` and `workdir: <project workspace>` so future runs load the right profile, MCP scope, and project context;
   - convert user-facing local times to the scheduler's timezone from real system/config state; do not assume local cron is MSK just because the product domain is MSK;
   - for script jobs, Hermes resolves `script` relative to `/root/.hermes/profiles/<profile>/scripts/` when `profile` is set;
   - do not use symlinks from the profile `scripts/` directory to `/root/.hermes/scripts/` — the scheduler resolves the real path and blocks scripts that escape the profile scripts directory;
   - create small real wrapper files inside the profile `scripts/` directory instead, e.g. a `.sh` wrapper with `exec bash /root/.hermes/scripts/name.sh "$@"` or a `.py` wrapper with `runpy.run_path('/root/.hermes/scripts/name.py', run_name='__main__')`;
   - set wrappers executable and verify with `hermes -p <profile> cron run <job_id>` plus the next scheduler tick; final state must show `last_status=ok` and `last_error=None`.
11. Verify:
   - `hermes profile show <name>`;
   - `hermes -p <name> mcp list`;
   - `hermes -p <name> skills list | grep <skill>`;
   - check repo `git status`;
   - run a short `hermes -p <name> chat -Q -q '...'` smoke test to confirm persona;
   - for a live bot, verify both the default gateway and `hermes-gateway-<profile>` are active, inspect recent logs, and send a Telegram test message if the user has already opened the bot;
   - for cron/profile changes, scan every active script job and confirm there are no missing/non-executable script paths and no active jobs with `last_status=error`.
12. When the owner asks whether Codex/OpenAI accounts attached to Hermes still work, audit credential pools across profiles, not only the active profile:
   - start with `hermes auth list` and repeat for relevant profiles with `hermes --profile <profile> auth list`;
   - distinguish `openai-codex` from `copilot` entries; they are separate providers even though both may be "coding accounts";
   - a listing or `auth status` only proves credentials are stored, not that inference works — run a real minimal Codex `/responses` request for each entry;
   - use `scripts/check_codex_pool.py` from this skill as the reusable probe, setting `HERMES_HOME` to the profile home and `CHECK_PROFILE=<name>` for readable output;
   - treat HTTP 200 as working; treat 401 `token_expired` / invalid token as stale and remove only that exact entry by label or id with `hermes --profile <profile> auth remove openai-codex <label-or-id>`;
   - after removal, rerun the probe and `auth list` to verify only working entries remain.
13. Save a compact durable memory with the profile name, workspace, enabled MCP scope, custom skill, service name, and any profile-owned cron wrappers.

## References

- `references/temur-albery-live-agent.md` — concrete implementation notes from turning the Albery/Темур profile into a separate Telegram bot-backed agent, including the recovered full cron schedule.
- `references/telegram-agent-team-groups.md` — group-chat routing pattern for several Hermes Telegram bot profiles in one shared chat.

## Scripts

- `scripts/check_codex_pool.py` — reusable no-token-leak smoke test for every `openai-codex` credential in a chosen Hermes profile; use before deleting stale Codex entries.

## Pitfalls

- For an existing project Telegram agent where notifications/approvals must go to a separate group instead of the owner DM: first verify the bot is a member of that group with Telegram `getChat`; set `TELEGRAM_HOME_CHANNEL` and `TELEGRAM_APPROVALS_CHANNEL` to the group chat id, add `TELEGRAM_ALLOWED_CHATS`/`TELEGRAM_GROUP_ALLOWED_CHATS`, require mentions in groups, change cron jobs from hard-coded `telegram:<owner_id>` to bare `telegram`, restart only that profile's gateway, and verify cron delivery resolution plus service health. If `getChat` says `chat not found`, the owner must add the bot to the group before deliveries will succeed; bots cannot add themselves.
- Do not leave unrelated MCP servers enabled after cloning a profile.
- Do not leave stale cloned memories in a new profile after the owner corrects a preference; patch the same correction into every profile that will answer the owner, not only the current default profile.
- Do not let a cloned Telegram profile inherit and use the source bot token; that makes two agents speak as the same bot and breaks group routing.
- Do not print secret-bearing MCP URLs, bot tokens, OAuth access/refresh tokens, or token-like env values in user-facing messages.
- When auditing Codex accounts, do not rely on `hermes auth status` alone and do not delete by index until after the final `auth list` ordering is known; run a real per-entry probe, then delete by exact label/id where possible. Codex `/responses` health checks need `instructions` and `stream: true`, and may reject generic Responses parameters such as `max_output_tokens`; a 400 about request shape is not evidence that the account is dead.
- Do not edit another profile's files unless Александр explicitly asked to create/modify that agent.
- Do not mutate Hermes Brain silently; follow the brain approval-gated diff workflow unless the owner explicitly authorizes the change.
- A new profile's config/gateway changes usually require starting that profile's own session/gateway to take effect.
- Telegram bots cannot initiate a private chat with a user; ask the user to open the bot and press `/start` before treating a failed first outbound test as a gateway problem.
- In Telegram groups, a normal message may not appear in `getUpdates` or Hermes logs while BotFather Group Privacy is enabled; use an explicit `@bot` mention or `/command@bot` to discover the chat id, then disable privacy only if the workflow needs passive group context.
- Never enable free-response behavior for several bots in the same group without mention routing; otherwise multiple agents may answer the same message.
- When starting long-lived gateways from the terminal, use the process/service manager or Hermes background mode; do not use shell `&` backgrounding in foreground commands.
