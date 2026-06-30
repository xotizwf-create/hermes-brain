# Albery Zoom report save-contract hardening

Use this when diagnosing Albery Zoom reports that were saved through MCP but later produce incomplete Bitrix dispatch cards, missing artifacts, or misleading task counts.

## Durable lesson

Do not fix this class of bug by making the text parser more permissive first. If `mcp_save_zoom_call_report` accepts a successful report whose structured `analysis` is only an abbreviated summary, downstream logic loses data even though the report looks saved.

The correct boundary is the save tool contract: a successful Zoom report must contain the full `zoom_processing` analysis object, not a shortened object with counters.

## Required successful payload shape

For `status=done`, require at least:

- `dispatch_summary` — non-empty human summary used for dispatch context;
- `leader_evaluations` — list, even if empty;
- `people` — object with participant/mentioned-person data;
- `operational_tasks` — list, even if empty.

For each operational task, require the fields needed by dispatch cards, such as owner, Bitrix user mapping, deadline text, result criteria, expected artifact, responsibility check, status, and source.

`status=error` can remain looser so failed processing attempts can be recorded without a full analysis object.

## Debugging sequence

1. Confirm the report source in DB/raw JSON is `mcp_save_zoom_call_report`.
2. Inspect whether `analysis` contains the full `zoom_processing` structure or only counters like `operational_tasks_count` / `leaders_present`.
3. Reproduce with a focused test that abbreviated `analysis` is rejected before DB persistence.
4. Keep parser fallback tests, but treat parser fallback as compatibility/read recovery, not the primary correctness layer.
5. Verify `preview_zoom_operational_tasks` after saving a full report; only dispatch to Bitrix after explicit owner approval.

## Deployment notes

- Prefer a branch + PR for this fix; do not push directly to `main` unless explicitly asked.
- Run narrow MCP contract tests plus adjacent tool-registry and Zoom parsing tests.
- If CI dependency audit fails on unrelated frontend packages, inspect failed logs and either fix the audit in the same PR only if safe and low-risk, or report it as a blocker; do not claim the MCP fix is red without checking the failed job.
