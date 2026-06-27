# Screenshot-matched finance templates — lessons from a failed first pass

Use this note when recreating a Google Sheets finance dashboard from screenshots and the owner expects “1 в 1”.

## What went wrong

A sheet can pass mechanical checks — correct formulas, dropdowns, chart object exists, totals match — while still being unacceptable because the visual layout is wrong. In this session, the donut chart was too large and overlapped the expense category list; the block widths/heights and borders did not match the screenshot, even though API verification returned valid formulas and chart data.

## Better workflow

1. Build the normalized data sheet and dashboard formulas.
2. Add dropdowns and date validation.
3. Add chart only after source ranges contain non-zero numeric values.
4. Do a visual QA pass before delivering:
   - inspect a screenshot/browser render of the sheet;
   - compare grid positions and block proportions to the reference screenshot;
   - ensure charts sit inside their intended framed cards and do not cover category rows;
   - check that empty chart/table areas have the same gray header bands, borders, and spacing as the reference.
5. Then run mechanical verification:
   - no formula errors;
   - selected-period totals match independent recomputation;
   - dropdown validations are present;
   - chart count and source ranges are correct;
   - export/open check if a downloadable copy matters.

## Practical Google Sheets API pattern

For overlay charts, verify and tune these fields, not just the chart source:

```json
{
  "overlayPosition": {
    "anchorCell": {"rowIndex": 10, "columnIndex": 5},
    "offsetXPixels": 2,
    "offsetYPixels": 4,
    "widthPixels": 375,
    "heightPixels": 188
  }
}
```

If a category list starts at row 19, keep the chart container above it (for example rows 11–18) and keep `heightPixels` low enough that it does not overlap the list. Re-run a visual inspection after resizing.
