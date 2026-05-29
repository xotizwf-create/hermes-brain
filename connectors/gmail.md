---
id: gmail
type: connector
tags: [google, email, mcp]
updated: 2026-05-29
secret_refs: []
---

# Connector: Gmail

## Purpose
Read, search, draft and send email.

## Allowed without confirmation
- Search emails, read emails on request, create drafts.

## Only with confirmation
- Send email, delete, mass archive/label.

## Authentication
MCP Gmail `authenticate` → user completes OAuth in browser → `complete_authentication`.
OAuth tokens live in the MCP layer, never in the brain.

## Notes
- Don't expose full email bodies in logs unless asked.
