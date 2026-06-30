# Diagnostic-only production/agent incident pattern

Use when the user asks why an automated agent, MCP tool, cron job, or production workflow produced an unexpected artifact, and they did **not** ask for a fix.

## Safe investigation sequence

1. Confirm the task mode in your own reasoning: investigation only, read-only by default.
2. Identify the artifact and source of creation:
   - persisted payload fields such as `source`, `model`, `saved_at`, `raw_input`, `analysis`, `report_text`;
   - job/cron prompt used by the automation;
   - MCP/tool handler that accepted and stored the payload;
   - active contract/schema/prompt version at the time if available.
3. Compare expected contract vs actual artifact:
   - required human-readable sections;
   - required structured JSON fields;
   - whether JSON was omitted, truncated, split into another field, or normalized by backend code;
   - whether the backend parsed text as fallback instead of using structured fields.
4. Build a finding table:
   - expected behavior;
   - actual stored data;
   - component responsible;
   - evidence location/command result;
   - confidence.
5. Present fix options separately and do not execute them until the user approves.

## Pitfall from a real session

A user asked to understand why an Albery Zoom report was generated in the wrong structure through MCP. The assistant incorrectly applied a small parser fix before completing diagnosis. Correct handling would have been:

- inspect `raw_json.ai_report.source` to verify MCP origin;
- inspect `analysis` vs `report_text` to see whether the agent passed full structured data but produced a mismatched visible report;
- inspect the live `zoom_processing` contract and cron/MCP instructions;
- explain the divergence as an agent contract-following issue, not jump to code changes;
- only after approval modify prompts/code/data.

If a write happens by mistake, revert it immediately, verify revert in git and on the affected runtime, and disclose the mistake plainly.