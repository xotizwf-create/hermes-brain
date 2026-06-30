# Albery Bitrix REST dispatch troubleshooting

Use this as a concise case note for Albery Zoom → Bitrix task dispatch failures.

## Symptom A — MCP timeout / possible duplicate risk

- `dispatch_zoom_operational_tasks(confirm=true)` times out at the MCP client layer (120s).
- `list_pending_zoom_operational_dispatches` still shows the same calls.
- `search_tasks(query="Итоги созвона", date_from=..., date_to=...)` returns no created tasks.

## Safe triage pattern

1. Do **not** retry blindly after a timeout.
2. First verify whether side effects happened:
   - pending queue still contains the call?
   - Bitrix search has tasks titled `Итоги созвона` for the date?
3. If no tasks were created and the call is still pending, inspect the production app logs around the attempt, redacting URLs/tokens/secrets.
4. For Albery, `journalctl -u albery --since ...` can reveal the real internal error even when the MCP client only reports a timeout.

## Known durable error class — Bitrix REST denied

Bitrix may return:

```text
RuntimeError: tasks.task.add: HTTP 401 {"error":"ACCESS_DENIED","error_description":"REST is available only by subscription."}
```

This means task creation reached Bitrix, but Bitrix rejected REST access because the portal tariff/subscription does not allow REST. This is not a prompt/report formatting issue and not a recipient-matching issue.

## Symptom B — report exists but dispatch cannot build cards

A Zoom call can have a visible `analytical_note` / report text while dispatch still fails before Bitrix. The durable pattern is: the human report was saved, but `raw_json.ai_report` is absent, truncated, or missing fields used by dispatch (`dispatch_summary`, `leader_evaluations`, `operational_tasks`, participants/people). In that case preview/dispatch may report that mapped participants/tasks/summary/evaluations are missing, or it may fall back to parsing text and produce noisy tasks.

Triage:

1. Confirm the user’s correction first: if they say the call is correct, stop chasing “wrong call” and inspect report generation + task dispatch inside that exact `zoom_call_id`.
2. Load the concrete call and compare:
   - `analytical_note` length and headings;
   - `raw_json->'ai_report'` presence;
   - `raw_json.ai_report.analysis` has full contract fields, not a short summary object;
   - `zoom_call_operational_tasks(call)` / `preview_zoom_operational_tasks(call_id)` task count and recipients.
3. If an automated Hermes/cron processing run is active for the same `zoom_call_id`, treat it as a race: it can overwrite the report while you are debugging. Check processes for the call id and re-read the DB after any restart/reset before reporting final state.
4. Do not create Bitrix tasks until `preview_zoom_operational_tasks` shows the exact intended recipients and task count.

## Text-parser pitfall — section boundaries

For fallback parsing, Albery extracts everything after section `4. Операционные задачи` until a recognized next heading. If the report contains an unrecognized heading such as `Открытые вопросы`, the parser can turn it and its bullets into fake tasks.

Durable fix pattern:

- Make the report heading numbered/readable if needed (`5. Открытые вопросы`), but do not rely on formatting alone.
- Harden `extract_zoom_operational_tasks_section()` so stop-heading regex includes the new heading class, e.g. `Открытые` alongside `Риски`, `Рекомендации`, etc.
- Verify with real app helpers after restart:
  - `zoom_call_operational_tasks(call)` returns only real tasks;
  - `preview_zoom_operational_tasks(call_id)` returns expected recipients/cards/task counts;
  - service is active after restart;
  - the fix is committed to the GitHub repo, not only patched live.

## Participant report dispatch is a separate lane

Albery now has two Zoom → Bitrix task dispatch flows that must stay independent:

- **Operational/leader tasks**: tasks for the call leader/manager to put work into motion. This uses the existing operational-task preview/dispatch and its own dispatched flag.
- **Participant reports**: per-participant task-style reports with shared call conclusions plus a personal evaluation. If there are no real issues, the report should praise the participant and use `10/10`; if performance was very poor, phrase it softly and constructively rather than demotivating the employee.

Implementation/verification pattern:

1. Keep separate preview and dispatch endpoints/UI state for participant reports; do not overload operational task dispatch.
2. Preview before sending and inspect recipient/card counts. Never create Bitrix tasks until the preview shows the intended participants and text shape.
3. Use a separate persisted status/flag for participant reports so sending them does not mark operational tasks as sent, and vice versa.
4. After a frontend change, rebuild the Vite `dist/` bundle and verify the generated asset contains a marker such as `Персональные итоги участникам` or the visible participant-report button text.
5. On production, a `401 Authentication required` from an API preview route can be an expected auth gate, not a broken route; pair it with service-active/log checks and UI/static asset verification.

## Git/prod sync note

Albery production may contain useful local commits that were not pushed. Before aligning prod with `origin/main`, inspect `git log --left-right --cherry-pick HEAD...origin/main`. If an ahead commit is relevant (for example deadline parsing for `create_bitrix_task`), port/push it instead of discarding it with `reset --hard`.

## User-facing explanation

Say plainly which layer failed:

- **Before Bitrix**: dispatch could not build a valid card from the saved report/JSON; no Bitrix request was made.
- **At Bitrix**: Bitrix rejected `tasks.task.add` (for example REST subscription/access).
- **Parser noise**: open questions or other report headings were accidentally parsed as tasks; fixed by section-boundary hardening.

Avoid dumping webhook URLs, path tokens, `.env` values, raw JSON, or full command output.
