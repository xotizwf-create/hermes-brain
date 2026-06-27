# One-to-one Google Sheets cloning and style analysis

Use this when the owner sends an existing Google Sheet as a visual/formula reference and asks whether Hermes can make something equally polished or "1 в 1".

## Best path

If the desired result is truly **1:1**, use Google Drive `files.copy` first. It preserves far more than a hand-built Sheets API reconstruction:

- formulas and calculated values;
- cell formatting, fonts, colors, borders, number/date/currency formats;
- frozen rows/columns;
- data validation dropdowns;
- column widths/row sizing;
- hidden/helper areas and other sheet metadata.

Then customize the copy only where the owner requested changes. Do not rebuild by hand unless the owner explicitly wants a redesigned derivative instead of a true clone.

## Inspection pattern before copying or recreating

Use `spreadsheets.get(includeGridData=True)` with a bounded range and explicit fields. Useful fields:

```text
properties(title,locale),
sheets(properties(sheetId,title,gridProperties),merges,conditionalFormats,charts,data(rowData(values(userEnteredValue,formattedValue,userEnteredFormat,dataValidation))))
```

Pitfall: there is no top-level `sheets.dataValidations` field. Data validation lives on individual cells as `data(rowData(values(dataValidation)))`.

Summarize the sheet for yourself before acting:

- title and locale;
- sheet names and grid sizes;
- frozen rows/columns;
- non-empty cell count in the inspected range;
- styled cell count;
- validation count;
- visible formulas and sample rows;
- charts/conditional formatting/merges if present.

## Copy + permission workflow

1. `drive.files().copy(fileId=SOURCE_ID, body={'name': NEW_NAME}, fields='id,name,webViewLink,owners(...)')`.
2. Set sharing to match the owner's expectation. In these owner-facing quick demo sheets, if they asked for editable access, set `anyone` to `writer`; otherwise avoid broad write access.
3. Read the new file back with the same summary routine used for the source.
4. Compare source vs copy on practical invariants:
   - same sheet title(s);
   - same row/column counts where important;
   - same frozen row/column setup;
   - same counts for styled cells and validations in the sampled range;
   - same first N formulas exactly;
   - no visible formula errors.
5. Only then report the link.

## Reporting pattern

Keep the owner-facing answer short and human:

- say whether it is possible;
- link the created copy;
- mention only meaningful verification: owner, editor access if set, formulas preserved, dropdowns preserved, formatting preserved, no visible formula errors.

Avoid dumping API fields or long metadata. The owner wants confidence that it works, not a transcript of the inspection.
