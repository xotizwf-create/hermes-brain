---
id: google-drive
type: connector
tags: [google, drive, files, mcp]
updated: 2026-05-29
secret_refs: []
---

# Connector: Google Drive

## Purpose
Search and read documents/files.

## Allowed without confirmation
- Search, list, read file content on request.

## Only with confirmation
- Create/modify/delete/share files.

## Authentication
MCP Google Drive `authenticate` → OAuth → `complete_authentication`.

## Notes
- Long Drive syncs need Nginx proxy timeout 600s on albery.
