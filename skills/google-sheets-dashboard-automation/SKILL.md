---
name: google-sheets-dashboard-automation
description: Use when creating, editing, debugging, or beautifying Google Sheets dashboards, calculators, charts, formulas, validation, and bound Apps Script automations for the owner. Enforces readable layout, simple auditable formulas, and mechanical verification that charts have real numeric data.
---

# Skill: Google Sheets dashboard automation

Use this when the owner asks to create or fix a Google Sheet, calculator, dashboard, charts, formulas, dropdowns, formatting, or Apps Script menu/automation.

## First principles

1. **Use the API, not browser clicking.** Prefer Google Sheets API `spreadsheets.batchUpdate` + `spreadsheets.values.update` with `valueInputOption=USER_ENTERED`. For bound Apps Script use the Apps Script API. Credentials and scopes are documented in `skills/google-account/`. **Before building any button/menu automation, read `skills/google-account/references/sheets-apps-script-automation.md` → "Bound Apps Script automation — the robust pattern (and the `scripts.run` 404 trap)"**: never execute a bound script over the API (it 404s), deploy `onOpen`/`onEdit` simple triggers as content only, do the computation + verification yourself via the Sheets API, and assert against a known example before reporting success.
2. **Simple formulas beat clever formulas.** The owner prefers readable, stable spreadsheets. Avoid one huge `IFERROR(QUERY({ ... }))` formula that builds the whole dashboard at once. Split logic into understandable helper blocks/columns.
3. **Design is part of correctness.** Dashboards must be visually scannable: KPI cards, clear section headers, divider bands/lines, framed table zones, framed chart zones, consistent colors and spacing.
4. **Charts are not verified by existence.** A chart object can exist and still show `Нет данных`. Always verify the chart source range contains non-empty numeric rows.
5. **A raw grid is not a finished deliverable.** Even a simple task/list table needs a readable header, frozen top row when useful, borders, wrapping, sensible widths, alternating/status colors, and number/date/currency formats that match the meaning.

## Recommended build workflow

1. Identify or create the main data sheet with normalized columns. For finance calculators use:
   - `Операции`: `Дата`, `Тип`, `Категория`, `Счёт/карта`, `Сумма`, `Комментарий`, `Месяц`.
   - `Дашборд`: period selectors, KPI cards, summary tables, chart zones, recent operations.
2. Add validations early:
   - date column as dates;
   - type dropdown (`Доход`, `Расход`);
   - category/account dropdowns;
   - amount as positive currency number.
3. Add helper columns with explicit names, e.g. `Месяц = ARRAYFORMULA(IF(A2:A="";"";TEXT(A2:A;"yyyy-mm")))`.
4. Build summary blocks as small formulas:
   - one formula to produce category/month labels;
   - separate `SUMIFS`/share formulas for values;
   - separate balance column (`Доход - Расход`).
5. Add charts only after their source tables are populated and formatted.
6. Add Apps Script `onOpen()` menu for owner-friendly actions when useful: current month, add row, clear demo data, refresh dashboard.
7. Run mechanical verification before reporting success.

## References

- `references/finance-dashboard-debugging.md` — concrete debugging pattern for income/expense dashboards where a chart exists but shows `Нет данных`, including source-table fixes and verification assertions.
- `references/formula-mastery.md` — mandatory formula discipline: official Google syntax sources, locale rules, QUERY/FILTER/ARRAYFORMULA/XLOOKUP/IMPORTRANGE pitfalls, and readback QA loop.
- `references/linked-sheets-import-repair.md` — repair pattern for linked spreadsheets when `IMPORTRANGE` is syntactically correct but blocked by Google’s manual access approval; includes snapshot fallback, strict error scanning, and chart-range rebuild checks.
- `references/screenshot-matched-finance-template.md` — lesson from recreating a finance template from screenshots: visual QA is required in addition to formula/chart API checks, especially for overlay chart sizing and block alignment.
- `references/one-to-one-sheet-cloning.md` — pattern for cloning an existing polished Sheet 1:1 with Drive `files.copy`, inspecting formulas/style/validations via `includeGridData`, setting access, and verifying the copy before reporting.

## Formula rules that prevent broken dashboards

Before writing or fixing non-trivial formulas, load `references/formula-mastery.md` and follow its QA loop. Do not rely on memory or visual inspection for formula correctness: write the formula, read formulas back, read displayed values back, scan for formula errors, and independently recompute key totals from source rows before reporting success.


### Avoid this pattern

Do **not** rely on a single large spill formula like:

```text
IFERROR(QUERY({range1\IF(...)\IF(...)}; ...); {"Нет данных"\0\0\0})
```

It is hard to debug and can hide real formula/range/locale failures behind `Нет данных`, causing charts to exist but render empty.

### Prefer this pattern for monthly finance charts

Use a finite, readable dashboard table, for example `G8:J24`:

- `G8:J8`: `Месяц | Доход | Расход | Баланс`
- `G9`: month list formula, filtered by dashboard dates.
- `H9`: `ARRAYFORMULA` + `SUMIFS` for income by month.
- `I9`: `ARRAYFORMULA` + `SUMIFS` for expense by month.
- `J9`: `ARRAYFORMULA(H - I)`.

Example formulas for Russian-locale Sheets:

```text
G9 = IFERROR(SORT(UNIQUE(FILTER('Операции'!G2:G;'Операции'!G2:G<>"";'Операции'!A2:A>=$B$2;'Операции'!A2:A<=$D$2)));"Нет данных")
H9 = ARRAYFORMULA(IF($G$9:$G$24=""; ; IF($G$9:$G$24="Нет данных"; 0; SUMIFS('Операции'!$E:$E;'Операции'!$G:$G;$G$9:$G$24;'Операции'!$B:$B;"Доход";'Операции'!$A:$A;">="&$B$2;'Операции'!$A:$A;"<="&$D$2))))
I9 = ARRAYFORMULA(IF($G$9:$G$24=""; ; IF($G$9:$G$24="Нет данных"; 0; SUMIFS('Операции'!$E:$E;'Операции'!$G:$G;$G$9:$G$24;'Операции'!$B:$B;"Расход";'Операции'!$A:$A;">="&$B$2;'Операции'!$A:$A;"<="&$D$2))))
J9 = ARRAYFORMULA(IF($G$9:$G$24=""; ; $H$9:$H$24-$I$9:$I$24))
```

For category shares, do not calculate the share inside the same `QUERY` spill if it only fills the first row. Use a separate share column:

```text
C9 = ARRAYFORMULA(IF($A$9:$A$24=""; ; IF($A$9:$A$24="Нет расходов"; 0; $B$9:$B$24/$H$4)))
F9 = ARRAYFORMULA(IF($D$9:$D$24=""; ; IF($D$9:$D$24="Нет доходов"; 0; $E$9:$E$24/$E$4)))
```

## Visual design checklist

Before saying a dashboard or task/list table is ready, check that it has:

- large title and clear period controls;
- KPI cards with visible borders/backgrounds;
- separate colors for income, expense, balance, neutral labels;
- thick/clear dividers between major sections;
- table blocks with header bands and borders;
- chart cards with visible frames/backgrounds, not floating charts on raw grid;
- frozen header or enough spacing so the sheet does not look like one merged blob;
- number formats that match meaning: counts are plain numbers, money is ₽, shares are %, dates are dates.

### Screenshot-matching / “1 в 1” visual QA

When the owner asks for a Sheet to look **1 в 1 like screenshots**, formula/API readback is not enough. Treat visual similarity as a deliverable:

1. Re-open or screenshot the resulting sheet before reporting success, or otherwise inspect a visual render/export, not only API metadata.
2. Verify chart overlay positions and pixel sizes against the grid. A chart object can be mathematically correct but visually wrong if it overlaps the category list or floats outside its framed card.
3. Check the exact relative placement of blocks: top KPI row, selector, calendar box, income/expense titles, chart/table containers, and category lists below them.
4. If the owner sends a screenshot of the broken result, fix the visual layer first: widths, row heights, borders, fills, chart `overlayPosition`, and only then re-run formula checks.
5. Report “ready” only after both checks pass: visual layout inspection + semantic formula/chart-source verification.

For a simple generated task/list table, the minimum acceptable style is: contrast header band, bold readable header text, frozen header row when the list is longer than one screen, wrapped text, useful column widths, borders, alternating rows, and status/deadline colors when the table contains tasks.

## Mechanical verification checklist

After every write or redesign, read data back through the Sheets API. Do not rely on visual intuition alone.

Minimum checks:

1. Key ranges have no formula errors (`#ERROR!`, `#N/A`, `#VALUE!`, etc.).
2. KPI values are semantically correct:
   - operation count is a number, not currency;
   - biggest expense and top category match the summary table;
   - income/expense/balance totals match the source data for selected dates.
3. Share columns are not accidentally zero except where mathematically zero.
4. Every chart source table has at least one non-placeholder row with numeric series values.
5. Chart specs point at the intended finite source ranges and have the intended titles/types.
6. If the owner sent a screenshot showing a broken area, verify the specific broken block, not just the whole sheet.

Example semantic test result to aim for before reporting:

```json
{
  "ok": true,
  "errors": [],
  "monthly_rows": [["2026-06", 102000, 112300, -10300]],
  "operation_count": 8,
  "top_category": "Возвраты"
}
```

## One-to-one clones from an existing polished Sheet

When the owner sends a Google Sheet as a style/formula reference and asks for the same level of polish or a file “1 в 1”, do not start by manually recreating every style. First inspect the source, then use Drive `files.copy` for a true clone unless the owner explicitly wants a redesigned derivative. Load `references/one-to-one-sheet-cloning.md` for the exact inspection, copy, permission, and verification pattern. This preserves formulas, dropdowns, formats, frozen rows, widths, and hidden/helper metadata better than hand-built `batchUpdate` recreation.

If the target spreadsheet must keep its URL but be restored from an original template, do not copy only the first tab and do not hand-redraw from screenshots. Inspect all source tabs, copy all relevant tabs with `sheets.copyTo`, restore the source tab names/order, then re-read formulas from the source with `valueRenderOption=FORMULA` and write them back after final names are set so references bind inside the target workbook. Load `references/google-sheets-original-template-restore.md` for the detailed workflow and verification checklist.

### When the reference is only a screenshot

A screenshot is not enough to reliably reconstruct a polished Google Sheet by hand. Do **not** keep making blind visual edits against the live file after the owner says the result is wrong.

Use this safer sequence:

1. **Stop editing the live sheet** and acknowledge the specific breakage plainly.
2. Ask for the best available reference, in this order:
   - original/working Google Sheet or template link;
   - Drive/XLSX copy of the correct version;
   - full un-cropped screenshot at 100% zoom with row/column headers visible.
3. Clarify whether the target is **exactly like the screenshot** or a **new clean redesign**.
4. Work in a duplicate/candidate copy first; only replace/update the owner’s working file after visual approval or clear instruction.
5. If recreating from screenshot is unavoidable, treat the screenshot as approximate: match layout zones, but avoid claiming “1 в 1” unless verified visually from an actual rendered file.

Pitfalls from prior failures:

- Do not write visible currency strings like `"35 511,58 ₽"` into chart source cells and expect charts to treat them as numeric. Keep chart source ranges numeric and apply number formats separately.
- For pie/donut charts, verify the selected series range is the numeric amount column; the Google Sheets error “Столбец 2 должен содержать числовые данные” means the chart is pointing at labels/text or text-formatted money.
- API readback of values, chart count, and anchor position is not sufficient visual QA. If the user complains about visual fidelity, obtain a real reference/copy or produce a rendered preview/screenshot before reporting success.

## Common pitfalls

- When creating spreadsheets through the API, never assume a new sheet's `sheetId` is `0`. Read `spreadsheets.get(..., fields='sheets.properties')` after creation and use the actual `sheetId` for formatting, filters, charts, and frozen rows. A wrong guessed id causes `Invalid requests[].repeatCell: No grid with id: 0`.
- `IMPORTRANGE` links can be written by API, but the first connection between two spreadsheets may still require **Allow access / Разрешить доступ** in the destination sheet. Treat that as a normal Google Sheets authorization step: add a clear note in the sheet, verify the formula is present with `valueRenderOption=FORMULA`, and do not claim imported dashboard values are live until readback shows non-zero/non-placeholder imported rows. If the owner asks to fix the sheet so it opens cleanly now, do not leave a visible error cell: use the linked-sheets import repair pattern and point the report at a verified API-written snapshot while keeping the source link/explanation visible.
- Google Sheets locale: Russian spreadsheets use semicolons `;` between function arguments and backslashes `\\` between horizontal array columns.
- `IFERROR(...; "Нет данных")` is acceptable for user-facing fallback, but never let it hide test failures. Read the underlying output and assert expected numeric rows.
- A chart with a valid title and legend can still be broken if the source range is a placeholder row like `Нет данных | 0 | 0 | 0`.
- Applying one currency format to a wide KPI block can turn counts into `8 ₽`. Format each KPI value by meaning.
- `INDEX(summary_range; row)` for “top category” should point at the first sorted summary row, not a hard-coded later row.
- After visual-only changes, still re-run formula/chart verification because formatting scripts can accidentally clear spills or overwrite ranges.

## Reporting to the owner

Report briefly in Russian:

- what was broken in plain language;
- what was changed;
- what was verified with real readback;
- link to the spreadsheet if useful.

Do not expose token paths, API object names, raw secret files, or long technical traces unless the owner explicitly asks.
