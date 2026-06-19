# Albery Google Drive folder-item operations

Use when Александр asks to extend the Albery Bitrix/Telegram AI agent so it can manipulate Google Drive folders and items.

## Durable lesson
Google Drive "delete from this folder" is usually **not file deletion**. For shared/team-drive style workflows it means removing one parent folder relation from a Drive item while leaving the underlying file/folder alive elsewhere. The same capability should work for Google Sheets, Docs, arbitrary files, and folders.

## Implementation checklist
1. Add/verify MCP tools at the agent boundary, not only UI/backend helpers:
   - `remove_drive_item_from_folder` — remove one item from one folder without deleting the item globally.
   - `move_drive_file_to_folder` / equivalent move tool — support folders as well as files.
2. Accept both raw IDs and Drive/Docs/Sheets URLs; normalize IDs before calling Google APIs.
3. Use Google Drive API parent updates:
   - remove from folder: update the item with `removeParents=<folder_id>`.
   - move: update parents with `addParents=<target_folder_id>` and `removeParents=<old_parent_ids>` where appropriate.
   - include shared-drive flags such as `supportsAllDrives=true` when the project already uses them.
4. Keep destructive-operation wording precise: "убрать из папки" / "переместить" is not the same as "удалить файл полностью".
5. Require an explicit confirmation gate (`confirm=true`) before mutation. The handler should reject missing confirmation before external side effects.
6. Expose the tools only to access tiers that are allowed to mutate Drive. Verify that full/operational users can see them and FAQ users cannot.
7. Update the human-readable capabilities/instructions so the bot stops saying "не умею" for folder-file/folder-folder moves.

## Verification checklist
- Import/registry check: `TOOLS` contains both move and remove operations.
- Confirmation guard check: calling the mutation tool without `confirm=true` returns an approval requirement and performs no API call.
- Access-tier check: full and operational capabilities include the Drive folder operations; FAQ does not.
- Runtime check: restart only the relevant Albery services and verify they are active.
- Documentation check: update Hermes Brain project docs/changelog for the Albery MCP/tool surface.
- Repository check: commit/push both code and brain documentation when applicable.

## Pitfalls
- Do not implement this as permanent file deletion/trash unless Александр explicitly asks to delete the object itself.
- Do not limit the operation to spreadsheet MIME types; folders and arbitrary files must be accepted.
- Do not report success from code edits alone. Verify the running MCP/agent registry and confirmation guard after restart.
- Some project `.env` files include human notes; parse only required keys instead of blindly sourcing the whole file.
