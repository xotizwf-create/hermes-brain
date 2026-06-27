# Restoring a Google Sheet from an original template

Use this when the owner gives an original Google Sheet after a failed manual recreation and asks to make another sheet look exactly like it.

## Lesson

Do **not** keep guessing layout from screenshots or hand-drawing formatting via `batchUpdate` once an original spreadsheet exists. Use the original as the source of truth.

## Robust workflow

1. Inspect the source workbook first, not just the first tab:
   - list all sheet titles, indexes, row/column counts;
   - identify which tab is the visual dashboard (often not the first tab; e.g. a data-entry tab may be first, with `Светлая тема` / `Темная тема` later);
   - count merges, charts, validations, formulas, styled cells, visible errors.
2. Make a Drive backup of the target before destructive replacement.
3. For true 1:1 restoration, copy **all source tabs** into the target with `sheets.copyTo`, not only the first sheet.
4. After all copied tabs are present, delete or archive old broken target tabs, then rename/reorder copied tabs to exactly match the source.
5. Important: after `copyTo`, formulas on dashboard/theme tabs can still point at old/intermediate sheet references or copied-sheet names. Once final tab names are in place, read formulas from the source with `valueRenderOption=FORMULA` and write them back to the matching ranges in the target with `valueInputOption=USER_ENTERED`. This preserves copied styles/charts while rebinding formulas inside the target workbook.
6. Verify against the source by comparing, per tab:
   - row/column counts and frozen rows/cols;
   - gridline visibility;
   - merge count;
   - chart count;
   - conditional formatting count;
   - styled-cell count;
   - validation count;
   - formula count;
   - non-empty cell count;
   - visible formula errors.
7. Report only after the comparison is clean. Link directly to the visual tab (`#gid=...`), not just the workbook root, so the owner opens the polished screen immediately.

## Pitfalls from the session

- The source's first tab may be raw data (`Лист для вноса данных`), while the desired visual screen is another tab (`Светлая тема`). Copying only the first tab makes the result look wrong even if the copy is technically exact.
- Manually recreating charts from screenshots is fragile: source ranges, series columns, overlay positions, merged cells, and number formats are easy to misread.
- A copied sheet can preserve styles/charts but still show formula errors until formulas are rebound after final sheet names are restored.
- Avoid claiming success from API geometry alone; compare against the original workbook and check visible formula errors.
