# Темур / Albery live Telegram agent notes

Use as a concrete example when creating a project-specific Hermes profile that is also a live Telegram bot.

## Shape that worked

- Dedicated Hermes profile: `temuralbery`
- Dedicated project workspace: `/root/projects/albery`
- Dedicated Telegram bot: `@TemurZ_bot`
- Dedicated systemd gateway service: `hermes-gateway-temuralbery`
- Scope: only the Albery MCP/tools enabled; unrelated MCP servers disabled
- Profile-local role/instructions: `SOUL.md`
- Profile-local project skill: `albery-temur-agent`

## Implementation pattern

1. Load the Hermes configuration skill and inspect the current profile/tooling.
2. Clone/create a named profile for the role.
3. Copy only the needed secret values into the profile environment/config. Never print token values; inspect names/presence only.
4. Restrict the profile config to the domain-specific MCP server(s).
5. Create role instructions and a profile-local skill so the agent knows its identity, allowed actions, and confirmation rules.
6. Smoke-test with `hermes -p <profile> chat -Q -q '<short identity/status prompt>'`.
7. Start a separate gateway service for that profile; do not disturb the default Telegram gateway.
8. Verify both services are active and inspect recent logs.
9. Configure BotFather-visible metadata: name, description, commands, and optional avatar.
10. Ask the user to open the bot and press `/start`; Telegram blocks first outbound private messages from a bot until then.

## Verification checklist

- `hermes profile show <profile>` reports the expected profile.
- `hermes -p <profile> mcp list` shows only intended MCP access.
- `hermes -p <profile> skills list` includes the profile-local project skill.
- `systemctl status hermes-gateway-<profile>` is active.
- Default gateway remains active.
- Telegram test either succeeds or returns the expected `/start` requirement.

## Cron audit and recovered Albery schedule

When auditing whether Темур has the “full” Albery automation set, check the profile cron store, not the default one:

- Source of truth: `hermes -p temuralbery cron list --all` and `/root/.hermes/profiles/temuralbery/cron/jobs.json`.
- A project script or prompt existing under `/root/projects/albery/scripts/` does not mean the profile cron job exists.
- Old registrar scripts may target `/root/.hermes/cron/jobs.json` or an obsolete host; inspect their target path before running them.
- LLM jobs should carry `profile: temuralbery` and `workdir: /root/projects/albery`.
- If scheduler times are UTC, convert MSK → UTC by subtracting 3 hours.

Recovered full set:

- `zoom-to-tasks`: `*/5 * * * *`, no-agent script watchdog, Telegram delivery.
- `owner-daily`: 18:00 МСК daily except Friday → `0 15 * * 0-4,6`, prompt `scripts/hermes_owner_daily_prompt.txt`.
- `owner-weekly`: Friday 18:00 МСК → `0 15 * * 5`, prompt `scripts/hermes_owner_weekly_prompt.txt`.
- `leader-evaluations-digest`: Wednesday 19:00 МСК → `0 16 * * 3`, prompt `scripts/hermes_leader_digest_prompt.txt`.

## Pitfalls from the session

- Do not use shell `&` to background a long-lived gateway from a foreground terminal command; use systemd or Hermes background process tracking.
- Treat Telegram `/start` gating as normal product behavior, not as a broken bot.
- Avatar/image generation can be optional; if unavailable due to provider credentials, continue with the agent setup and report the avatar as optional follow-up.
