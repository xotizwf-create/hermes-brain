---
id: zoom
type: connector
tags: [zoom, transcripts, mcp]
updated: 2026-05-29
secret_refs: [proj/albery/zoom/event-secret, proj/albery/zoom/webhook-token]
---

# Connector: Zoom

## Purpose
Zoom calls, recordings, transcripts and call reports — via the Albery MCP context server.

## Allowed without confirmation
- List calls, read transcripts, search transcripts, read stored call reports.

## Only with confirmation
- Save/delete call reports, dispatch operational tasks from calls.

## Integration
- Incremental recording sync (skips unchanged recordings).
- Webhook: `https://mcp.m4s.ru/zoom/events/<ZOOM_EVENT_SECRET>` → queue `zoom_recording_events`.
- `ZOOM_WEBHOOK_SECRET_TOKEN` from Zoom Marketplace Event Subscriptions.

## Secret references
`proj/albery/zoom/event-secret`, `proj/albery/zoom/webhook-token`
