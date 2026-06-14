---
name: prostye-postavki-contract-period-lookup
description: Use when answering questions about what must be delivered for a customer/organization in a period in the «Простые поставки» MCP system.
---

# Простые поставки: поиск поставок/контрактов по заказчику и периоду

## Trigger
Use this when the user asks what needs to be delivered to a customer/city/organization in a month or date range.

## Steps
1. Read `get_mcp_prompt('prostavki_operator_guide')` first.
2. Do not rely on `get_deliveries` alone: it may return only receipts/stages and miss active contracts without plan stages.
3. Search contracts with a broad, case-tolerant fragment first:
   - Prefer city/root words like `Карачев`, `Брянск`, etc.
   - Avoid exact uppercase aliases such as `КАРАЧЕВСКАЯ ЦРБ`: `get_contracts(query=...)` can miss rows when the stored customer alias casing differs.
4. If the user supplies a screenshot or contract number, search that exact number separately with both `get_contracts(query=<number>)` and `search(query=<number>)`.
5. For period answers, filter returned contracts by contract deadline/end date inside the requested period, and include active contracts with empty fact date/quantity as still needing delivery.
6. If the customer has repeating monthly contracts with the same number, treat each row/end date as a separate delivery obligation.
7. Report uncertainty explicitly when the tool has no plan stages or fact fields are empty; do not infer completion from status alone.
8. For warehouse receipts / inbound goods, use the MCP server tool `get_warehouse_receipts`: `status="in_transit"` means draft/not posted/not accepted to warehouse, while `status="on_stock"` means posted and already included in inventory balances. Do not mix in-transit receipts with `get_inventory_balances` stock.

## Pitfalls
- `get_deliveries(query=<customer>)` can return empty even when contracts exist.
- Exact uppercase abbreviated customer names can miss contracts; use broad root search and then filter locally.
- Some rows have `amount` as quantity; item `count` is the more reliable quantity for the exact line.

## Verification
Before final answer, verify at least:
- broad customer query results,
- exact contract number if known,
- period/date filtering,
- empty or filled fact delivery fields.

## Keeping MCP behavior aligned
If this workflow changes because of a real miss/correction, do not only update this Hermes skill. The «Простые поставки» MCP server exposes its own operator prompt (`prostavki_operator_guide`), and future agents may rely on that prompt directly. When the user asks to "пропиши в MCP/МСП сервере" or the correction affects all operators, update the MCP server prompt with the same rule, restart the backend if required, then verify by reading `get_mcp_prompt('prostavki_operator_guide')` through MCP rather than trusting the edited file.
