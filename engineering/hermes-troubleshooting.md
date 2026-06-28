---
id: hermes-troubleshooting
type: engineering
tags: [hermes, troubleshooting, triage, symptoms, gateway, runbook]
updated: 2026-06-28
secret_refs: []
---

# Hermes — диагностика по симптомам (что говорит владелец → куда смотреть)

Front door for the recurring Hermes failure modes, keyed on the **owner-facing complaint**
(plain Russian), because those symptoms are how problems actually arrive. Each row = symptom →
one journal check → cause → where the full fix lives. The hourly `scripts/hermes_selfcheck.py`
(self-check cron) already watches for most of these and alerts before the owner has to notice.

> Almost every "Hermes is broken" symptom is a **silent log-only degradation**: the chat looks
> normal, the model and the owner see nothing, only the gateway journal shows it. So the first move
> is **always** `journalctl -u hermes-gateway` with a grep — never guess.

## «Тупит / медленно / отупел / тормозит / долго думает / стал глупым»
Usually an invisible cascade, not the model. Check:
```bash
journalctl -u hermes-gateway --since '-3 hours' | grep -iE 'blocked:|unhealthy|Failed to generate context summary|Preflight compression|413|Request too large'
```
Causes (any/all at once):
1. **`Context file SOUL.md blocked: exfil_curl`** — text like `curl …$TOKEN` landed in SOUL.md and the
   threat scanner silently drops the WHOLE file from the prompt → agent loses its system rules. After
   editing SOUL, re-run `scan_for_threats`.
2. **`marking … unhealthy (payment / credit error)` / `413 Request too large`** — an aux-task payload
   exceeded the Groq free limit (70b = 12k tokens/MINUTE, 8b = 6k). One oversized request stuns all
   Groq aux tasks for ~600s. **Law: `compression` and `web_extract` must ALWAYS run on the 70b model
   (12k TPM), never 8b.** After any `hermes update` / aux-config pass, re-check `grep -A2 compression: /root/.hermes/config.yaml`.
3. **Context compression falling back to `openai-codex/gpt-5.5`** (120s timeouts) — anti-pattern (ties
   slow turns to the brain, blocker #1). Compression belongs on `llama-3.3-70b-versatile`, threshold ~0.04.

Full detail: `skills/hermes-self-repair/references/auxiliary-provider-health.md`, `engineering/hermes-gateway-ux.md`, `logs/mistakes.md`.

## «Одно и то же длинное сообщение пришло дважды / агент повторил финальный ответ»
Usually a Telegram **long-final partial overflow**. Gateway edits chunk 1 of a long final reply and
sends continuation chunks. If a continuation send fails after chunk 1 is already visible
(`RetryAfter`/flood-control/network), `overflow_continuation_failed` used to be reported as
`retryable=True`, so the runtime could retry the **whole** final reply and duplicate the delivered
prefix.
```bash
journalctl -u hermes-gateway --since '-2 hours' | grep -iE 'overflow_continuation_failed|partial_overflow|RetryAfter|Flood control|flood'
```
Fix: persistent startup patch `/root/.hermes/patches/telegram_overflow_dedup_patch.py` changes that
partial-overflow failure to `retryable=False` in `plugins/platforms/telegram/adapter.py` (idempotent;
look for marker "Retrying the whole final reply duplicates..."). Regression test:
```bash
cd /usr/local/lib/hermes-agent && /usr/local/lib/hermes-agent/venv/bin/python -m pytest tests/gateway/test_telegram_overflow_partial.py -q
```
Operational rule: do **not** restart gateway on a guess. First verify the marker/test. Restart only if
the live process still lacks the patch or after a Hermes update replaced the adapter.

## «Молчит / совсем не отвечает / ничего не приходит»
The brain (primary model) lost auth or hit its limit — nothing that needs the model can run.
```bash
journalctl -u hermes-gateway --since '-1 day' | grep -iE 'token_invalidated|missing access_token|refresh_token_reused|usage_limit_reached|Primary provider auth failed|401'
```
- **Codex/ChatGPT brain** (`openai-codex`): `token_invalidated` / `refresh_token_reused` /
  `missing access_token` → re-auth (`hermes auth add openai-codex --manual-paste`, device-code flow).
  This is **blocker #1**. See `projects/albery/hermes-operations.md` + memory `hermes-codex-auth`.
- **Usage limit reached** → single account, no fallback → waits for reset; self-check flags it.
- The Telegram **coder agent** (Claude on 217, `@GoogleDeck_Bot`) is separate → `engineering/claude-code-tg-agent.md`.

## «Отправил файл, а файл не пришёл» / «говорит, что сделал, а результата нет»
Silent **media drop**: `validate_media_delivery_path` rejects a path outside the allowlist (in
non-strict mode all of `/root` is denied) and the drop is **journal-only** — the model gets no error
and confidently reports success.
```bash
journalctl -u hermes-gateway | grep -i 'Skipping unsafe MEDIA'
```
Fix is a persistent ExecStartPre rescue patch (survives `hermes update`): a fresh (≤30 min) non-credential
file is copied to `/root/.hermes/outbox` and delivered. Save outbound files to `/root/.hermes/outbox`
(or `/tmp`). Source: `scripts/hermes_media_rescue_patch.py` (217), `scripts/hermes_media_rescue_patch_186.py`
(Albery/186). Manual guaranteed delivery: Telegram Bot API `sendDocument`, verify `"ok":true`.

## «Стало глупее / сломалось после обновления»
`hermes update` can wipe non-native patches and reset aux config (e.g. an auto-pass put ALL aux tasks
on 8b/6k). After any update: re-verify aux models (`compression` on 70b), and that ExecStartPre
self-patchers re-applied (`media_rescue`, etc.). Patches must be **idempotent** (check "already
applied?"). Memory: `albery-hermes-gateway-patches-status`. Repair runbook: `skills/hermes-self-repair/`.

## «База знаний не в чистом состоянии»
Handled automatically: the `brain-dirty-watchdog` cron auto-commits stable working-tree leftovers in
the server brain clone after ≥25 min, once `scripts/validate.py` passes; otherwise it alerts. No manual
action needed (source: `scripts/brain_dirty_watchdog.py`).

## Gateway itself looks corrupted (giant/duplicated `run.py`, restart hangs, looping self-patcher)
Different problem — code on disk is broken. Diagnose-first, restart-last runbook with backups and
rollback: `skills/hermes-self-repair/`. **Never restart on a guess.**
