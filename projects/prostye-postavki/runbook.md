---
id: prostye-postavki-runbook
type: project
project: prostye-postavki
tags: [runbook, ops]
updated: 2026-05-31
secret_refs: []
---

# Простые поставки — runbook

## Routine tasks
- Work with contracts, deliveries, balances, organizations and commercial offers via the connected MCP tools.
- For commercial offers, always follow the MCP prompt `commercial_offer_workflow` before generation or email sending.
- For incoming contract documents, always follow the MCP prompt `incoming_contract_processing` before saving extracted fields or creating/updating a contract.

## Backups
Known operational memory: backups are configured for this project on server `miramed32` with database backups under `/root/db_backups` and daily backup schedule. Before relying on this, verify current state through the dedicated backup instruction/skill.

## Troubleshooting
- MCP unavailable → check Hermes MCP configuration first, then server health if SSH access exists.
- КП generation wrong → inspect MCP prompt, templates, item names, VAT/markup parameters, and history.
- Contract import wrong → re-read OCR text, save corrected extracted fields, then verify by reading the document back.
