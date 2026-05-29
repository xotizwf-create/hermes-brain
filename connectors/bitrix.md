---
id: bitrix
type: connector
tags: [bitrix, tasks, crm, mcp]
updated: 2026-05-29
secret_refs: [proj/albery/bitrix/event-secret]
---

# Connector: Bitrix

## Purpose
Tasks, task comments, chats/messages, send messages — via the Albery MCP context server.

## Allowed without confirmation
- Search tasks, read task comments, search messages, read org structure/knowledge.

## Only with confirmation
- Create/delete tasks, send Bitrix messages, send recommendations to Bitrix.

## Integration
- Near-realtime via outgoing Bitrix webhook → queue `bitrix_task_events`.
- Endpoint shape: `https://mcp.m4s.ru/bitrix/events/tasks/<BITRIX_EVENT_SECRET>` (secret by reference).

## Secret reference
`proj/albery/bitrix/event-secret`
