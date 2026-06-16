# Google Sheets + Apps Script automation notes

Use this when the owner asks to build or modify a Google Sheet, add formulas, dashboards, charts, menus, or bound Apps Script.

## Proven workflow
1. Use the full-access OAuth token (`drive`, `spreadsheets`, `script.projects`, `script.deployments`) from the secure Google token paths; do not ask the owner to share each sheet manually.
2. For a non-trivial spreadsheet, prefer the Sheets API `spreadsheets.batchUpdate` + `spreadsheets.values.update` rather than browser editing:
   - create/rename sheets;
   - write header/data/formula grids with `valueInputOption=USER_ENTERED`;
   - add validation dropdowns (`setDataValidation` / `BooleanCondition` via API), formatting, frozen rows, widths, conditional formatting, filters;
   - add charts with `addChart` requests after formulas/tables exist.
3. For bound Apps Script, use the Apps Script API:
   - `projects.create(parentId=<spreadsheet_id>, title=...)` to create a bound project;
   - `projects.updateContent` with at least `Code` (`SERVER_JS`) and `appsscript` (`JSON`) files;
   - read back `projects.getContent` to verify the script exists.
4. Add a custom menu via Apps Script `onOpen()` for owner-friendly actions (for example: set current month, add an operation row, clear demo rows).
5. Verify the result mechanically before telling the owner it works:
   - read key formula cells back via `spreadsheets.values.batchGet`;
   - inspect chart objects via `spreadsheets.get(..., includeGridData=false)` and confirm expected chart titles/counts;
   - for every chart, verify the source table has non-placeholder rows with numeric values (a chart can exist and still show `Нет данных`);
   - if readback contains `#ERROR!`, fix formulas/locale/ranges and re-read before reporting success.

## Budget / income-expense calculator pattern
Useful default structure for a personal finance sheet:

- `Операции`: дата, тип (`Доход`/`Расход`), категория, счёт/карта, сумма, комментарий, месяц.
- `Дашборд`: period selectors (`с`/`по`), total remaining, income for period, expense for period, net result, average daily expense, operations count, category summaries, monthly dynamics, recent operations.
- Add dropdowns for type/category/account, green/red conditional formatting for income/expense, frozen header and a filter.
- Add charts only after the summary ranges are populated: pie/donut for expenses by category, column/line chart for income vs expense by month.

## Dashboard visual design checklist
When building or revising a Google Sheets dashboard, do not stop at technically correct tables/charts. The owner notices legibility and wants the eye to have clear anchors:

- Separate major blocks with visible structure: thick KPI card borders, section header bands, muted horizontal divider rows, and framed table/chart zones.
- Make section titles read as sections, not random filled cells: merge/size title rows where helpful, use stronger typography, and keep consistent spacing above/below each block.
- Treat charts as cards: put them inside bordered/background zones instead of leaving them floating in empty grid space.
- Add a clear divider between tabular summaries and chart areas when both are on one dashboard.
- After visual changes, still verify formulas and charts mechanically (`values.batchGet` for key cells and `spreadsheets.get` for chart titles/counts) before reporting success.

## Pitfalls
- Apps Script has two switches: the Apps Script API user setting at `script.google.com/home/usersettings` and the Google Cloud API `script.googleapis.com` for the OAuth project. If REST calls return `SERVICE_DISABLED`, enable `script.googleapis.com` in Cloud Console for the project; the user-setting toggle alone is insufficient.
- Windows OAuth bundles should always include a manual command fallback (`py -3 authorize_google_full_access.py` from an ASCII path such as `C:\google-auth`) because `.bat` files can break with Cyrillic paths, spaces, BOM/codepage issues, or mangled quoting.
- Treat spreadsheet formulas as untrusted until read back. Locale/range mistakes can silently create `#ERROR!` cells even though the API update succeeded.
