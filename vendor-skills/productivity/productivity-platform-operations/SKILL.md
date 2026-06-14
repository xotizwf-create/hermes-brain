---
name: productivity-platform-operations
description: "Use when operating productivity SaaS/platform APIs: Google Workspace, Airtable, Notion, Linear, Obsidian, maps/geocoding, project registries, reminders, and owner/business recommendation workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [productivity, google-workspace, airtable, notion, linear, obsidian, maps, workflows]
    related_skills: []
---

# Productivity Platform Operations

## Overview

Umbrella for manipulating structured productivity systems. The common discipline is the same: discover schema/targets first, use official APIs/CLIs, make minimal scoped changes, and verify by reading back.

## When to Use

- Gmail/Calendar/Drive/Docs/Sheets via Google Workspace tooling.
- Airtable record CRUD/filter/upsert.
- Notion pages/databases/blocks.
- Linear issues/projects/teams.
- Obsidian vault notes.
- Maps/geocoding/POIs/routes/timezones.
- Hermes Brain/project registries or owner recommendation workflows.
- Prostye Postavki / `prostye_postavki` MCP connector workflows: incoming contracts, organizations, product/stock lookup, deliveries, and generated business documents.

## Common Workflow

1. Identify workspace/account/base/database/vault/team/project.
2. Read schema/metadata before writes.
3. Resolve fuzzy names to stable IDs.
4. Prepare the exact payload; ask for confirmation for external messages/tasks/destructive changes.
5. Execute through the platform tool/API.
6. Read back the record/document/event/task to verify.

## Platform Notes

- Google Workspace: never expose tokens; prefer `gws` helpers or typed API wrappers. For Александр's calendar requests, default to the primary personal calendar `alexxandr.nikitenko@gmail.com`; do **not** mix in subscribed/shared calendars such as Евгений Палей unless the user explicitly asks for all/shared calendars. If a Google OAuth token is expired but has a refresh token, refresh it silently and retry once before reporting an access problem.
- Airtable/Notion/Linear: schema fields and IDs beat display names.
- Obsidian: preserve frontmatter/link style and avoid breaking vault links.
- Maps: include retrieval time/source and distinguish route estimates from facts.
- Owner/business workflows: obey MCP-specific confirmation and formatting contracts.
- Prostye Postavki incoming contracts: first read `incoming_contract_processing`; extract fields from OCR/text manually; resolve organizations by INN; search products/stock but preserve the full contract item name when there is no confident catalog match; save parsed fields without creating contracts unless asked; always verify with a separate read-back. For large OCR output that gets truncated, use a local JSON-RPC MCP call that filters and prints only safe snippets. See `references/prostye-postavki-incoming-contracts.md`.
- Albery owner reports / Google Sheets acceptance: when the owner asks for a weekly/daily owner report based on a meeting and a sheet, explicitly compare `meeting transcript/report ↔ Google Sheet ↔ prior owner reports`. Separate **accept**, **partial accept**, and **do not accept**; do not let a sheet status of “Выполнено” override a spoken blocker or missing artifact. If the owner asks to expand/rebuild using регламент, матрица решений, instructions, or feedback, preserve existing person-specific findings and add governance checks for meeting rhythm, decision roles, task/result artifacts, and prior recommendation feedback. See `references/albery-owner-report-acceptance.md`.

## Pitfalls

- Updating by title/name when multiple records match.
- Skipping schema discovery and sending invalid field names.
- Treating generated project registries as source of truth when editable source cards exist.
- Dispatching recommendations/tasks without explicit approval.

## Verification Checklist

- [ ] Stable target ID resolved.
- [ ] Payload reviewed for scope.
- [ ] API/tool call succeeded.
- [ ] Read-back verification completed.
