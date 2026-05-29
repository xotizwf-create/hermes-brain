---
id: google-calendar
type: connector
tags: [google, calendar, mcp]
updated: 2026-05-29
secret_refs: []
---

# Connector: Google Calendar

## Purpose
Read events, check availability, create/update events.

## Allowed without confirmation
- List events, read availability.

## Only with confirmation
- Create/update/delete events, send invites.

## Authentication
MCP Google Calendar `authenticate` → OAuth → `complete_authentication`.
