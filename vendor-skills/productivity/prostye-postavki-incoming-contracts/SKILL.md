---
name: prostye-postavki-incoming-contracts
description: Use when reading, correcting, registering, or overwriting incoming contract documents in the «Простые поставки» MCP system, including OCR/image extraction, party matching by INN, specification entry, dates, VAT, and final verification.
---

# Incoming contracts in «Простые поставки»

Use this skill for the full incoming-document pipeline: inspect the source, extract exact fields, save parsed data, verify it, and create or overwrite the contract card.

## Core workflow

1. Read the MCP prompt `incoming_contract_processing` before changing data.
2. Start from `list_incoming_contract_documents`; identify the exact document and whether it is already processed.
3. Read the source with `read_incoming_contract_document(includeText=true)`.
4. For scans, images, doubtful OCR, signatures, requisites, or dense specification tables, inspect only the necessary original pages with `view_incoming_contract_document` and vision. If the user supplies a separate screenshot with clearer values, treat it as primary evidence for those visible fields and cross-check against the document.
5. Extract only supported facts:
   - contract number and date;
   - customer and supplier names plus INNs;
   - VAT rate/text;
   - deadline as an absolute date or a duration phrase;
   - every specification row: exact document name, unit, quantity, unit price, row sum;
   - plan quantity/date when requested.
6. Preserve source wording in `docName`; use `name` as the concise working name only when there is a reliable catalog match or an obvious harmless normalization.
7. Save fields with `save_incoming_contract_document_fields`.
8. Immediately verify with `read_incoming_contract_document(includeText=false)`. Check parties, dates, VAT, every item, and totals.
9. Create the card with `save_contract_from_incoming_document`. Set `markDocsSent` only when the user explicitly says documents were sent.
10. Verify creation from the returned `itemsSaved`, `totalAmount`, `sumWarnings`, and `linkedOrganizations`. Do not add redundant diagnostic reads when the tool explicitly says these fields are sufficient.

## Exactness and user overrides

- Never invent a missing date, INN, quantity, price, or party.
- If the user explicitly overrides a source date or deadline (for example, “date and deadline today”), apply that value to `contractDate` / `deadlineDate` and planned item dates as requested.
- Preserve the original contractual deadline phrase in `deadlineText` or `notes`, clearly noting that the card date was set by direct user instruction. This keeps the operational card faithful to the request without losing the source condition.
- Resolve “today” with the live Europe/Moscow date, never from model memory.
- Match customer and supplier by INN. If `linkedOrganizations.*.isPlaceholder=true`, create/complete the organization by INN and repeat the save using `contractId`.

## Specification safeguards

- Recalculate row sums and grand total before saving.
- Verify VAT is included/excluded exactly as written. Do not infer “без НДС” from a missing VAT line.
- Historical UI storage may expose quantity in raw `parsedEdits.items[].price` and unit price in `.total`. Do not interpret these raw field names literally. Verify against `itemsReadable` after field save and `itemsSaved` after contract creation.
- Treat `sumWarnings` as a blocker: correct the extracted payload with one overwrite call rather than creating a duplicate.
- After successful creation, the source document disappearing from incoming is normal; its file should be attached to the contract.

## Overwrite and duplicate prevention

- Never recreate a processed document as a new contract merely because it disappeared from incoming.
- To correct an already-created contract, call `save_contract_from_incoming_document` once with its exact `contractId` and corrected `extracted`; `documentId` is no longer required.
- Report success only after the creation response confirms status and saved items.

## User-facing response

Keep the final confirmation short and operational: contract number, dates, parties, item count, total, VAT, and whether the source file is attached. Avoid internal IDs and raw schema details unless troubleshooting is requested.

## Reference

See `references/verification-patterns.md` for the raw-schema mapping and a compact final verification checklist.