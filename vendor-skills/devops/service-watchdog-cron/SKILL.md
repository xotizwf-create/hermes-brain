---
name: service-watchdog-cron
description: "Create silent Hermes cron watchdogs for service availability checks: no message when healthy, urgent Telegram alert on outage."
version: 1.0.0
author: Hermes Agent
metadata:
  created_by: agent
  created_at: "2026-06-01"
---

# Service watchdog cron

Use when Александр asks to periodically check whether a website/service is alive and alert only on failure.

## Workflow

1. Identify the canonical public URL/domain from project docs, memory, session history, or the user. Do not guess if multiple production domains exist.
2. Smoke-check the URL manually first with a lightweight HTTP request:
   - short timeout, custom User-Agent;
   - treat 2xx/3xx and ordinary 4xx as reachable unless the user needs an authenticated/business-health check;
   - treat 5xx, DNS/TLS/timeout/network errors as failures.
3. Implement a script-only watchdog under `~/.hermes/scripts/`:
   - stdout empty = healthy/silent;
   - non-empty stdout = exact Russian alert delivered to Telegram;
   - do 2–3 quick attempts with a small pause to avoid false positives;
   - include service name, URL, Moscow timestamp, response status if known, and short reason;
   - return exit code 0 for detected outage after printing the alert, so the user gets the intended message rather than a technical scheduler error.
4. Create a Hermes cron job with `no_agent=True`, `script=<name>.py`, `deliver=origin` unless the user requests another target, and the requested schedule.
5. Verify:
   - run the script directly while the service is healthy and confirm stdout is empty;
   - create/list the cron job and confirm it is enabled with the intended schedule;
   - trigger one scheduler run and confirm `last_status` becomes ok and no message is sent while healthy;
   - convert `next_run_at` to Moscow time before confirming to Александр.

## Daily operational digests

Use a two-stage cron pattern when the user wants a scheduled daily health digest rather than immediate outage-only alerts:

1. Create an early read-only collector job (`deliver=local`) that runs before the requested delivery time. It gathers facts from project docs and lightweight checks only: availability, backup freshness, RAM/swap/disk/load, recent errors, MCP reachability, and explicit "not checked" gaps.
2. Create a separate delivery job at the requested user time with `context_from=[collector_job_id]`. This job turns the collector output into a human digest.
3. Convert Moscow delivery times to UTC cron expressions before creating jobs and verify `next_run_at` back in Europe/Moscow. Examples: 08:30 МСК collector → `30 5 * * *`; 09:00 МСК digest → `0 6 * * *`.
4. Keep collector prompts strict: read-only, no restarts, no builds/tests/migrations, no secret values, no heavy operations on production hosts.
5. Digest formatting for Александр: Russian, concise, no commands/paths/job IDs/IPs/secrets/stack traces. Use moderate context-appropriate emoji and per-service OK/WARN/FAIL sections plus a final "Что сделать" only when action is actually needed.

## Owner-facing response

Keep it Russian and non-technical. Mention only:
- monitoring/digest is active;
- frequency and Moscow-time delivery/check time;
- what condition triggers an alert or what the digest covers;
- next check time in Moscow time if useful.

Do not expose script paths, job IDs, commands, or UTC timestamps in chat.

## Pitfalls

- Do not use an LLM cron prompt for pure availability checks; a script-only job is cheaper and quieter.
- Do not alert on a single transient failure if the user did not explicitly ask for single-attempt paging.
- Do not run heavy checks on production servers for memory-constrained projects; prefer public HTTP checks or a lightweight health endpoint.
