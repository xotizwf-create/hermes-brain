# Простые поставки — product model and Business Pack direction

Use this reference when documenting, changing, or planning «Простые поставки» product flows, especially incoming contracts, product-name mapping, stock, commercial offers, directories, MCP actions, Telegram upload, and Business Pack document generation.

## Product description workflow

When Александр asks to describe or formalize «Простые поставки»:

1. Treat it as a product/business-flow document, not only a technical README.
2. Write the current/target behavior with an explicit date, e.g. `Дата описания: DD.MM.YYYY`.
3. Put the durable product doc in the project repo, preferably `docs/product-description.md`, and link it from the root `README.md`.
4. If a repo agent/runbook file contains stale business rules, patch it too so future agents do not follow old behavior.
5. Commit and push documentation-only changes when the owner explicitly asks to put the description in the Git repo.

## Core product flow to preserve

Main flow:

1. Operator uploads a contract into incoming documents.
2. Future target: operator can send the contract directly in Telegram; the file should become an incoming document.
3. AI/MCP reads OCR/text and extracts all required fields: date, supplier, customer, VAT, specification, units, quantities, prices, sums, deadlines.
4. MCP saves the fields, reads them back, verifies no critical data was lost, then creates the contract only after successful verification.
5. Do not create a contract if number/date/parties/VAT/items/qty/price/deadline are missing or doubtful; ask the operator.

## Product naming rule — important correction

Александр clarified the target naming rule:

- `Наименование для документов` / `docName` should be `Наименование по Р/У` when present.
- If `Наименование по Р/У` is absent, fallback to the normal long `Наименование`.
- `Наименование` / `name` has two valid modes:
  - internal short product code/name such as `СМ04`, `СМ02` when the long specification name confidently matches the price list/catalog;
  - otherwise the same long name as `docName`.

If older prompts/code say “do not use Наименование по РУ” or always use the ordinary `Наименование` for `docName`, treat that as documentation/code drift and synchronize prompts, backend logic, and tests with the rule above.

## Stock model

- Stock is `incoming - outgoing`.
- Incoming can be entered manually; future target is MCP-assisted incoming receipts.
- Outgoing is derived from actual contract deliveries/shipments.
- Matching should use internal short product names/codes where possible to avoid duplicate stock buckets for the same product.

## Commercial offers

- There are three commercial offers in one archive: КП1 main, КП2 and КП3 with markups.
- КП1 uses the main price-list/table price unless the user explicitly overrides the price.
- If the user enters a short code such as `СМ04`, resolve it through the price list and fill full name, unit, and price; explicit user price overrides the price-list price.
- Output can be PDF or Word; all three files are archived together.
- MCP commercial-offer actions should verify items, qty, unit, prices, VAT, markups, templates, format, and email recipient before creating/sending.

## Directories

- Directories include units and organizations.
- Organizations are filled by INN through the external service (DaData in current implementation): user enters INN, clicks fill, and fields are populated.
- MCP should support organization lookup/ensure/upsert by INN.
- Never overwrite existing non-empty organization fields with empty values.

## Business Pack direction

Current architecture: Business Pack runs on a Windows PC next to a local connector. The site queues jobs for that device; the connector writes documents into the local Firebird Business Pack database and returns results.

Guidance:

- Do **not** recommend installing Business Pack on the Linux production server or relying on server-side UI automation.
- UI automation for Business Pack is fragile: focus, modal dialogs, RDP session state, Windows locking, resolution, and BP updates can break it.
- Preferred path: improve the existing Windows/local connector so it can select templates, create BP documents, export/download files, and return structured results.
- If a server-like BP environment is needed, use a dedicated Windows BP-agent machine/VM with Business Pack + connector, not the Linux web server.
- For documents not strictly requiring Business Pack, prefer server-side generation inside «Простые поставки» using templates, as already done for acts.

## Safety gates

Any MCP action that creates, sends, exports, writes, or changes external/local state should use preview/read-back and explicit confirmation. This includes contract creation, commercial-offer archive/email, organization upsert, document generation/export, and future stock incoming receipts.
