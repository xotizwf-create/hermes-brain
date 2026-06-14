---
name: email-watchers
description: "Build and troubleshoot scheduled email watcher jobs that notify only on real actionable mail."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  created_by: agent
  hermes:
    tags: [email, cron, gmail, imap, himalaya, monitoring, notifications]
---

# Email Watchers

Use this skill when creating, reviewing, or debugging scheduled email monitoring jobs that send Telegram/DM notifications about important mail.

This is a class-level workflow skill. It complements `himalaya` (mailbox operations) and Hermes cron/gateway docs (scheduling and delivery).

## Core rule

A watcher must be deterministic about what it reports. Do not let an LLM infer that a message exists unless the current mailbox query returned that exact message in the same run.

## Recommended architecture

Prefer a script-backed cron job over a free-form LLM cron prompt for mail monitoring:

1. Query the mailbox with a deterministic command/API call.
2. Parse structured output, preferably JSON.
3. Filter by folder, flags, sender type, date, and stable message identity.
4. Compare against a persistent state file containing already-notified IDs.
5. Print notification lines only for new qualifying messages.
6. Print nothing when there is nothing to report.
7. Let cron deliver stdout verbatim with `no_agent=True`, or pass the compact candidate list to an agent only for summarization.

## Deduplication

Do not rely on Hermes memory inside cron jobs for deduplication. Cron sessions may run with memory disabled or unavailable. Use a local state file instead, for example:

- `~/.hermes/state/email_watch_<account>.json`
- Keys: message UID / Message-ID / provider stable ID, plus subject/from/date as fallback metadata
- Update state only after successful candidate selection

## Safe mailbox checks

When using Himalaya:

1. Start with `himalaya account list` and `himalaya folder list`.
2. Prefer the default configured account unless `himalaya --help` confirms the current version supports the account-selection syntax you plan to use.
3. Use `himalaya envelope list --output json` for envelope-only checks.
4. Avoid `message read` in watcher jobs unless the body is necessary, because reading can change flags or trigger side effects depending on backend/client behavior.
5. Re-list after moving/marking messages because Himalaya message IDs can be folder-relative.

## Filtering policy

For a user-facing actionable-mail watcher, report only messages that satisfy all of these:

- currently returned by the mailbox query
- in the intended folder, usually `INBOX`
- actually unread if the watcher is configured for unread mail (`Seen` flag absent)
- not an automated sender/newsletter/service notification
- not previously notified according to the local state file

If any query fails or returns unparsable output, fail closed: print nothing or a diagnostic only if the user explicitly asked for watchdog health alerts. Never invent likely messages from prior runs, prompt examples, or partial context.

## Prompt-only watcher pitfalls

A cron prompt like “look for new messages or unread, use memory to avoid repeats” is fragile because:

- memory may be unavailable in cron sessions
- LLMs can over-report from stale context if the command failed
- “new or unread” can surface old unread messages forever
- folder-relative IDs can produce false duplicates or misses

If using an agent-driven job anyway, make the prompt strict:

- “Only report rows present in the current command output”
- “If the command errors, respond exactly `[SILENT]`”
- “Do not use memory; use the attached state file or report only current unread messages”
- “Do not summarize or infer mail that is not in the latest JSON output”

## Verification checklist

Before declaring a watcher fixed:

1. Run the exact mailbox query manually.
2. Confirm current unread count and flags.
3. Confirm notification candidates correspond to real current envelope rows.
4. Confirm already-notified IDs are suppressed on a second run.
5. Confirm errors produce silence or an explicit health alert, not mail notifications.
6. For Hermes cron, prefer `no_agent=True` plus a script that prints the final user-facing text itself; this prevents the LLM from hallucinating old envelopes when mail commands fail.

## Known-good Hermes cron pattern

For a Gmail/Himalaya unread-INBOX watcher, use a script like `~/.hermes/scripts/mail_watch.py` and configure the cron job with:

- `script: mail_watch.py`
- `no_agent: true`
- `deliver: telegram` or the intended destination
- no skills and no free-form agent prompt needed for the actual decision

The script should:

- run `himalaya envelope list --folder INBOX --page-size 50 --output json`
- parse only the current JSON envelope list
- require the `Seen` flag to be absent
- suppress automated senders/newsletters/service domains
- dedupe using `~/.hermes/state/mail_watch_seen.json`
- catch command/parse errors and exit successfully with empty stdout, so broken mail checks do not become false user alerts

## References

- `references/false-positive-mail-watch-2026-05.md` — example false-positive caused by prompt-only cron watcher, unavailable memory, and partial command failures
