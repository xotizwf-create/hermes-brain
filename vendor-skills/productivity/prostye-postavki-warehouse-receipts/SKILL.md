---
name: prostye-postavki-warehouse-receipts
description: Use when checking, creating, or explaining warehouse receipts / expected incoming stock in the “Простые поставки” MCP/project.
version: 1.0.0
created_by: agent
---

# Простые поставки: приходы и ожидаемый товар

Use this skill when the user asks whether goods are ordered, on the way, already on stock, or asks to record an expected incoming shipment.

## MCP tools

- `get_inventory_balances` — authoritative calculated stock balance. Use it for “сколько есть на складе”. Do not infer balance manually from contracts or receipts.
- `get_warehouse_receipts` — list receipt lines with `stock_state`:
  - `in_transit` = draft / not posted / not accepted to stock yet;
  - `on_stock` = posted receipts that participate in stock balance.
- `create_expected_warehouse_receipt` — create a draft expected receipt. It records ordered goods, order date, expected receipt date, supplier/warehouse/items. It does **not** add to calculated stock until accepted/posted.
- `receive_warehouse_items` — record actual arrival. It first consumes matching `in_transit` expected receipts, supports partial arrivals by splitting the accepted quantity into `on_stock` and leaving the rest `in_transit`; if no matching expected receipt exists, it creates a new posted/on-stock receipt. Always run `dryRun: true` first when the user has not already approved the exact write.
- `update_warehouse_receipt_item_status` — safe status change without physical deletion: `in_transit/draft/transit` removes stock movement and returns to “в пути”; `on_stock/posted/arrived` posts to stock; `cancelled` cancels and removes stock movement while keeping history. `cancelled` requires `confirm: true`; multi-line receipts require `applyWholeReceipt: true`.
- `delete_warehouse_receipt_item` — physical deletion of one receipt line. Use only for explicit user-confirmed cleanup/test duplicates. Prefer `update_warehouse_receipt_item_status(status="cancelled")` for normal cancellation.

## Safe workflow for creating an expected receipt

Reference: `references/product-code-aliases.md` contains the durable Cyrillic/Latin alias lesson (`SM04`/`SM02` vs `СМ04`/`СМ02`) and the lookup sequence to avoid duplicate products.

1. Confirm all required business facts with the user before writing:
   - item name/code or product id;
   - quantity;
   - expected receipt date;
   - order date if not today;
   - supplier if known;
   - receipt/order/invoice number if known.
2. Search product first (`search`, `read_table_rows`, `get_inventory_balances`, or item lookup in app context). Prefer exact existing **active** `productId` from the warehouse/catalog when available.
   - Always compare the user's spoken/typed item with existing warehouse products before creating anything.
   - Treat visually similar Latin/Cyrillic codes as possible aliases and check both variants: e.g. `SM04`/`SM02` from speech may mean existing Russian `СМ04`/`СМ02` (Cyrillic `СМ`), not new English `SM04`/`SM02`.
   - If an active product exists in the warehouse/catalog under the Russian code/name, use that `productId`; do **not** create a new inactive duplicate under the Latin spelling.
   - If only inactive or newly-created-looking Latin products are found, keep searching by the Cyrillic variant and by current stock balances before writing.
3. Run `create_expected_warehouse_receipt` with `dryRun: true` first.
4. Inspect the dry-run result:
   - correct product resolved;
   - correct warehouse, usually “Основной склад”;
   - `stock_state` is `in_transit`;
   - warnings are acceptable or clarified.
5. Only after the user’s facts are clear, call it again with `dryRun: false`.
6. Verify with `get_warehouse_receipts(query=<product/code/order>, status="in_transit")`.
7. If asked about actual stock after that, still use `get_inventory_balances`; expected receipts should not be counted as on-stock balance.

## Owner rule: partial arrivals and unordered arrivals

When Александр reports a receipt, interpret it against existing in-transit receipts before creating a new posted/on-stock receipt:

- Example: “1 июня СМ02 заказ 100 шт” → create/keep 100 шт as in-transit expected receipt.
- Example later: “8 июня пришли 50 СМ02” → find matching in-transit СМ02. Mark 50/100 as arrived/on-stock with the arrival date from the message, and leave the remaining 50/100 in transit.
- If the reported arrived quantity equals the remaining in-transit quantity, mark the whole matched expected receipt as arrived/on-stock with that arrival date.
- If no matching in-transit order exists, treat the message as a new actual warehouse receipt: create/post the quantity as arrived/on-stock, not as expected/in-transit.
- If several in-transit receipts match, prefer oldest expected/order date first and ask only if ambiguity changes the business result.
- Deleting receipts is destructive: only do it after explicit confirmation naming the exact receipt/product/quantity/date. For normal business cancellation, use `update_warehouse_receipt_item_status(status="cancelled", confirm=true)` so history remains.

Current MCP supports the full owner workflow: expected order, partial/full receipt, unordered actual receipt, safe status change/cancellation, and explicit physical deletion for confirmed cleanup.

## Production implementation note

The live MCP backend has the expected-receipt tool implemented in the production repository `xotizwf-create/prostavki`. It stores dates in `warehouse_receipts.order_date` and `warehouse_receipts.expected_receipt_date`; draft receipts are intentionally treated as “в пути / не принято на склад”.
