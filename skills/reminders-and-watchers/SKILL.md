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
- **schedule**: relative `30m` / `every 2h`, cron `M H * * *`, or an explicit ISO timestamp.
  **All user times without a timezone are Moscow time (Europe/Moscow)**. For one-shot reminders,
  prefer an explicit timestamp with offset, e.g. `2026-05-31T15:00:00+03:00`, never a naive
  timestamp. Cron expressions are evaluated by the scheduler/server timezone, so if a cron expression
  is necessary, convert from МСК deliberately and verify the resulting `next_run_at` before confirming.
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

## Reliability rules for reminders

1. **Default timezone = Moscow**. If Александр says "в 15:00" without a timezone, treat it as
   `15:00 Europe/Moscow`; do not ask again unless the date itself is ambiguous.
2. **One-shot reminders use explicit timezone timestamps** whenever possible:
   `YYYY-MM-DDTHH:MM:SS+03:00`. This prevents UTC/МСК shifts.
3. **After creating a reminder, verify the actual scheduled time**: inspect the created job's
   `next_run_at`, convert it to Moscow time, and confirm it equals the requested time.
4. **If verification fails**, remove the bad job immediately and recreate it correctly.
5. **Keep confirmations short**: `Поставил на 15:00 МСК` or `Поставил на завтра, 18:00 МСК`.
   Do not show job ids, UTC, commands, paths or scheduler internals.
6. **Active reminders list**: run `/root/.hermes/scripts/reminder_audit.py --list` and summarize in
   Russian. If empty, say `Активных напоминаний нет`.
7. **Missed-reminder check**: script-only cron job `reminder-audit` runs every 15 minutes. It stays
   silent when all is OK and sends a short Russian alert only if an active reminder is overdue,
   failed, or not delivered.

## One-shot reminder — "напомни завтра в 18:00 написать Даше"
Compute tomorrow's date in Europe/Moscow; fire once with an explicit Moscow offset:
```
hermes cron create "2026-05-31T18:00:00+03:00" "Ответь ровно так и ничего больше: \"⏰ Напоминание\n\nНаписать Даше\"." \
  --name remind-dasha --deliver telegram --repeat 1
```
Then verify the created job's `next_run_at` equals 18:00 МСК. For "через 2 часа" use `2h --repeat 1`
and still check the computed next run.

## Recurring reminder — "каждый день в 10:00 напоминай скинуть архив"
For recurring cron schedules, convert the user-facing Moscow time to the scheduler/server timezone and verify the first `next_run_at`. If the server is UTC, 10:00 МСК = 07:00 UTC:
```
hermes cron create "0 7 * * *" "Ответь ровно так и ничего больше: \"⏰ Напоминание\n\nНужно скинуть архив\"." \
  --name daily-archive --deliver telegram
```
After creation, confirm to the user only in Moscow time: `Поставил ежедневно на 10:00 МСК`.
Weekly example for Monday 10:00 МСК on a UTC server: `"0 7 * * 1"`. Monthly example for the 1st day 10:00 МСК: `"0 7 1 * *"`.

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

### ChatGPT/Codex account pool — checking active vs limited account
Use this when Александр asks which ChatGPT/Codex account Hermes is using, whether it switched after a
limit, or whether the active account is the one with email / without email.

1. Check the pool state with `hermes auth list openai-codex` (or `hermes auth list` if provider is
   unclear). **Never paste raw emails, token values, refresh tokens or auth files into chat.** It is OK
   to say human labels only: "аккаунт с почтой" / "аккаунт без почты" / "первый доступ" / "второй
   доступ".
2. Interpret markers:
   - `←` = currently selected/active pool entry.
   - `rate-limited`, `usage_limit_reached`, `429`, `exhausted` = this entry is temporarily limited.
   - A remaining time like `2h left` is the expected cooldown; convert it to МСК before telling the
     owner.
3. Hermes itself rotates pool entries on provider failures: for usage-limit errors it marks the
   current entry exhausted and switches to the next usable entry. For ordinary rate limits it may retry
   once, then rotate on the next failure. So if the emailed account shows limited and the no-email
   account has `←`, explain: "переключились на аккаунт без почты, потому что почтовый сейчас на лимите".
4. If the owner asks "ты только что переключился?", answer from the current pool state plus timestamps
   if available; do not claim an exact switch moment unless logs show it. Safe wording: "по текущему
   состоянию активен X, Y на лимите до примерно HH:MM МСК".
5. If all entries are exhausted, tell the owner plainly that the model pool is temporarily out of
   usable ChatGPT/Codex access and give the nearest cooldown time. Do **not** remove accounts for
   temporary usage limits; removal is only for expired subscriptions via `chatgpt-sub-watch`.

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
