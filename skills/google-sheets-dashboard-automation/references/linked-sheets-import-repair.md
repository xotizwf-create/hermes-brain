# Linked Google Sheets import repair

Use when a spreadsheet pair is connected with `IMPORTRANGE` and the owner asks to audit/fix broken formulas or dashboards.

## Durable lesson

`IMPORTRANGE` can be syntactically correct yet still display an authorization error until Google receives a manual **Allow access / Разрешить доступ** click. If the owner asked for a working deliverable now, do not leave the report visibly broken with an error cell and call it done.

## Repair pattern

1. Read the source table directly through the Sheets API and compute source-of-truth totals independently.
2. Read the report with both `valueRenderOption=FORMULA` and displayed values.
3. Scan user-facing ranges for formula errors: `#ERROR!`, `#N/A`, `#VALUE!`, `#REF!`, `#DIV/0!`, `#NAME?`, `#NUM!`.
4. If `IMPORTRANGE` is blocked by manual Google authorization:
   - keep a clear source link and explanation in the import sheet;
   - add a verified imported snapshot below, written from the source through the API;
   - point report formulas and charts at that verified snapshot so the report opens cleanly;
   - state plainly that the sheet is no longer relying on unresolved manual authorization for the visible report.
5. Avoid putting literal error tokens like `#REF!` in explanatory notes inside scanned ranges; the QA scanner should remain strict and return zero visible error tokens.
6. Rebuild charts only after computing the final block positions. Do not reuse old chart source ranges after inserting/removing rows.
7. Final verification must include:
   - no visible formula-error tokens in import/report ranges;
   - KPI formulas read back correctly;
   - KPI values match independent source totals;
   - chart source ranges contain numeric rows;
   - chart titles exist and point to intended blocks.

## Reporting

For the owner, summarize in plain Russian:

- what was broken (`IMPORTRANGE` required manual authorization, chart ranges stale, etc.);
- what was changed;
- exact verified values (rows, total, count, average);
- links to the source and repaired report.

Do not expose token paths or API internals.
