---
name: google-sheets-dashboard-automation
description: Use when creating, editing, debugging, or beautifying Google Sheets dashboards, calculators, charts, formulas, validation, and bound Apps Script automations for the owner. Enforces readable layout, simple auditable formulas, and mechanical verification that charts have real numeric data.
---

# Skill: Google Sheets dashboard automation

Use this when the owner asks to create or fix a Google Sheet, calculator, dashboard, charts, formulas, dropdowns, formatting, or Apps Script menu/automation.

## First principles

1. **Use the API, not browser clicking.** Prefer Google Sheets API `spreadsheets.batchUpdate` + `spreadsheets.values.update` with `valueInputOption=USER_ENTERED`. For bound Apps Script use the Apps Script API. Credentials and scopes are documented in `skills/google-account/`.
2. **Simple formulas beat clever formulas.** The owner prefers readable, stable spreadsheets. Avoid one huge `IFERROR(QUERY({ ... }))` formula that builds the whole dashboard at once. Split logic into understandable helper blocks/columns.
3. **Design is part of correctness.** Dashboards must be visually scannable: KPI cards, clear section headers, divider bands/lines, framed table zones, framed chart zones, consistent colors and spacing.
4. **Charts are not verified by existence.** A chart object can exist and still show `Нет данных`. Always verify the chart source range contains non-empty numeric rows.

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

## Formula rules that prevent broken dashboards

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

Before saying a dashboard is ready, check that it has:

- large title and clear period controls;
- KPI cards with visible borders/backgrounds;
- separate colors for income, expense, balance, neutral labels;
- thick/clear dividers between major sections;
- table blocks with header bands and borders;
- chart cards with visible frames/backgrounds, not floating charts on raw grid;
- frozen header or enough spacing so the sheet does not look like one merged blob;
- number formats that match meaning: counts are plain numbers, money is ₽, shares are %, dates are dates.

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

## Common pitfalls

- Google Sheets locale: Russian spreadsheets use semicolons `;` between function arguments and backslashes `\` between horizontal array columns.
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
