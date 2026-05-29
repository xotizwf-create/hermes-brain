---
name: reminders-and-watchers
description: Use when the user wants one-off or recurring reminders, or a periodic watcher (e.g. "remind me tomorrow 18:00 to text Dasha", "every day at 10:00 remind me to send the archive", "check my mail every 2 hours and tell me only the important non-newsletter stuff"). Implemented with Hermes' built-in cron scheduler, delivering to Telegram.
---

# Skill: reminders-and-watchers

Hermes runs 24/7 on prod with a built-in cron scheduler (`hermes cron`) and delivers to the owner's
Telegram. Reminders and watchers are just cron jobs. Run these on the server (the agent already runs
there; from a workstation use the `_deploy_helper.py new "<cmd>"` transport).

## The one command
```
hermes cron create <schedule> "<prompt>" [--name N] [--deliver telegram] [--repeat K] \
                   [--skill S] [--script F --no-agent] [--workdir DIR]
```
- **schedule**: relative `30m` / `every 2h`, or cron `M H * * *`. **The prod server is on UTC**
  (verified 2026-05-30), so a Moscow time = UTC−3 in the cron: "18:00 МСК" → `0 15 * * *`,
  "10:00 МСК" → `0 7 * * *`. Always confirm the user means Moscow time, then convert.
- **--deliver telegram**: send the result to the owner's Telegram chat (default target). Use
  `platform:chat_id` for a specific chat.
- **--repeat 1**: fire once then stop (one-shot reminder).
- **--skill / --script --no-agent**: give the job tools, or run a pure script watchdog.

## Delivery format — clean, no technical text
`cron.wrap_response: false` is set in `config.yaml`, so deliveries are the agent's raw output only
(no `Cronjob Response`/`job_id`/management footer). Write reminder prompts so the agent replies with
**just**: an emoji header, blank line, the point — nothing else. E.g. the prompt:
`Ответь ровно так и ничего больше: "⏰ Напоминание\n\nПора почистить зубы".`
Watchers: header optional; on nothing-to-report return `[SILENT]`.

## One-shot reminder — "напомни завтра в 18:00 написать Даше"
Compute tomorrow's date; fire once:
```
hermes cron create "0 18 30 5 *" "Напомни владельцу: написать Даше." \
  --name remind-dasha --deliver telegram --repeat 1
```
(`M H DOM MON *` pins an exact date; `--repeat 1` removes it after firing. For "через 2 часа" just
use `2h --repeat 1`.)

## Recurring reminder — "каждый день в 10:00 напоминай скинуть архив"
```
hermes cron create "0 10 * * *" "Напомни владельцу: нужно скинуть архив." \
  --name daily-archive --deliver telegram
```
Weekly example: `"0 10 * * 1"` (Mondays). Monthly: `"0 10 1 * *"` (1st of month).

## Watcher — "смотри мою почту каждые 2 часа, говори только про важное (не рассылки)"
Mail backend = Hermes built-in **`himalaya`** skill (IMAP). One-time prereq: configure himalaya with
the Gmail account + an **App Password** (Gmail → Security → App passwords; IMAP enabled). Store it in
the server secure store, never in the brain.
```
hermes cron create "every 2h" \
  "Через himalaya проверь новые письма Gmail с момента прошлой проверки. \
   Покажи ТОЛЬКО важные личные/рабочие письма: отправитель-человек, адресовано мне, требует ответа \
   или действия. ОТФИЛЬТРУЙ рассылки, промо, уведомления сервисов, соцсети, автоматические письма. \
   Формат: '✉️ <отправитель> — <тема> — <1 строка сути>'. Если важного нет — ответь пустой строкой \
   (ничего не присылай)." \
  --name mail-watch --deliver telegram --skill himalaya
```
- Empty / `[SILENT]` output = no delivery (verified: the scheduler logs `agent returned [SILENT] —
  skipping delivery`). Always tell a watcher to return `[SILENT]` when nothing is relevant, else spam.
- Same pattern works for other watchers (calendar, a URL, CI) — swap the skill/prompt.

### Deployed mail watcher (2026-05-30, live)
- `himalaya` v1.2.0 at `/usr/local/bin/himalaya`; config `/root/.config/himalaya/config.toml`
  (account `gmail`, IMAP `imap.gmail.com:993` tls, SMTP `smtp.gmail.com:465`).
- App Password stored at `/root/.hermes/secure/gmail_app_password` (600 root:root), referenced from
  the config via `backend.auth.cmd = "cat /root/.hermes/secure/gmail_app_password"` — **no secret in
  the config or the brain**. Gmail App Passwords: create at myaccount.google.com/apppasswords, store
  without spaces.
- Cron `mail-watch` (`every 2h`, `--skill himalaya`, `--deliver telegram`) reads INBOX, filters
  important non-newsletter human mail, dedupes via `memory`, returns `[SILENT]` when nothing matters.
  Smoke-tested with `hermes cron run <id>`: 5 tool turns, returned `[SILENT]`, no spam.

## ChatGPT subscription watcher + auto-disable (deployed 2026-05-30)
Warns before a ChatGPT/Codex account subscription expires AND auto-removes the account the day after
it expires. Subscription end-dates aren't in the OAuth tokens → kept manually in a registry.
- Registry: `/root/.hermes/chatgpt_accounts.json` (server, not in git) — `{lead_days, accounts:[{label,
  auth_id, expires:"YYYY-MM-DD", removed, note}]}`. `auth_id` = id from `hermes auth list`. Update a
  date from chat by editing this file (terminal tool); when a new account is bought, add it + set the
  old one's date.
- Script: `/root/.hermes/scripts/chatgpt_sub_watch.py` (no LLM). Per account (MSK days left):
  `>0 ≤lead_days` → 🟠 warn; `=0` → 🔴 «заканчивается сегодня»; `<0` (expired) → run
  `hermes auth remove openai-codex <auth_id>`, mark `removed`, report 🔴 «аккаунт ОТКЛЮЧЁН». Guard:
  never removes the **last alive** account (instead screams to add a new one). Empty output = silent.
- Cron `chatgpt-sub-watch`: `0 7 * * *` (10:00 МСК), `--script chatgpt_sub_watch.py --no-agent
  --deliver telegram`. Accounts pool: `hermes auth list`.

## Manage
```
hermes cron list                 # all jobs + ids
hermes cron run <id>             # run on next tick (test it now)
hermes cron edit <id> --prompt "..."   # change the instruction/schedule
hermes cron pause/resume <id>
hermes cron remove <id>
```
Always `hermes cron run <id>` once after creating, to confirm it fires and delivers to Telegram.

## Rules
- Confirm exact time + timezone with the user before creating a dated reminder.
- Watchers must define a "stay silent when nothing relevant" rule, or they become noise.
- Secrets (App Password, IMAP creds) live only in `/root/.hermes/secure/`, never in the cron prompt
  or the brain. See `secure-access`.
