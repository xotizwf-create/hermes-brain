# Albery Zoom report recovery and dispatch checks

Use this reference when Александр says that an Albery Zoom transcript already exists but the Zoom analytical report or Bitrix task dispatch did not appear.

## Durable lesson

Albery Zoom processing may have two separate stages:

1. **Transcript sync** — Zoom call and transcript segments exist in Albery.
2. **Management report + dispatch preview** — `zoom_calls.analytical_note` / `raw_json.ai_report` is saved and `operational_tasks` can be dispatched to Bitrix after owner approval.

Do not assume stage 2 happened just because the transcript exists.

## Fast diagnostic sequence

1. Read Albery live AI instructions first with `start_here_always_read_ai_instructions`.
2. Check readiness for the specific day with `get_report_readiness(date_from=date_to=<day>)`.
   - `missing_zoom_reports` identifies calls with transcript but no analytical report.
   - `ready_for_owner_daily` stays false until missing Zoom reports are closed.
3. List the day’s Zoom calls with `list_zoom_calls(date_from,date_to)` to confirm:
   - `analytical_note` empty/non-empty;
   - `transcript_segments_count`;
   - participants and start/end time.
4. Check Hermes cron jobs if a fallback automation is expected:
   - `albery-zoom-to-tasks-fallback` is a polling fallback, not an event trigger.
   - Its local script may poll on a schedule and may have cooldown/deduplication state.
5. If automation failed silently but the transcript is present, manually generate the report:
   - `get_report_contract(category_key="zoom_processing")`;
   - `get_zoom_call_transcript(call_id, include_full_text=true)`;
   - `get_org_structure(include_inactive=false)`;
   - build the report strictly from the current `zoom_processing` contract;
   - include `analysis.operational_tasks` and `analysis.leader_evaluations` when applicable;
   - save with `save_zoom_call_report`.
6. Verify after save:
   - `get_report_readiness` should show `missing_zoom_reports: []` for that call/day;
   - `list_pending_zoom_operational_dispatches` should include the call if operational tasks are ready and not yet dispatched;
   - `preview_zoom_operational_tasks(call_id)` shows exactly what will become Bitrix cards.
7. Never dispatch tasks without owner approval. After preview, tell Александр that he can answer `ставь` / `создавай`; only then use `dispatch_zoom_operational_tasks(confirm=true)`.

## Important pitfalls

- **Transcript exists != report exists.** Always check `analytical_note` or `missing_zoom_reports`.
- **Polling fallback != immediate event processing.** If the user expects instant processing, explain that the fallback checks periodically unless the production event handler is confirmed working.
- **Cooldown can hide repeat attempts.** A local watchdog may deduplicate the same missing call for a cooldown window. If you verify the transcript exists and the report is still missing, clear/retry only in a controlled recovery step and then verify with Albery tools.
- **Do not run long LLM report generation inside a short no-agent cron script.** Script-only watchdogs can time out while `hermes chat` is still generating the Zoom report. Keep the script fast: detect missing calls, start a guarded detached worker or hand work to an agent job, and write dedupe state only after successful report generation.
- **No silent Bitrix dispatch.** Report generation and task dispatch are separate; Bitrix task creation requires explicit owner confirmation.
- **Use the current contract.** The `zoom_processing` contract can change; always fetch it before rebuilding a report, especially because leader evaluations and operational task schemas are contract-dependent.
- **Preview may normalize tasks.** Compare your saved `operational_tasks` with `preview_zoom_operational_tasks`; the preview is the exact Bitrix-card view the owner cares about.
- **The call host must not receive a personal participant card in combined dispatch.** Albery’s combined Zoom dispatch intentionally creates one operational lead card for the meeting host/leader plus personal cards for non-host participants. If the host is also listed in `people.actual_participants`, exclude the resolved host Bitrix user id from `build_zoom_participant_reports_dispatch` before card creation; otherwise the host receives two “Итоги созвона” tasks. Cover this with `tests/unit/test_zoom_participant_reports.py`: preview should contain `operational` for the host and `participant_report` only for non-host participants.
