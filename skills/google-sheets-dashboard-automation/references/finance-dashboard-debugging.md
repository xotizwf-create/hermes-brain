# Finance dashboard debugging notes

Use this reference when fixing a Google Sheets income/expense dashboard where charts exist but show `Нет данных`, odd near-zero axes, or misleading KPI formats.

## Symptom pattern

- The chart object exists, has a title and legend, but renders `Нет данных`.
- Axis labels may show tiny values around `0 ₽` / `1 ₽` because the source table has no usable numeric rows.
- The underlying summary block may display a placeholder such as `Нет данных` even though source operations exist.

## Durable root cause

Do not assume the chart is broken. Usually the chart is faithfully rendering a broken or empty source range. The common durable failure mode is a large spill formula that combines `QUERY`, array literals, `IF`, and `IFERROR`; the `IFERROR` masks the real formula/range/locale problem and feeds the chart a placeholder row instead of month/category numeric data.

## Fix pattern

1. Inspect the chart's source table, not just the embedded chart object.
2. Replace the giant spill with small auditable blocks:
   - label list, e.g. month/category;
   - `SUMIFS` income/expense/value columns;
   - separate balance/share columns.
3. Use finite dashboard ranges for charts, e.g. `G8:J24`, rather than unbounded ambiguous ranges.
4. Format by semantic meaning:
   - money as ₽;
   - counts as plain numbers;
   - shares as percent;
   - dates/month labels as text/date.
5. Verify the exact broken block shown in the user's screenshot.

## Verification assertions

Before reporting success, read back the dashboard table and assert:

- no formula error strings (`#ERROR!`, `#N/A`, `#VALUE!`, etc.);
- each chart source table contains at least one non-placeholder row;
- each series column used by the chart contains numeric values;
- KPI count cells are not formatted as currency;
- category share columns are not accidentally all zero;
- top category/summary KPI points to the first sorted summary row, not a hard-coded unrelated row.

A good readback for the June 2026 test finance dashboard looked like:

```json
{
  "monthly_rows": [["2026-06", 102000, 112300, -10300]],
  "operation_count": 8,
  "top_category": "Возвраты",
  "errors": []
}
```

This reference is intentionally about the debugging pattern, not that specific sheet ID.