# Project Audit Pattern — MCP Boundary and Action-Safety Matrix

Use this reference when auditing a project where an MCP server, AI agent, backend workflows, UI buttons, and external systems all operate on the same data.

## Trigger

Apply this during a read-only audit when:

- MCP tools are described as “read-only” but some handlers may write to the database or call backend workflows.
- AI agents can create/delete tasks, send messages, save reports, process OCR, update live instructions, or fetch arbitrary URLs.
- UI actions and MCP tools are parallel surfaces for the same workflows.
- The user asks to continue from a lost/interrupted context and provides a screenshot or partial prior message.

## Recovery after context interruption

If the conversation context was compacted or interrupted:

1. Acknowledge the interruption plainly; do not blame the project or pretend the context is intact.
2. Reconstruct the stopping point from the user-provided screenshot/quote plus local audit artifacts.
3. Resume from the reconstructed phase, not from the beginning.
4. Write a durable stage-specific audit artifact so the next interruption has a concrete file to resume from.
5. Verify `git status --short` and state whether only audit documentation changed.

## MCP boundary audit method

1. Inspect the MCP server handlers and count the actual tool functions.
2. Classify tools by *real side effect*, not by name or description.
3. Treat words inside guide/instruction tools as potential false positives; inspect function bodies and called backend workflows.
4. Follow `app_workflow_function(...)` / backend workflow calls to the actual executor before assigning risk.
5. Cross-check frontend/API actions, because UI buttons may perform the same writes/sends as MCP tools.
6. Compare current behavior with documentation claims; flag documentation drift explicitly.

## Recommended action classes

Use a stable classification matrix:

- `read_only` — only reads DB/context.
- `external_read` — reads from external network/documents, no writes.
- `local_export` — creates a local file/artifact/link.
- `workflow_db_write` — invokes a workflow that updates derived state such as OCR/statuses.
- `db_write_draft` — writes draft/event/version data that does not become current behavior.
- `db_write_current` — changes current status, current report version, or live AI instructions.
- `external_action` — sends messages, creates/deletes tasks, uploads files, or otherwise mutates an external system.

## Confirmation standard

The goal is not to ask the owner for 1000 confirmations. Separate a fast read route from real external mutations:

- A user request to analyze, prepare a report, inspect tasks, or collect recommendations is enough permission for bounded read-only exploration inside that work scope.
- MCP routes should be short: entry instructions → context guide/intent → source indexes → targeted reads by date/id/dialog/call → preview → action only if needed.
- Complex requests may take as long as needed for quality when many sources/tools are genuinely required; still optimize the route with indexes, limits, offsets, exact ids, and bounded compact exports instead of random unbounded scans.
- `read_only`: no confirmation needed inside the agreed work scope.
- `external_read`: allowlist domains where possible; otherwise require explicit user intent for the link/domain.
- `local_export`: no external confirmation, but report that a file/artifact was created.
- `workflow_db_write`: require at least an explicit operator action or clearly named workflow; do not call it “read-only”.
- `db_write_draft`: can be allowed without confirm when clearly a draft/event.
- `db_write_current`: require preview or precise description before writing, especially for live AI behavior.
- `external_action`: always require preview + explicit approval + a code-level `confirm=true` gate.

## Common findings to look for

- A tool like `create_*` performs an external action without `confirm=true`, while `delete_*`/`send_*` tools do require confirmation.
- OCR tools look harmless but update OCR/state tables.
- `upsert_ai_instruction` changes live agent behavior and should be treated as current-state mutation.
- `fetch_url` or similar arbitrary URL fetchers create SSRF/URL-leak risk even if they are read-only.
- Project docs call MCP “read-only” after write/send tools were added.
- Root README still describes an old smaller app instead of the current AI/MCP platform.

## Output artifact

Create a stage-specific Markdown artifact, for example:

```text
audit-stage-b-mcp-boundary.md
```

Suggested sections:

- stopping point / reconstructed context
- checked sources
- MCP tools by action class
- backend workflows called by MCP
- UI/API parallel manual actions
- inconsistencies and risks
- proposed unified action standard
- next step for the audit

Keep it read-only: do not change production code while building the matrix.
