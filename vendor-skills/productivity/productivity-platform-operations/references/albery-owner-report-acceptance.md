# Albery owner-report acceptance workflow

Use when preparing an owner-facing daily/weekly report for Albery from operational meetings, Google Sheets, Zoom reports/transcripts, Bitrix tasks, and prior owner reports.

## Core pattern

1. Start with Albery live AI instructions and the context guide for the report type.
2. Check report readiness for the full period before deepening. If a daily source is missing, label the report as early/manual rather than pretending the chain is complete.
3. Gather the three evidence layers:
   - saved owner daily/weekly reports for continuity and repeated risks;
   - Zoom call report/transcript for what people actually said;
   - Google Sheet rows for what was finally recorded as tasks/results/artifacts.
4. Compare the layers explicitly:
   - `meeting said` — what was discussed, blockers, commitments, exact owners;
   - `sheet says` — task text, weight, result/status, artifact link/text;
   - `owner decision` — accept / partially accept / do not accept.
5. Save the generated owner weekly/daily report with raw_input noting manual/early inputs when used.

## Acceptance rules

- Accept only when the task is completed, the blocking decision is closed, and the artifact is present or clearly identified.
- Partial accept when the work progressed but a blocker remains, only part of the scope is done, or the artifact proves preparation rather than final result.
- Do not accept as complete when the sheet says “Выполнено” but the transcript says the decision is pending, the owner has not decided, or the next step is still required.
- Treat `Выполнено` in a sheet as a claim to verify, not as source-of-truth by itself.

## Reporting style for the owner

Use direct management language, not a generic recap:

- “Принимать” — items the owner can count as done.
- “Не принимать полностью” / “частично” — items with open blockers or weak proof.
- “Несостыковки” — where the meeting, sheet, and artifacts disagree.
- “Что сделать сейчас” — owner actions and control points.

For short upcoming weeks, require internal control dates (Mon/Tue/Wed/Thu), not only a week-level deadline.

## Expanding reports with regulations / matrix / feedback

When the owner asks to “расширить/пересобрать отчёт” using MCP instructions, регламент, матрицу решений, feedback, or similar governance context, do not merely rephrase the existing report. Add a separate governance layer while preserving the current person-specific findings.

Required extra evidence layers:

- `report contract / live AI instructions` — what the Albery MCP says this report type must check.
- `meeting rhythm / регламент встреч` — which meeting type the call corresponds to, required time/duration/participants/agenda/result.
- `decision matrix` — who initiates, verifies, approves, and executes each task/decision.
- `task/result regulations` — whether each task has action/result, owner, deadline, expected artifact, result format, status, deviation, and needed decision.
- `recommendation feedback` — prior human feedback on recommendations, especially signals that a recommendation was based on wrong context or lacked a clear expected artifact.

Output pattern:

1. Keep the existing conclusions for each named person intact; explicitly say they are preserved.
2. Add “Сверка с регламентом встреч”: identify the closest meeting type and list mismatches (time, duration, missing decision maker, participants not using full names, incomplete agenda, missing decision/result list).
3. Add “Сверка с матрицей решений”: for each task, separate the person’s action from Evgeniy/owner approval, verification by another manager, and execution by subordinates. Do not blame an executor for a missing owner decision.
4. Add “Сверка с регламентом постановки/фиксации задач”: flag empty artifacts, missing dates, unclear result criteria, and sheet statuses unsupported by evidence.
5. Add “Обратная связь”: if prior recommendation feedback said context was wrong or a protocol/recommendation was unclear, convert that into stricter requirements for source links, role, expected artifact, and acceptance criteria.
6. Save the updated report version if the workflow/tool supports saving; mention the new version/id in the user response.

## Albery-specific pitfalls observed

- Administrative/legal work can be marked complete in the sheet while still blocked by Evgeniy’s decision on contract format. Call this `частично / заблокировано`, not `выполнено`.
- Artur’s operational tasks often have stronger artifacts (Docs/Sheets/Bitrix links); Natalia’s commercial/admin rows may contain text or a report name instead of a direct link. Flag uneven artifact quality.
- If a Friday leadership meeting is short or missing Evgeniy, say which decisions could not be closed because the decision maker was absent.
- Additional sheet tasks that were not discussed in the Friday meeting should be called out as “added in sheet, not discussed in this meeting” rather than silently treated as agreed.
