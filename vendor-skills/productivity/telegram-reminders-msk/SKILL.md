---
name: telegram-reminders-msk
description: Create one-shot Telegram reminders for Александр with correct Moscow-time handling.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [reminders, cron, telegram, timezone]
---

# Telegram reminders for Александр

Use this skill whenever Александр asks to set a reminder, especially from Telegram/voice.

## Core rule

Александр's unqualified reminder times are Moscow time: Europe/Moscow, UTC+03:00. Never pass a naive date/time to the scheduler for a one-shot reminder.

## Procedure

0. First classify the intent from the wording:
   - «Напомни…», «поставь напоминание…» = create or update a reminder.
   - «У меня стоит напоминание…», «проверь напоминание…», «есть ли напоминание…» = verify/list existing reminders first; do not create a duplicate unless the reminder is absent and the user clearly wants it added.
   - When only verifying, answer with what is scheduled and do not mention unrelated side effects.
1. Parse the requested date/time in Europe/Moscow unless the user explicitly gives another timezone. All unqualified times from Александр are Moscow time.
2. Convert the target time to an explicit ISO timestamp with timezone.
   - Preferred: include the Moscow offset directly, e.g. `2026-05-31T15:00:00+03:00`.
   - If using UTC, convert first and include `+00:00`, e.g. `2026-05-31T12:00:00+00:00` for 15:00 Moscow.
   - For recurring cron schedules, remember the scheduler cron expression is UTC unless verified otherwise. Convert MSK to UTC first: 09:00 МСК → `0 6 * * *`, 17:30 МСК → `30 14 * * *`.
3. For Александр's personal reminders, create the cron job in the `nikita-reminders` profile's own cron store so delivery comes from Никита's Telegram bot. Do **not** create the job in the default profile with only `profile='nikita-reminders'`: that runs the script under Никита but the default gateway still performs Telegram delivery, so the message appears from the main assistant. Use the Nikita profile gateway/scheduler (for example `hermes --profile nikita-reminders cron create ... --deliver telegram`) or manually ensure the job lives under `~/.hermes/profiles/nikita-reminders/cron/jobs.json` with scripts present in `~/.hermes/profiles/nikita-reminders/scripts/`.
4. Use `repeat=1` for one-shot reminders; for daily/recurring reminders use a recurring cron expression and a large repeat count or forever, as appropriate. For Александр's reminders/automations, deliver to the Telegram group «Уведомления» (`telegram:-5120862157`) unless the owner explicitly specifies another non-personal target. Do not send reminder cron deliveries to the owner's private chat.
5. For recurring reminders that should send a fixed text, prefer a `no_agent=True` script-only job whose stdout is the exact message. This avoids model variance and keeps the reminder cheap and reliable.
5. After creation, verify the actual scheduled time before confirming to the user:
   - Inspect the returned `next_run_at` and convert it to Europe/Moscow with a tool if needed.
   - Run/list cron jobs if needed and confirm the reminder appears among active jobs.
   - If intended 15:00 MSK, expected UTC is 12:00, not 15:00.
6. If the created job is off by timezone, remove it immediately and recreate it correctly.
7. User-facing confirmation must be short and human: `Поставил на 15:00 МСК` (or include the date for non-today reminders). Do not include job ids, commands, UTC times, or other technical details.
8. Never claim a reminder, message, email, or any other side effect was created/sent unless the corresponding tool output in this session confirms it. If the task is only reminder verification, keep the response scoped to the reminder check.

## Reminder message style

Александр likes reminders to feel human and warm, not like system notifications. Use a short clear message, one or two context-appropriate emoji, and avoid dry technical wording. Example for an archive task:

```text
📦 Александр, не забудь отправить архив Максиму Анатольевичу

Лучше сделать это сейчас, пока день не убежал 🙂
```

Keep emoji relevant to the task: 📦 for archive/package, 📞 for calls, 🧾 for documents, ⏰ only when the time itself matters. Do not overload reminders with decorative emoji.

## Active reminders and missed-reminder audit

- To show active reminders, run `/root/.hermes/scripts/reminder_audit.py --list` and translate the result into a short Russian message.
- A script-only watchdog cron job named `reminder-audit` runs every 15 minutes. It stays silent when everything is OK and alerts only if an active reminder is overdue, failed, or not delivered.
- The audit script is `/root/.hermes/scripts/reminder_audit.py`; it reads the local Hermes cron jobs file and displays reminder times in Moscow time.

## Pitfall this prevents

Do not create reminders with schedule strings like `2026-05-31T15:00:00` or `once at 2026-05-31 15:00` when the user meant Moscow time. These naive times can be interpreted as UTC and fire three hours late for Александр.

## Example

User: «Напомни в 15:00 позвонить деду»

Correct scheduler timestamp for 2026-05-31:

`2026-05-31T15:00:00+03:00`

If the cron tool returns `next_run_at: 2026-05-31T12:00:00+00:00`, that is correct: it equals 15:00 Moscow
