# LiteExams / Gov Exams: read-only subscription payment check

Use this when Александр asks whether anyone paid for a LiteExams subscription today or over a recent period.

## Scope and safety

- Treat as production read-only unless the user explicitly asks for a fix.
- Use the secure project access card for `gov-exams-app`; never print IP/user/password, database URLs, Telegram tokens, YooKassa secrets, or webhook secrets.
- The LiteExams server is small; do preflight and avoid builds, migrations, restarts, or heavy scans for a payment-status question.
- Interpret "today" as Moscow time (`Europe/Moscow`) unless the user specifies another timezone.

## Canonical source

The application records YooKassa attempts in PostgreSQL table:

- `yookassa_payment_attempts`
- key fields: `payment_id`, `telegram_id`, `chat_id`, `username`, `amount_value`, `currency`, `status`, `created_at`, `updated_at`, `succeeded_at`, `notified_success_at`, `metadata`
- successful payment: `status = 'succeeded'`, preferably counted by `succeeded_at` in the Moscow-day window

Access activation can be cross-checked in the Telegram access/user table if present, but the primary evidence for payment is `yookassa_payment_attempts`.

## Minimal query pattern

Use a single read-only psql session with repeated local bounds CTEs per SELECT. Do not define `WITH bounds AS (...)` once and reuse it across separate SELECT statements; CTE scope is one statement only.

Suggested checks:

1. Count attempts created today by status:
   - `created_at >= today_msk_start AND created_at < tomorrow_msk_start`
2. List successful payments whose `succeeded_at` (fallback `updated_at`) falls today:
   - `status = 'succeeded'`
   - `coalesce(succeeded_at, updated_at, created_at)` in the Moscow-day window
3. Show the latest 5 successful payments overall as a sanity check.
4. Optionally check access rows updated/created today, if the table/schema exists.

## Reporting style

Report concise operational facts:

- whether there were payments today
- counts of created attempts and successful payments
- if non-zero: time in MSK, username/telegram_id when appropriate, amount/currency
- if zero: include the last successful payment timestamp as sanity evidence

Do not include raw SQL, connection details, or secrets in the user-facing answer unless explicitly requested.
