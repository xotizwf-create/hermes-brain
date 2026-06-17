# Product code aliases and Cyrillic/Latin pitfalls

Use this reference when recording warehouse receipts or expected incoming stock from spoken messages, screenshots, invoices, or OCR.

## Durable lesson

Before creating a receipt item, compare the requested name/code against existing active warehouse/catalog products. Do not trust the literal spelling from speech/OCR when the code contains letters that look identical in Latin and Cyrillic.

Common case from owner correction:

- Spoken/typed/OCR `SM04` may correspond to existing Russian product `СМ04` (`С` and `М` are Cyrillic).
- Spoken/typed/OCR `SM02` may correspond to existing Russian product `СМ02`.

If an active Cyrillic product exists, use its existing `productId` and Russian code/name. Do not create or keep a duplicate Latin product just because the incoming text was Latin.

## Practical lookup sequence

1. Search the literal user/OCR text.
2. Search visually equivalent Cyrillic/Latin variants:
   - `S` ↔ `С` where the product family is written as `СМ` in the catalog.
   - `M` ↔ `М` in short Russian-coded product names.
3. Check `get_inventory_balances(query=...)` for the variant; active stock/balance entries are strong evidence of the canonical product.
4. Prefer an active product already present in warehouse/catalog over any inactive or newly-created-looking duplicate.
5. Only write the receipt after the resolved product name/code is canonical.

## Reporting back

If a correction was needed, tell the owner plainly which canonical items were used, e.g. `СМ04` and `СМ02`, and confirm that expected receipts are still `in_transit` and not counted as on-stock balance.
