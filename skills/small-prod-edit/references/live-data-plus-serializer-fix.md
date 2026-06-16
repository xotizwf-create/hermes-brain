# Live data + serializer fix pattern

Use when a production issue is visible in an API/UI response and may be caused by both stored data and response serialization.

## Pattern
1. Verify the symptom through the same layer the user sees (MCP/API/UI), not only by inspecting the database.
2. If stored rows are wrong, take a targeted backup/export of only the affected IDs before editing.
3. Patch only the affected rows first; do not run broad migrations for two bad records.
4. Re-check via the same outward layer. If raw DB data is now correct but API/UI still shows bad values, the bug is in serialization/normalization, not in the data.
5. Make a minimal backwards-compatible serializer fix that accepts both historical and current payload shapes.
6. Restart only the affected backend service and verify with the same outward layer again.
7. Commit the code fix to the canonical repo so a future deploy does not revert the production hotfix.
8. Document the project-specific incident in the project brain, including affected IDs and the code commit.

## Pitfall
Do not stop after a DB correction just because the database looks right. If the user's surface is MCP/API/UI, final verification must happen there. A production hotfix is incomplete until both data and the serving code path agree.

## Example from Простые поставки
Incoming contract import saved item unit price in a snapshot field layout different from the UI serializer's expected layout. The cards stored prices, but the connector returned `items[].price = 0`. The fix required both targeted normalization of two contract cards and a backend fallback that accepts both snapshot formats.