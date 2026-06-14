# Простые поставки — MCP document export workflows

Use this reference when adding or repairing MCP tools that generate downloadable documents for «Простые поставки»: commercial offers, acts, contract exports, transfer/acceptance documents, or similar backend-rendered files.

## Durable pattern

1. **Load project/server skills first.** For code + production work, use `alexandr-it-project-operations` and `secure-project-server-ops`; for document extraction/contract data, also use the Prostye Postavki MCP prompts such as `prostavki_operator_guide`, `incoming_contract_processing`, or the relevant commercial-offer workflow.
2. **Do not create a parallel renderer.** Reuse the same backend functions/data structures that the UI export button uses. The MCP tool should be a thin, validated wrapper around the existing export path so the resulting `.docx`/`.pdf` matches the interface format.
3. **Expose a clear MCP tool contract.** Add the tool schema, handler, and route/dispatch entry together. Include document type, contract id, optional template id/name, stage number, and only safe override fields.
4. **Resolve templates from existing app state.** Prefer the template already saved in the contract/form snapshot or document config; otherwise require a specific `templateId`/`templateName` if multiple templates match. Do not silently choose among multiple valid templates.
5. **Use a dedicated export directory under app data.** Keep generated files separate from source templates, e.g. a `DATA_DIR` subfolder for MCP document exports. Return a short-lived/public download URL or a local downloaded file for Telegram delivery, not raw binary in tool output.
6. **Build payload from contract data the way UI does.** For acts, derive stage rows/items from the contract snapshot/stage rows, map back to full specification rows for `docName`, unit, price, and quantities, and reject empty item sets instead of generating a blank document.
7. **Keep production patch narrow.** Edit only the backend file(s) needed for the MCP wrapper unless the existing renderer itself is broken. Avoid schema migrations unless the feature truly needs persistent new data.

## Verification checklist

- Backend syntax/import check passes.
- Service restarts cleanly and health endpoint returns OK.
- MCP `tools/list` shows the new tool with the expected schema.
- A real MCP call creates a document and returns filename, size, document type, item count, and template name/id.
- Download the returned document and verify it is a valid Office/PDF file, not just that the endpoint returned 200.
- Inspect the generated document text enough to confirm the target contract/product/customer data appears.
- Re-check service health after the test generation.
- If the change touched live production code, commit the exact tracked production code, push it to GitHub, fast-forward `main` when safe, remove temporary backup files, and verify the production checkout and GitHub `main` point to the same commit.
- Deliver the generated file as a real Telegram attachment (`MEDIA:/absolute/path`), not just a local path string.
- Before calling the task complete, verify the code change is captured in the project source of truth: locate the repo/working copy, check `git status`, commit/push if this was an approved code change, and update the project docs/runbook with the new MCP tool contract and verification notes. If the live service was patched but the repo is empty/missing, say so explicitly and schedule/recommend a source-of-truth recovery instead of implying the change was committed.

## Calling the MCP export tool from Hermes

When the built-in MCP tool wrapper is not available or the conversation was compacted, use the configured HTTP MCP server as the source of truth instead of guessing the project path:

1. Read only the MCP server URL from Hermes config; do not print the URL/token to chat.
2. Use the Python MCP client (`mcp.client.streamable_http.streamablehttp_client` + `ClientSession`) to call `list_tools` and confirm the document export tool/schema.
3. Resolve the target contract through `get_contracts(query=<number>)`; when several contracts match the same number, pick the one that matches the prior context/customer/product, not just the first result.
4. For `create_contract_act_document`, pass `contractId`, `actType`, and `stageNumber`. Valid act types include `act_acceptance`, `act_commissioning`, `act_obligations`, and `act_warranty_obligations`.
5. If the tool returns “multiple templates found”, do not bypass the safety guard. Look up `act_templates` (or the contract `formSnapshot.businessPackDocs`) and retry with the explicit `templateId`/`templateName` that matches the supplier/document type.
6. Download the returned `downloadUrl` to a stable `/tmp/...` path, then validate the `.docx` package with `zipfile.testzip()` and inspect `word/document.xml` text for contract/product/document-type markers.
7. Some generic templates, especially warranty documents, may intentionally contain fewer product details. Treat a valid `.docx` with the correct document heading/contract marker as acceptable if the template itself does not include item placeholders; mention this only if relevant.
8. For multi-document requests, generate and verify the whole set before replying, then send every file as a separate real Telegram attachment.

## Pitfalls

- UI-export parity matters more than making a quick standalone template filler; duplicate renderers drift quickly.
- If multiple templates match a document type, forcing the caller to pass `templateId`/`templateName` is safer than guessing.
- Generated-file success is not enough: verify downloaded bytes and document contents before telling Александр it works.
- Do not let a strict text-marker check falsely fail a document whose template intentionally omits product rows; validate by document-type heading and available contract/template markers instead.
- Never print project secrets or full env values while connecting to production; parse secure env files and pass credentials through process environment only.
