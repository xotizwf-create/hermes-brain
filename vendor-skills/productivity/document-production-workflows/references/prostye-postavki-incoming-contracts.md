# «Простые поставки»: входящие контрактные документы

Use this reference when Александр asks to process incoming documents in the «Простые поставки» connector/MCP.

## Safe processing sequence

1. Read the MCP prompt `incoming_contract_processing` before extracting or saving anything.
2. List unprocessed incoming contract documents and handle each document explicitly by `documentId`.
3. Read/extract the document text; do not trust OCR blindly for legal/financial fields.
4. Extract only contract fields that belong in the card: number, date, customer/supplier names and INNs, VAT, delivery terms, line items, quantities, prices, sums, notes.
5. Ensure customer/supplier organizations by INN, marking the supplier as `asSupplier=true` only for suppliers.
6. Calculate derived deadlines with a tool, not mentally. If delivery is per заявки rather than a fixed date, preserve the delivery-term text and avoid inventing a single fulfillment date unless the UI requires a conservative contract-end placeholder.
7. Save parsed fields with `save_incoming_contract_document_fields` first.
8. Search existing contracts by contract number before creating/updating. If no duplicate exists, create via `save_contract_from_incoming_document`; if a duplicate exists, update only the intended card.
9. Read back the created/updated contract with `get_contracts`/`fetch` and verify the visible card, not only the extracted state.

## Line-item verification pitfall

For incoming contracts, successful MCP writes are not enough. After `save_contract_from_incoming_document`, always verify each visible line item:

- item name comes from the contract/specification `Наименование` column, not from `Наименование по Р/У` unless the prompt explicitly says otherwise;
- quantity equals the contract quantity;
- price equals unit price;
- line sum equals quantity × price;
- total contract amount equals the sum of lines.

A real observed failure mode: the created contract card can show `price=0` or contract `amount` equal to quantity when the extracted state itself had correct `qty`, `price`, and `sum`. Treat this as an incomplete processing result. Do not tell Александр the documents are fully processed until the card has been fixed or the backend mapping has been patched and the contract is read back correctly.

## Reporting

When reporting back, separate:

- documents parsed/fields saved;
- contracts created/updated;
- read-back verification passed;
- unresolved connector/card-mapping problems.

Avoid sending unnecessary downstream information or dispatching anything outside the contract registry unless Александр explicitly asks.