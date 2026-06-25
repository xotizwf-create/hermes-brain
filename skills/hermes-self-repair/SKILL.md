---
name: hermes-self-repair
description: Use when the Hermes gateway runtime itself is suspect or broken — symptoms like a giant/duplicated run.py, duplicated config.yaml blocks, a restart that hangs or kills the bot, self-patchers (apply_patches / ExecStartPre) that re-inject the same text every start, or a missing/regressed code-task time-budget classifier. A diagnosis-first, restart-last runbook for safely repairing the gateway on the prod server without taking the bot down, with backups and a tested rollback at every step.
---

# Skill: hermes-self-repair

Repairing the thing that runs you. The gateway (`/usr/local/lib/hermes-agent/gateway/run.py`,
service `hermes-gateway`) is what reads Telegram, runs the model, and applies its own patches at
start. If it's broken on disk, **the next restart loads the broken file** — so the cardinal rule is:
**verify before you touch, and restart only last, with a rollback ready.** Never restart on a guess.

## Cardinal rules
1. **Verify every claim before acting.** "run.py is corrupted", "config has duplicate blocks",
   "the classifier is gone" are *hypotheses* until a command proves them. A diagnosis carried over
   from a flaky/garbled session is **not** evidence — re-run it cleanly.
2. **The running process is your safety net.** The gateway keeps the last good code in memory; the
   on-disk file may be worse. Don't restart until the on-disk file is proven good (`py_compile` +
   sanity checks) and you have a backup to roll back to.
3. **Backup before every write.** `cp -p file file.bak.$(date +%Y%m%d_%H%M%S)`.
4. **One controlled restart, observed.** Restart from outside any chat turn, then immediately check
   health; if bad, roll back and restart again.
5. **Idempotent self-patchers only.** Anything that runs on every gateway start (ExecStartPre,
   `apply_patches.py`) must be safe to run 1000× — it must check "already applied?" and do nothing if
   so. A self-patcher that *appends* unconditionally is a time bomb (it grows the file every boot).
6. **Auxiliary failures are runtime failures too.** If self-check reports `unhealthy`, Groq/TPM,
   compression, compaction, or summary timeouts, treat it as a gateway repair path: inspect config,
   provider health, disk headroom, and only then restart. See `references/auxiliary-provider-health.md`.
7. **Unit-file warnings count as unfinished repair.** If `daemon-reload` or journals show unsupported systemd keys, clean them up before saying the gateway is healthy. See `references/systemd-unit-hygiene.md`.

## Phase 1 — Diagnose (read-only, no writes, no restart)
Run these and read the actual numbers. Nothing here changes state.

```bash
RUN=/usr/local/lib/hermes-agent/gateway/run.py
# size & line count — a normal run.py is large but not absurd; flag if wc -c is many MB
wc -lc "$RUN"
# is a docstring/marker duplicated? count exact occurrences
grep -c 'Patched build' "$RUN" 2>/dev/null
grep -c '"""Hermes message gateway' "$RUN" 2>/dev/null
# does it even still compile?
/usr/local/lib/hermes-agent/venv/bin/python -m py_compile "$RUN" && echo COMPILE_OK || echo COMPILE_FAIL
# what re-applies things at every start? (the suspect for repeated injection)
ls -l /etc/systemd/system/hermes-gateway.service.d/ 2>/dev/null
grep -Rn 'ExecStartPre' /etc/systemd/system/hermes-gateway.service.d/ 2>/dev/null
# clean backups to restore from, newest last
ls -lt /usr/local/lib/hermes-agent/gateway/run.py.bak.* 2>/dev/null | head
# config duplication
grep -nE '^model:' /root/.hermes/config.yaml
grep -cE '^\s*reasoning_effort:' /root/.hermes/config.yaml
# is the running process old (memory may differ from disk)?
systemctl show hermes-gateway -p ActiveEnterTimestamp -p MainPID
```

Decide from the output:
- **run.py compiles + counts look normal** → no corruption; skip Phase 2, go to the classifier work.
- **run.py is huge / marker counted thousands of times / COMPILE_FAIL** → corruption confirmed,
  do Phase 2 first.
- **An ExecStartPre script appends a docstring/marker unconditionally** → that's the root cause of
  growth; it must be made idempotent (Phase 2.3) or the file will re-bloat after every restart.

## Phase 2 — Repair the file (only if Phase 1 confirms a problem)
2.1 **Get a clean run.py.** Prefer the newest backup that compiles and whose marker count is 1:
```bash
for b in $(ls -t /usr/local/lib/hermes-agent/gateway/run.py.bak.*); do
  if /usr/local/lib/hermes-agent/venv/bin/python -m py_compile "$b" 2>/dev/null && \
     [ "$(grep -c 'Patched build' "$b")" -le 1 ]; then echo "CLEAN: $b"; break; fi
done
```
If no clean backup exists, re-fetch a pristine `run.py` from the Hermes install source
(`hermes update` re-installs `/usr/local/lib/hermes-agent`; do it only when you can immediately
re-apply the legitimate patches afterward) — or de-duplicate in place: collapse repeated identical
leading docstring lines down to one, then `py_compile` to confirm.

2.2 **Stage, don't overwrite live.** Write the fixed file to a temp path, `py_compile` it, then
atomic move: `cp -p $RUN $RUN.bak.<ts>` → `mv fixed.py $RUN`. Never edit the live file in place
without a compiled temp.

2.3 **Make the self-patcher idempotent.** Whatever appends the docstring/marker every start must
become check-then-act. Pattern for `apply_patches.py` (and any ExecStartPre):
```python
text = path.read_text()
if MARKER in text:            # already applied — do nothing
    print("[hermes-reapply] already applied; skip"); 
else:
    text = apply(text)        # do the change exactly once
    tmp = path.with_suffix(".tmp"); tmp.write_text(text)
    import py_compile; py_compile.compile(str(tmp), doraise=True)  # never ship a broken file
    os.replace(tmp, path)
# always exit 0 so a patch failure never blocks gateway start
```
The canonical source of these patchers lives in the **site repo** (`scripts/hermes_apply_patches.py`),
not in this brain. Fix it there too and redeploy, or the next full reinstall reintroduces the bug.

## Phase 3 — Code-task time-budget classifier (the 2026-05-31 lesson)
Goal: a one-line support-text edit that ends in a service restart must get the **code budget (3600s)**,
not the chat budget (600s), so it isn't killed mid-task. In `gateway/run.py`'s `_run_agent`, the task
text is the `message` param (not `event` — that exact bug already bit us, see `hermes.md`). Classify
as code when the message mentions code/server work:
```python
_event_text = (message or "").casefold()
_CODE_HINTS = (
    "файл", "конфиг", "config", ".env", "сервер", "на сервере", "в боте", "в коде",
    "systemctl", "service", "деплой", "deploy", "правк", "замен", "replace", "скрипт",
    "script", "репозит", "repo", "nginx", "база", "sql", "лог ", "git", "бот",
    "code", "file", "server", "function", "функци", "рефактор", "refactor", "stack", "трейс",
)
_is_code = any(h in _event_text for h in _CODE_HINTS)
_budget = code_task_wall_timeout_seconds if _is_code else task_wall_timeout_seconds
```
Carry this in the idempotent patcher (guarded by a unique marker) so `hermes update` can't drop it.
Pair it with the deeper fix: real coding is delegated to Codex in a separate process
(`skills/codex-delegation`), so the wall-clock guard rarely matters for quality anyway.

## Phase 4 — Config hygiene
De-duplicate `config.yaml` (e.g. a tripled `model:` block — keep one). Back up first
(`config.yaml.bak.<ts>`), load it with a YAML parser to confirm it still parses, then write back.
Keep `reasoning_effort: medium` for the shared 5h limit; get high reasoning for code via Codex
delegation, not a global bump (see `engineering/agentic-coding.md`).

## Phase 4.5 — Auxiliary/provider health alerts
When the symptom is a self-check alert about auxiliary providers, Groq/free-tier limits, compression,
web extraction, or context-summary timeouts, use `references/auxiliary-provider-health.md` before
changing providers. In short: inspect the active auxiliary routing without printing secrets; do not
assume a provider that works for tiny helper calls can handle compression; validate real credentials
before switching to OpenRouter/Google/etc.; move heavy auxiliary roles only to a verified high-budget
provider or to the already-working `auto` route; then run `hermes config check` and the self-check
script. If the self-check scans a rolling journal window, make it ignore pre-fix journal lines by
starting no earlier than the config/script mtime, so the next hourly alert is not stale noise.

## Phase 4.6 — systemd unit hygiene (do not "improve" blindly)
When touching `/etc/systemd/system/hermes-gateway.service` or drop-ins, only use directives supported by the host's systemd version. A unit can still start while `systemctl daemon-reload` prints `Unknown key ...` warnings; those warnings are real operational noise and must be cleaned up before declaring the gateway healthy.

Safe pattern:
```bash
systemctl --version | head -1
cp -p /etc/systemd/system/hermes-gateway.service /etc/systemd/system/hermes-gateway.service.bak.$(date +%Y%m%d_%H%M%S)
systemd-analyze verify /etc/systemd/system/hermes-gateway.service 2>&1 | tee /tmp/hermes-unit-verify.log
systemctl daemon-reload 2>&1 | tee /tmp/hermes-daemon-reload.log
journalctl -b -u hermes-gateway --no-pager | grep -iE 'Unknown key|Failed to parse|bad unit|error' || true
```
If you introduced unsupported keys (for example newer restart-backoff directives such as `RestartSteps` / `RestartMaxDelaySec` on an older systemd), remove them or replace with older supported equivalents. Re-run `daemon-reload` and the grep until the warnings are gone. Prefer `daemon-reload` first; do **not** restart just to test unit parsing unless a restart is actually needed.

## Phase 4.7 — Telegram rich messages after Hermes updates

If the symptom is “answers look worse / formatting degraded after update” and logs show
`rich_messages_patch: cannot read telegram.py`, do **not** recreate the old monkey-patch blindly.
Newer Hermes builds moved Telegram from `gateway/platforms/telegram.py` to
`plugins/platforms/telegram/adapter.py` and include native rich-message support guarded by config.
Use this safe order:

1. Inspect `telegram.extra.rich_messages` in `/root/.hermes/config.yaml` without printing tokens.
2. If the native adapter contains `_rich_messages_enabled`, enable the config flag instead of patching code:
   `hermes config set telegram.extra.rich_messages true`.
3. Make the ExecStartPre rich patcher idempotently detect the native adapter and exit with a clear
   “native adapter supports rich_messages; no patch needed” message, so future restarts/updates do not
   emit stale missing-file errors.
4. Validate config YAML and the patcher with `py_compile`. Restart only after the normal restart-last checks.

## Phase 5 — One controlled restart + health check

**Do not restart `hermes-gateway` from inside a gateway-handled chat/tool process.** Hermes blocks this
because the restart would terminate the process that is running the command and can leave the user
without a clean completion. If you are in Telegram/gateway, ask the owner to send `/restart`, or run the
restart from a separate shell outside the running gateway.

From an external shell:
```bash
systemctl restart hermes-gateway
sleep 3
systemctl is-active hermes-gateway          # want: active
systemctl show hermes-gateway -p MainPID    # want: a fresh PID
journalctl -u hermes-gateway -n 40 --no-pager | grep -iE 'error|traceback|reapply|Unknown key|Failed to parse' 
```
Confirm the bot answers Telegram (a `/accounts` or a tiny test push) **without printing tokens**.
If `is-active` is not `active`, or the log shows a traceback: **roll back immediately** — restore the
`.bak.<ts>` files and restart again, then report and stop. Do not iterate blindly on prod.

## Rollback (always ready before Phase 5)
```bash
cp -p $RUN.bak.<ts> $RUN
cp -p /root/.hermes/config.yaml.bak.<ts> /root/.hermes/config.yaml
systemctl restart hermes-gateway && systemctl is-active hermes-gateway
```

## Hard rules
- Diagnose before you touch; restart last; rollback ready before the restart.
- Every on-disk write: backup + `py_compile`/YAML-parse + atomic move.
- Self-patchers must be idempotent and always exit 0.
- Never restart through a flaky/garbled control channel — if outputs are inconsistent, stop and
  report; a corrupted command on prod is worse than waiting.
- Secrets: references only; never printed, committed, or passed as CLI args.
- Mirror any fix to the canonical source (site repo `scripts/`) so a reinstall doesn't undo it.

## Done when
Phase 1 numbers are clean (run.py compiles, markers == 1, config parses, no looping appender), the
classifier gives code/server edits the 3600s budget via an idempotent guarded patch, auxiliary/provider
routes are validated for the workload that triggered the alert (not just for tiny helper calls), one
observed restart left the gateway `active` with a fresh PID and clean logs when a restart was needed,
the bot answers Telegram, and the fix is mirrored to the site repo when it changes canonical runtime
code. Log operational lessons in the relevant brain file (`logs/changelog.md`, `logs/mistakes.md`, or
a project incident file) rather than relying only on chat history.
