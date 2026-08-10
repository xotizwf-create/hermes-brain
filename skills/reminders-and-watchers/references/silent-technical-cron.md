# Silent technical cron pattern

Use this for periodic technical keepalive/refresh actions that should run quietly and alert only on failure (for example a minimal CLI request that starts/refreshes an external service's rolling limit window).

## Pattern

1. Prefer `cronjob`/`hermes cron` in `--no-agent` mode with a small script. This avoids spending LLM tokens for the scheduled job itself.
2. The script should:
   - do the smallest real action that satisfies the goal;
   - write **nothing to stdout on success** so no Telegram message is delivered;
   - write one concise human-readable alert on failure and exit non-zero;
   - use an explicit timeout so hung CLIs do not block forever.
3. Deliver failure alerts to the configured notifications group, not to the owner's private chat.
4. Convert user-facing Moscow times to the scheduler/server timezone and verify `next_run_at`.

## Example: Claude Code limit-window refresh

Live on 217 as job `claude-code-limit-refresh` (`359c8c2c7cab`). Versioned source:
`scripts/claude_limit_refresh.sh` in this repo, deployed to `/root/.hermes/scripts/`.

Server timezone may be UTC. For 06:00 / 11:00 / 16:00 МСК, use cron `0 3,8,13 * * *` on a UTC scheduler.

**Multiple accounts (since 2026-08-10).** The script refreshes every connected account in one run:
the historical account through the ordinary login in `/root/.claude`, and any additional account
through `<secure>/claude_code/accounts/<slug>/oauth_token` (a long-lived token from
`claude setup-token`, mode 600) with its own `HOME` under `/root/claude-accounts/<slug>` — two
accounts sharing one `HOME` overwrite each other's login. Add one with
`python scripts/add_claude_account.py <slug>`; no cron edit is needed. Exit code = number of
accounts that failed, so one dead account never hides the others.

Two traps worth keeping (both hit on 2026-08-10):

- **Give the CLI `</dev/null`.** Without it `claude` waits ~3 s for stdin and exits non-zero when the
  script is run by hand over SSH — the manual check would report a failure that cron never has.
- **Account-level refusals arrive in stdout, not stderr.** A 403 («organization has disabled Claude
  subscription access») or an exhausted limit comes back as the JSON result body while stderr stays
  empty, so an alert built only from stderr says «Код: 1» and nothing else. Parse
  `api_error_status` + `result` from the JSON before giving up.

Minimal script shape (single-account original, kept as the pattern skeleton):

```bash
#!/usr/bin/env bash
set -euo pipefail

export HOME=/root
PROMPT='OK'
TMP_OUT="$(mktemp)"
TMP_ERR="$(mktemp)"
cleanup() { rm -f "$TMP_OUT" "$TMP_ERR"; }
trap cleanup EXIT

if timeout 90s claude -p --model claude-haiku-4-5 --output-format json "$PROMPT" >"$TMP_OUT" 2>"$TMP_ERR"; then
  exit 0  # silent success
fi

status=$?
err="$(tr '\n' ' ' < "$TMP_ERR" | cut -c1-500)"
printf '🔴 Не удалось обновить окно Claude Code лимитов. Код: %s. %s\n' "$status" "$err"
exit "$status"
```

Cron shape:

```text
schedule: 0 3,8,13 * * *
script: claude_limit_refresh.sh
no_agent: true
deliver: telegram:-5120862157
```

After creating, run the job once through the scheduler and verify `last_status: ok` and `last_delivery_error: null`.
