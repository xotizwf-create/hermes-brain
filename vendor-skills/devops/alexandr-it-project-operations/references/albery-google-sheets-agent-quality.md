# Albery Bitrix AI Agent — Google Sheets Quality Regression Pattern

Use this reference when Александр reports that the Albery Bitrix AI agent created a Google Sheet but the result is ugly, unreadable, has bad formulas, wrong formatting, or otherwise looks low-quality despite completing the requested action.

## Typical investigation path

1. **Start from the live Albery project location.** Use the project registry and secure project access for `albery`; the live Bitrix/Hermes agent may run on the legacy Albery host, not the newer Andigital server.
2. **Find the exact AI-bot session.** Search Bitrix bot/session logs for the user/session around the reported time, then inspect the prompt, tool calls, created Google Sheet URL, and any final response the agent sent.
3. **Distinguish three problem classes.**
   - Data/formula logic: wrong formulas, ranges, totals, percentages, cross-sheet links, or locale separators.
   - Presentation/legibility: narrow columns, tiny rows, no wrapping, overused dark/accent colors, unreadable headers.
   - Delivery/storage: sheet created in the wrong folder, wrong sharing permissions, or link sent before verification.
4. **Read back the real sheet.** Do not judge from the agent's text alone. Fetch the spreadsheet metadata/cell values/formatting where possible, or open it manually if needed.
5. **Patch the shared sheet-generation layer, not just the one request.** Prefer reusable post-processing helpers around Google Sheets creation/write/format tools so all future Bitrix-agent sheets benefit.
6. **Run a real create-and-readback smoke test.** Create a disposable spreadsheet through the same server-side code path, verify values/formulas/formatting/column widths/wraps, then delete or clean up the test sheet.
7. **Deploy and verify the running service.** Restart only the affected service, check `systemctl is-active`, recent logs, and a representative MCP/agent smoke call.
8. **Commit and align source of truth.** Push the fix to the canonical repo and ensure the live checkout matches it so future deploys do not erase the patch.

## Formatting guardrails for generated Google Sheets

For business/operator-facing Google Sheets, readability beats decorative styling:

- Use calm, light palettes; reserve saturated colors for small accents or status cells.
- Avoid large dark or high-contrast filled regions unless the text color and purpose are explicitly controlled.
- Always enable text wrapping for long Russian labels, comments, task descriptions, and headers.
- Compute column widths from real content, including Cyrillic text, currency, percentages, and long headers; do not rely only on default auto-resize behavior.
- Enforce reasonable min/max widths so short columns stay compact and narrative columns become readable.
- Apply useful row heights for wrapped headers and multi-line cells.
- Freeze header rows and apply clear header styling, but keep the body mostly clean.
- If the agent applies manual formatting, run a final legibility pass after it so accidental narrow columns are corrected.

## Formula guardrails

When the reported issue includes formulas:

- Verify formulas against the actual requested business logic and sample rows, not just syntactic validity.
- Account for Google Sheets locale differences: function names, separators, decimal commas, and currency/percent formatting can differ by spreadsheet locale.
- Prefer simple formulas when Александр's task is an Excel/Sheets task; avoid clever array formulas unless they are necessary.
- Add a small fixture sheet or smoke script that checks at least one representative formula result after creation.

## What to report back

Summarize in Russian, briefly and concretely:

- what root cause class was found;
- what reusable layer was patched;
- what real spreadsheet smoke test proved;
- that the live service is active and logs are clean;
- where the durable project knowledge was updated, if a project-brain/runbook update was made.
