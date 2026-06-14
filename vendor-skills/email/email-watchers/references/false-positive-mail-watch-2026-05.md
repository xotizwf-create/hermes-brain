# False-positive mail watcher: May 2026

## Symptom

A scheduled Telegram notification reported several unread actionable messages from a real sender, but the mailbox did not currently contain those unread messages.

Example notification shape:

- `✉️ Максим <...> — документы в работу — непрочитанное рабочее письмо...`
- repeated variants of the same sender/theme

## Root causes

The watcher was an agent-driven cron job with a broad natural-language prompt:

- check new mail in INBOX for the last ~2 hours or unread messages
- show only important human/work mail
- use memory to avoid repeat notifications

This produced a fragile setup:

1. Cron runs did not have usable memory, so the requested deduplication mechanism failed.
2. Some mailbox commands failed during the run, but the agent still produced a normal-looking report.
3. The prompt allowed “new or unread,” which can resurface old unread mail and is ambiguous when current command output is incomplete.
4. The final cron output contained only the generated notification lines, not the structured envelope rows that justified them, making the false positive harder to audit.

## Durable lesson

For scheduled email monitoring, do not rely on prompt instructions and memory for correctness. Use deterministic state and fail closed.

## Safer design

Use a script/no-agent watchdog pattern:

1. Query `himalaya envelope list --output json` for the intended folder.
2. Parse JSON and filter only current envelopes with `Seen` absent.
3. Exclude known automated senders and newsletters.
4. Deduplicate by stable message identity in a local JSON state file.
5. Print notification lines only for current, real, unseen, not-yet-notified messages.
6. On command error or unparsable output, print nothing unless the user asked for health alerts.

## Audit steps for future incidents

1. List cron jobs and identify the watcher job.
2. Inspect the most recent saved cron output for the exact delivered text.
3. Query the mailbox directly for current `INBOX` envelopes and flags.
4. Search all-mail/archive only to explain old references, not to justify a current unread alert.
5. If current mailbox state contradicts the alert, treat it as watcher logic failure and tighten the job
