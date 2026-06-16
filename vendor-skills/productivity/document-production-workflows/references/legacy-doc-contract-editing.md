# Legacy `.doc` contract editing workflow

Use this when a user needs a Russian contract based on an existing old Word `.doc`/BusinessPack-style file and only a few legal/commercial fields should change.

## Approach

1. Work on a copy of the source file; never edit the original download in place.
2. Convert legacy `.doc` to `.docx` with LibreOffice headless so format-aware tooling can inspect and edit it:
   ```bash
   soffice --headless --convert-to docx --outdir /tmp/work /tmp/work/source.doc
   ```
3. Use `python-docx` to inspect paragraphs/tables and identify exact runs/cells for replacements. Print candidate paragraphs/tables around product names, legal basis, price, VAT, totals, specification rows, signatures, and customer details.
4. Make targeted replacements only: keep legal preamble/customer/vendor requisites unchanged unless the user explicitly asks otherwise. For specification rows, replace cell text rather than rebuilding the whole table. When the owner says “больше ничего не менять”, treat that as a hard constraint: change only the named fields (e.g. legal basis in preamble, product, quantity, unit price, VAT, total, contract number/date if later specified) and preserve all other wording/layout/requisites.
5. If the owner later changes the requested item/details, re-run replacements from the current edited document or a fresh source copy, then verify all previous requested fields are still consistent. Contract number/date often appear in both the main contract and the appendix/specification; update every visible occurrence.
6. Verify by reopening the resulting `.docx` and checking both positive and negative assertions:
   - required legal basis (e.g. `223-ФЗ`) is present;
   - required VAT text and prices/totals are present;
   - old product names and old totals are gone;
   - quantity/unit/price cells match the request;
   - contract number/date match in both the main text and appendix when the user specified them.
7. Do an openability check by converting the final `.docx` to PDF with LibreOffice headless. A non-empty PDF confirms the Word package is structurally valid, but not sufficient for delivery quality.
8. Render the PDF pages (for example with `pdftoppm`/`convert`) and visually inspect the changed pages before sending. In particular check that the appendix starts where expected, tables are not shifted, prices stay on one line, and no cells overlap after edits. If layout shifted, adjust column widths/font size/paragraph spacing in the `.docx`, reconvert, and re-render.
9. Save owner-facing files under `/root/.hermes/outbox/` before attaching in Telegram, and verify the send tool reports successful delivery before saying the files were sent.

## Pitfalls

- Old `.doc` files often contain binary/control characters if treated as plain text; do not edit them with raw string replacement.
- A legal reference can appear both in real contract text and in hidden hyperlink metadata. Verify the actual paragraph text after conversion, not just a byte grep.
- Price edits must update all dependent fields: title/subject if needed, clause “Цена договора”, specification unit price, quantity, and line total.
