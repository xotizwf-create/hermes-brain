# Простые поставки — поиск и выдача документов по контрактам

Use this note when Александр asks to send a contract document, act, invoice, waybill, or other file from «Простые поставки» into chat.

## Durable workflow

1. Read the MCP operator guide first when using the `prostye_postavki` MCP.
2. Search narrowly, then broadly:
   - exact customer/person + item/subject;
   - customer only;
   - item/subject only;
   - contract number if known.
3. Fetch the candidate contract and inspect:
   - `docSnapshot` — uploaded source contract file metadata;
   - `formSnapshot.businessPackDocs` — generated Business Pack document metadata;
   - `items`, dates, customer/supplier, and INNs for disambiguation.
4. Do not assume `businessPackDocs` means the generated file is downloadable from the server. In this app, Business Pack documents may be created on the selected PC through the Business Pack Connector, not stored as normal server attachments.
5. Public `/api/...` file URLs may require an authenticated browser/session; a 401 means the agent cannot directly fetch that file via unauthenticated HTTP. Treat this as an access boundary, not proof the file does not exist.
6. If the original/generated file cannot be downloaded, do **not** present a manually reconstructed document as the original. Offer or send it only with a clear label such as “собрал черновик/восстановленный акт по данным системы”, and mention that the original Business Pack file was not directly available.
7. If search results conflict with the user's wording (for example user says “Фокино”, but the matching audio contract is for another customer), state the mismatch plainly before sending anything.

## Common fields seen in fetched contracts

- `docSnapshot.url` / `previewUrl`: uploaded contract file endpoints, often auth-protected.
- `formSnapshot.businessPackDocs[]`: generated invoice/waybill/act metadata; for acts, includes `actTemplateId` and `actTemplateName` but may not include a server file URL.
- `formSnapshot.businessPackDataHash`: normalized data used for generated Business Pack docs.

## Safety / quality pitfall

The user expects Telegram files as real attachments. If producing a fallback document, write an actual `.docx`/`.pdf` and send it as `MEDIA:/absolute/path`, but make the fallback nature explicit in the message.