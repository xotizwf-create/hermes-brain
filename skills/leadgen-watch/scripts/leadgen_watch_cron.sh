#!/usr/bin/env bash
# leadgen-watch hourly wrapper: молчит при успехе (кандидатов шлёт сам скрипт в TG),
# печатает (=доставляется в TG) только если python упал до своего tg_send.
set -u
pgrep -f 'leadgen_watch\.py' >/dev/null && exit 0
OUT=$(/usr/local/lib/hermes-agent/venv/bin/python /root/.hermes/agent-knowledge/skills/leadgen-watch/scripts/leadgen_watch.py 2>&1)
rc=$?
echo "$OUT" >> /root/.hermes/logs/leadgen_watch.log 2>/dev/null || true
if [ $rc -ne 0 ]; then
  echo "leadgen-watch: прогон упал (rc=$rc): $(echo "$OUT" | tail -2)"
fi
exit 0
