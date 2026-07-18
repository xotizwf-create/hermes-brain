#!/usr/bin/env bash
# Inspect hermes journal for the contract-processing session: tools used, timings.
journalctl -u hermes-gateway --since -4hours --no-pager > /tmp/hj.log
echo "=== tool mentions count ==="
grep -o -E '[a-z_]*(incoming_contract|contract_from|contract_files|contract_templates|save_contract|ensure_organization|read_table_rows|get_contracts|view_incoming)[a-z_]*' /tmp/hj.log | sort | uniq -c | sort -rn | head -20
echo "=== lines mentioning tool calls (sample with time) ==="
grep -E 'tool|Tool' /tmp/hj.log | grep -i -E 'prostye|contract' | tail -40
echo "=== journal size ==="
wc -l /tmp/hj.log
