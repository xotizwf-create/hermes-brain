# Google Sheets formula mastery

Use this reference before creating or fixing formulas in Google Sheets, especially when the owner complained about formula errors.

## Source hierarchy

1. Google Docs Editors Help is the source of truth for function syntax and edge cases:
   - function list: https://support.google.com/docs/table/25273
   - QUERY: https://support.google.com/docs/answer/3093343
   - FILTER: https://support.google.com/docs/answer/3093197
   - ARRAYFORMULA: https://support.google.com/docs/answer/3093275
   - VLOOKUP: https://support.google.com/docs/answer/3093318
   - XLOOKUP: https://support.google.com/docs/answer/12405947
   - IMPORTRANGE: https://support.google.com/docs/answer/3093340
2. Practical deep dives are secondary; use them for patterns, not as authority:
   - Ben Collins QUERY guide: https://www.benlcollins.com/spreadsheets/google-sheets-query-sql/

## Non-negotiable formula discipline

Before writing formulas:

1. Determine the spreadsheet locale.
   - Russian locale usually needs `;` as argument separator.
   - Array literals use `\` for columns and `;` for rows in Russian-locale sheets.
   - Do not mix English formula names with localized separators blindly; verify with readback.
2. Identify data types for every source column: date, number, text, boolean.
3. Prefer simple auditable blocks over one clever formula.
4. Use finite ranges for dashboard outputs and chart sources when possible.
5. Only use whole-column ranges when the formula is stable and performance is acceptable.

## Function-specific rules

### QUERY

Google states that each QUERY column can hold only one dominant data type; minority types are treated as null. Therefore:

- normalize numbers and dates before QUERY;
- do not QUERY a column where numbers and text placeholders are mixed;
- pass the `headers` argument deliberately when the source has or lacks headers;
- keep the query string small enough to inspect;
- do not hide QUERY failures behind `IFERROR` until the raw result was verified.

### FILTER

FILTER conditions must match the shape of the filtered range.

- Row filters: condition height must match range height.
- Column filters: condition width must match range width.
- Do not mix row and column conditions in the same FILTER.
- For empty results, wrap only the final user-facing formula with `IFERROR`, then test a case that should return rows.

### ARRAYFORMULA

ARRAYFORMULA works only when all referenced ranges have compatible shapes.

- Use explicit blank guards: `IF(A2:A=""; ; ...)`.
- Do not put array output where it can collide with existing values.
- Avoid open-ended array formulas in heavily edited sheets unless needed.
- If an array formula fills KPI or chart data, read back at least several output rows.

### Lookups

Prefer XLOOKUP when available because lookup range and result range are explicit.

For VLOOKUP:

- use exact match unless sorted approximate match is intentionally required;
- ensure the lookup key is in the first column of the lookup range;
- do not hard-code column indexes when the table may change; prefer XLOOKUP or INDEX/MATCH.

### IMPORTRANGE

IMPORTRANGE may require manual access approval.

- Write the formula, then read back the value.
- If it returns an authorization placeholder, tell the owner that Google needs access approval.
- Do not claim imported data is live until actual imported rows are visible.

## Formula QA loop

Every Google Sheets formula task must end with this loop:

1. Read formulas back with `valueRenderOption=FORMULA`.
2. Read displayed values back with normal rendering.
3. Search key ranges for formula errors:
   - `#ERROR!`, `#N/A`, `#VALUE!`, `#REF!`, `#DIV/0!`, `#NAME?`, `#NUM!`.
4. Verify at least one positive test case and one empty/edge case.
5. For totals, independently recompute from source rows and compare.
6. For charts, verify the source range contains real numeric series, not placeholders.
7. Only report success after the readback is clean.

## Owner-specific preference

Alexander prefers the simplest reliable spreadsheet solution. Use complex formulas only when they reduce real maintenance risk. If a helper column makes the spreadsheet easier to audit, use the helper column.
