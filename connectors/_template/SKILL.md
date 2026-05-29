---
id: connector-template
type: connector
tags: [template]
updated: 2026-05-29
secret_refs: []
---

# Connector: {name}

## Purpose
What this connector is used for.

## Tools
Which MCP tools belong to it (e.g. authenticate, search, send).

## Allowed without confirmation
- read-only / non-destructive actions

## Only with confirmation
- sending, deleting, mass operations, anything outward-facing or irreversible

## Authentication
How the agent connects (MCP `authenticate` → user completes OAuth → `complete_authentication`).
Tokens are managed by the MCP layer — never stored in the brain.

## Secret reference
`proj/<slug>/<service>/...` or connector-level reference name (NAME only).
