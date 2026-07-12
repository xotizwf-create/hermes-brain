# Runtime budget: hourly LLM lead screening

## Why this matters

The lead monitor runs as a no-agent cron job with a finite scheduler wall-clock limit. It fetches all enabled sources and then assesses fresh entries sequentially with an LLM. The setting `llm_min_interval_sec` intentionally inserts a pause after each assessment, so a high `max_llm_per_run` can make an otherwise healthy monitor exceed its deadline.

## Observed sizing rule

A full run with 20 LLM assessments and a six-second interval took about 138 seconds. That exceeded a 120-second script limit even though each individual assessment succeeded.

Set the live state file's `max_llm_per_run` to 10 unless a new measurement proves a higher value has a safe margin. Remaining fresh items are not marked seen before assessment; they remain eligible for the next hourly run.

## Correct recovery

1. Read the leadgen log and distinguish a scheduler timeout from an LLM or source failure.
2. Lower the live `max_llm_per_run`; do not alter the wrapper to convert timeouts into successful exits.
3. Trigger one normal cron run and verify its scheduler status is `ok` with no delivery error.
4. Check every active cron job for non-OK state before declaring the notification group clean.

## Testing note

`--list` checks collection and prefiltering without LLM calls or writes. `--dry-run` invokes the real LLM path and therefore is unsuitable as a quick health probe when the fresh queue is large.
