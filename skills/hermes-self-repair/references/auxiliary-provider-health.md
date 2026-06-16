# Auxiliary provider health and self-check alerts

Use this reference when `hermes_selfcheck.py` reports `Auxiliary: marking ... unhealthy`, `payment / credit error`, Groq rate-limit/TPM failures, or `Failed to generate context summary`.

## Durable lesson
Heavy auxiliary jobs are not the same as title/approval helpers. Compression, compaction, large web extraction, and long summarisation can send large payloads even when `compression.threshold` is low, because Hermes still keeps a minimum context window. A free-tier provider that works for small helper calls can be structurally unsuitable for heavy auxiliary paths.

## Groq free-tier pitfall
Groq free-tier `llama-3.3-70b-versatile` has a low tokens-per-minute ceiling for long compression payloads. Symptoms can appear as:

- `Auxiliary: marking ... unhealthy for 600s (payment / credit error)`
- provider labelled `local/custom` or Groq depending on config shape
- hard rate/size rejection on the compression request
- then fallback compression via the main provider timing out, e.g. `Failed to generate context summary: Codex auxiliary Responses stream exceeded ... timeout`

Do not keep shaving `compression.threshold` or `protect_last_n` as the primary fix. That reduces frequency/size but does not guarantee the heavy request fits a free-tier TPM ceiling.

## Safer fix pattern
1. Inspect `/root/.hermes/config.yaml` without printing secrets.
2. Identify which provider handles heavy auxiliary roles:
   - `auxiliary.compression`
   - `auxiliary.web_extract`
   - any long summarisation/extraction-specific auxiliary block
3. Keep low-limit/free-tier providers only for short helpers if they are useful.
4. Move heavy auxiliary roles to a provider with a verified long-context/TPM budget, or to `provider: auto` if that is the only already-working authenticated route.
5. Run `hermes config check` after the edit.
6. Validate with a live self-check run, and if restarting the gateway is needed, follow the normal restart-last preflight/rollback rules.

## Avoid stale self-check noise after repair
Hourly journal scanners can re-alert on lines written before the fix. If the self-check is script-only and scans a rolling journal window, make it start no earlier than the relevant config/script mtime after a repair. This suppresses one extra stale alert while still catching new post-fix failures.

Pattern:

```python
window_start = time.time() - minutes * 60
try:
    window_start = max(window_start, os.path.getmtime('/root/.hermes/config.yaml'))
except OSError:
    pass
journalctl --since '@<int(window_start)>'
```

## Disk preflight connection
Provider/config incidents often coincide with low disk or swap pressure and can look like “the agent is dumb”. Before restarting gateway or making runtime changes, check `df -h /`, `free -h`, and `systemctl status hermes-gateway`. If `/` is nearly full, clear safe temporary workdirs and vacuum journal before restart; do not touch project repos or deliverable outboxes casually.
