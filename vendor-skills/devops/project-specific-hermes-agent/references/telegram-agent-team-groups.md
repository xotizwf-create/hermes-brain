# Telegram group routing for a team of Hermes bot profiles

Use this reference when several named Hermes profiles (for example the default assistant plus a project agent such as Темур) are added to the same Telegram group.

## Goal

- Bots can answer in the group and remain usable in DMs.
- A message addressed to one bot wakes only that bot.
- For Александр's AI-team group, bots should also wake on profile-specific keywords without `@` (for example: `Некит, привет` → Никита; `что по Albery/Албери` → Темур), while ordinary group chatter still does not wake every agent.
- Ordinary group chatter can optionally be saved as context, but should not trigger every agent unless it matches that agent's keyword patterns.
- Access stays limited to the intended group and/or operator.

## Recommended env/config knobs per profile

Set these in each profile's `.env` or equivalent Telegram platform config, then restart that profile's gateway:

```env
TELEGRAM_REQUIRE_MENTION=true
TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true
TELEGRAM_OBSERVE_UNMENTIONED_GROUP_MESSAGES=true
# Optional per-agent wake words. Prefer config.yaml telegram.mention_patterns for profiles.
# TELEGRAM_MENTION_PATTERNS='["(?iu)(^|[^\\w])албери([^\\w]|$)"]'
```

After the technical group id is known, add it explicitly:

```env
TELEGRAM_GROUP_ALLOWED_CHATS=-1001234567890
# If a response allowlist is configured, include the same id there too:
TELEGRAM_ALLOWED_CHATS=-1001234567890
```

Keep user allowlists (`TELEGRAM_ALLOWED_USERS`, `TELEGRAM_GROUP_ALLOWED_USERS`) as appropriate for the owner/operator. Do not use broad allow-all settings unless the owner explicitly wants an open bot.

## Discovering the Telegram group chat id

A Telegram invite link is not enough: Bot API `getChat` normally cannot resolve private invite links such as `t.me/+...`.

Use one of these in the target group:

- `/start@ExactBotUsername`
- `@ExactBotUsername ping`
- reply to a previous bot message

Then read the update/logs for `chat.id` and `chat.type`. If no event appears, check BotFather Group Privacy.

## BotFather Group Privacy

Telegram bots in groups usually receive only commands, direct mentions, replies to themselves, and service events while privacy mode is enabled. They will not see ordinary messages like "Некит, привет" or "Что у нас по албери".

For keyword routing in Александр's AI-team group, turn Group Privacy off for every profile bot that should react to unmentioned keywords:

1. Open BotFather.
2. `/mybots`.
3. Select the bot.
4. `Bot Settings` → `Group Privacy` → `Turn off`.
5. Send an ordinary keyword message again and verify logs.

Keep `TELEGRAM_REQUIRE_MENTION=true` after disabling privacy: Hermes will observe the group but dispatch only on direct @mentions/replies or that profile's `telegram.mention_patterns` keyword regexes.

## Keyword wake-pattern template

Prefer `config.yaml` under the top-level `telegram:` block (not `gateway.telegram`) for each profile:

```yaml
telegram:
  require_mention: true
  exclusive_bot_mentions: true
  observe_unmentioned_group_messages: true
  group_allowed_chats: '-5120862157'
  allowed_chats: '-5120862157'
  mention_patterns:
    - (?iu)(^|[^\w])(темур|тимур)([^\w]|$)
    - (?iu)(^|[^\w])(albery|албери)([^\w]|$)
```

Use narrow domain words. Avoid broad temporal triggers like `сегодня` / `завтра` for a reminder agent because they wake the bot in unrelated project questions such as `что по Албери сегодня`. Validate with a small regex routing test before restart: each sample phrase should wake only the intended profile, and ordinary chatter like `сегодня как дела` should wake nobody.

Current AI-team pattern examples:

- Никита: `некит`, `никита`, `napomni/напомни`, `напоминалка`, `дедлайн`, `срок`, `расписание`, `календарь`.
- Темур: `темур/тимур`, `albery/албери`, `bitrix/битрикс`, `zoom/зум`, `созвон`, `отчёт`, `руководители`.
- Default orchestrator: `ассистент`, `оркестратор`, `агент/агенты`, `команда агентов`, `создай/сделай/настрой/подними ... агент/бот`, `hermes/хермес`.

## Human group-chat behavior

For every project-agent profile, add an explicit group-chat tone rule in `SOUL.md` and any profile skill:

- Treat greetings, `пинг`, `тест`, and simple presence checks as human conversation, not completed work.
- Do not start any team-agent replies with the template `Готово:`. Each agent should answer naturally in its own voice; for completed work use human wording such as «Сделал», «Проверил», «Разобрал» or go straight to the result.
- If the owner corrects a team-wide communication preference (for example no `Готово:` or no artificial time limit for ordinary tasks), update that preference in the default profile and in every live agent profile that can answer the owner; cloned `memories/USER.md` files often keep stale copies.
- If several bots are mentioned together, treat it as an address to the team; do not scold the user for mentioning another bot.
- Each agent should briefly state its role and stay in its lane.
- The orchestrator should coordinate; project agents should answer only for their domain.
- Avoid duplicate replies: if another agent already covered the substance, add only routing/next-step value or stay quiet.

Example Temur greeting: `Привет, Александр, Темур на связи. Я по Albery — отчёты, Zoom, Bitrix, инструкции и код проекта.`

Example orchestrator greeting: `Привет, Александр, я на связи. Темур тоже здесь по Albery — можешь писать нам прямо в этот чат.`

## Verification checklist

- `getMe` shows the expected username for each token/profile, and token values are never printed.
- Before asking the owner for a token, check approved secure stores and project `.env` files for the named bot entry; report only whether it exists and the `getMe` username/id.
- Each profile has its own gateway service/process; restarting one does not stop the other.
- If `hermes -p <profile> gateway install` stops at an interactive prompt, create a dedicated `hermes-gateway-<profile>.service` manually from the known-good service pattern and verify `systemctl is-active` plus profile `logs/gateway.log`.
- `getChatMember` for the shared group confirms the bot is a member; Telegram `Bad Request: chat not found` usually means the bot has not been added to the group or has not seen it yet, not that the token is invalid.
- `TELEGRAM_REQUIRE_MENTION=true` and `TELEGRAM_EXCLUSIVE_BOT_MENTIONS=true` are present in both profiles.
- A message `@TemurBot ...` is processed only by the Temur profile.
- A message `@MainAssistantBot ...` is processed only by the default assistant.
- A greeting that mentions both bots gets short human replies in each agent's own voice, not task-completion boilerplate.
- Ordinary messages are either ignored or only observed, according to the configured privacy/observe mode.
- Group id allowlists contain the exact negative chat id for the shared group, not the invite link.

## Pitfalls

- Do not configure several bots with free-response in the same group unless you intentionally want multiple replies.
- Do not print bot tokens while inspecting `.env`; show token-bearing variables as `[REDACTED]`.
- A lack of `getUpdates` results after a normal group message is usually privacy mode, not a broken gateway.
- Telegram may consume updates through the running gateway before a manual `getUpdates` check sees them; logs are often the better source once the gateway is active.
