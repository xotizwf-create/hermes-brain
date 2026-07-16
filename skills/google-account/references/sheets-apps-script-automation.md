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

## Bound Apps Script automation — the robust pattern (and the `scripts.run` 404 trap)

Hard-won from the Albery «автоматизация заказа» task (2026-07-16), where the running agent
looped for ~2 hours creating buggy scripts. The failure mode and the correct pattern:

**Never try to *execute* a container-bound script over the API to do setup or "press the button".**
`scripts.run` (Apps Script Execution API) returns `404 "Requested entity was not found"` for a
normal bound/standalone script, because it requires (a) the script and the calling OAuth client to
share the **same** Google Cloud project, and (b) an **API-executable deployment**
(`deployments.create` with an `EXECUTION_API` entry point). A freshly created script has neither, so
every "запусти функцию через API" attempt 404s. The agent misread this as a Google outage and kept
retrying — the single biggest time sink. **`projects.create` / `projects.updateContent` /
`projects.getContent` work fine** (create + edit + read content); only *running* a function does not.

Correct pattern — do the work two ways, both of which avoid `scripts.run`:

1. **Setup, computation, and verification go through the Sheets API, in your own code** — read the
   source with `values.get(valueRenderOption=UNFORMATTED_VALUE)`, compute the result in
   Python/JS on the server, write it with `values.update` + `batchUpdate` formatting. This is what
   the owner actually sees, and you can read it back and assert it. Do NOT depend on the script
   running to populate the sheet.
2. **The recurring "button" is a client-side simple trigger, deployed as content only:**
   - Create **one** container-bound project: `script.projects.create(body={title, parentId=<spreadsheetId>})`,
     then `projects.updateContent` with `Code` (`SERVER_JS`) + `appsscript` (`JSON`). Confirm binding
     with `projects.get(scriptId).parentId == spreadsheetId`.
   - `onOpen(e)` builds a custom menu (`SpreadsheetApp.getUi().createMenu(...)`) — appears when the
     owner **reloads** the spreadsheet. `onEdit(e)` watches a **checkbox cell** (data-validation
     BOOLEAN): when ticked → run the compute function → untick. Both are **simple triggers**: they
     fire client-side, need **no** `scripts.run`, and (onEdit) need **no** owner authorization to
     read/write the same spreadsheet. A menu item run prompts the normal one-time Google consent.
   - You **cannot** create a drawing-image "button" bound to a macro via API (that assignment is
     UI-only). The checkbox-cell + `onEdit`, or the `onOpen` menu, is the API-createable button.
   - The compute function must be **self-contained**: `SpreadsheetApp.getActiveSpreadsheet()` only.
     No `openById` to another file, no hard-coded spreadsheet IDs, no `Range.copyTo` across files
     (Google forbids cross-spreadsheet `copyTo` → "Target range and source range must be on the same
     spreadsheet"). Mirror source tabs into the working file (values), then compute within one file.

**Verify before claiming success — a script you cannot run is not "проверено".** Compute the same
result in your own code, write it, read it back with the API, and assert against a **known example
from the dialogue** (Albery: SKU 969588068, 16.06–20.07 → June `488160/1357/360/23`, July
`656129/1357/483/25`). Never reply "исправил и перепроверил, работает" for a bound script whose
functions you never executed — that is false-success and the owner will catch it immediately.

**Parse messy tabular sources by header rows, not by a fixed column stride.** The Albery plan sheet
had month blocks that were *mostly* 4 columns wide but some only 3 (missing «план в день»). A fixed
`+4` stride silently read the next month's value into the wrong field (per-day showed `3 000 000`).
Robust approach: walk columns, use the **sub-header row** (e.g. «план, руб» marks a block start) plus
the **label row** (e.g. «ИЮНЬ 2026») to map each month → {metric: column}; skip metrics whose column
is absent instead of assuming it exists. Treat empty source cells as empty output, not zero.

**Identity / "нет доступа" is usually a wrong ID, not a real permission problem.** The agent's Google
account is `a9ent.ai@gmail.com`; files it creates are owned by it (full access). When a run reports
«таблица не найдена / нет доступа», first suspect a **hallucinated or OCR-mangled spreadsheet ID**
(the agent had drifted onto `1BZmBrEyLHP8...`, a nonexistent file, and onto a script with different
tab names). Re-derive the real ID from the owner's message/link before asking the owner to grant
access. One stable bound script per spreadsheet; do not spawn a new script project every turn (the
agent left three orphan projects `19k844ci…`, `1OEB2sh4…`, `1zFAfw9Sj…`).

## Pitfalls
- Apps Script has two switches: the Apps Script API user setting at `script.google.com/home/usersettings` and the Google Cloud API `script.googleapis.com` for the OAuth project. If REST calls return `SERVICE_DISABLED`, enable `script.googleapis.com` in Cloud Console for the project; the user-setting toggle alone is insufficient.
- Windows OAuth bundles should always include a manual command fallback (`py -3 authorize_google_full_access.py` from an ASCII path such as `C:\google-auth`) because `.bat` files can break with Cyrillic paths, spaces, BOM/codepage issues, or mangled quoting.
- Treat spreadsheet formulas as untrusted until read back. Locale/range mistakes can silently create `#ERROR!` cells even though the API update succeeded.
- `IMPORTRANGE` mirrors need a one-time manual «Разрешить доступ» and show `#REF!` until then — fine for a human-owned link, but do **not** build a computation on top of an unauthorized IMPORTRANGE and call it done. For a self-contained automation, prefer copying source values into the working file so the button's math never depends on a pending cross-file authorization.
