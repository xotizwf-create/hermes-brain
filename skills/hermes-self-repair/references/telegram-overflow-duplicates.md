# Telegram long-final duplicate after partial overflow

## Symptom
A long final answer appears twice (or the visible prefix repeats) in Telegram. The owner may also complain about status/progress spam during the investigation.

## Durable root cause pattern
Telegram messages have a hard length limit. Hermes handles an over-limit final reply by editing the existing preview/final message with chunk 1, then sending continuation chunks.

If a continuation chunk fails after chunk 1 is already visible (`RetryAfter`, flood-control, transient network/API error), the delivery path has already produced a user-visible side effect. Treating that failure as a generic `retryable=True` error is unsafe: the runtime may retry the whole final answer and duplicate the prefix, which can further amplify Telegram flood-control.

## Correct behavior
- The adapter should return partial-failure metadata (`partial_overflow`, delivered chunk count, last delivered message id, delivered prefix).
- The partial-overflow failure must be **non-retryable** for the whole final answer.
- If the stream consumer can recover, it should send only the missing tail, not the whole response again.
- During live incident handling, avoid repeated progress/status messages; send only blockers and the final result unless the owner asks for updates.

## Verification recipe
```bash
# Inspect recent signatures without changing state
journalctl -u hermes-gateway --since '-2 hours' | grep -iE 'overflow_continuation_failed|partial_overflow|RetryAfter|Flood control|flood'

# Verify the persistent patch is installed in the unit and idempotent
systemctl cat hermes-gateway | grep -F 'telegram_overflow_dedup_patch' || true
/usr/local/lib/hermes-agent/venv/bin/python /root/.hermes/patches/telegram_overflow_dedup_patch.py

# Regression test
cd /usr/local/lib/hermes-agent
/usr/local/lib/hermes-agent/venv/bin/python -m pytest tests/gateway/test_telegram_overflow_partial.py -q
```

Expected test result: all tests pass, including coverage that continuation failure after chunk 1 is visible is non-retryable and fallback sends only the tail.

## Restart policy
Do not restart `hermes-gateway` on a guess. Restart only if the live process is proven to lack the patch or an update replaced the adapter. If a restart is needed, follow the main skill's restart-last + rollback procedure.
