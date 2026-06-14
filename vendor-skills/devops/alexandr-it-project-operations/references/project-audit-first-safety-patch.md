# Project Audit First Safety Patch Pattern

Use this reference when a read-only audit has identified a small, high-confidence safety issue and Александр asks to start fixing it. The goal is to stabilize the dangerous edge first, not to begin broad refactoring.

## Trigger

- Audit found an AI/MCP/API action that can mutate external state or live project state.
- The action is clear enough for a narrow patch.
- Bigger structural risks exist, but changing them now would be too broad.

## Example Shape

A project MCP tool could create a Bitrix task. Documentation and model instructions said to confirm with the user, but the server-side handler did not require `confirm=true`. The safe first patch was:

1. Confirm audit markdown files are present in the repo root.
2. Add/import-package hygiene required for tests, e.g. local `mcp/__init__.py` if `import mcp.context_server` resolves to an installed external package instead of the project module.
3. Write a failing test before changing production code:
   - call the MCP handler without `confirm`;
   - monkeypatch downstream resolver/database/external API helpers to raise if reached;
   - assert the handler raises the project MCP error with a message mentioning `confirm=true`.
4. Patch the handler to check `args.get("confirm") is True` at the top before validation/resolution/API calls.
5. Update every contract surface:
   - MCP `inputSchema.properties.confirm`;
   - MCP `inputSchema.required`;
   - tool description;
   - internal context guide / AI instruction strings;
   - README/tool docs.
6. Run narrow verification:
   - new focused test;
   - MCP registry/contract tests;
   - lightweight static check such as `pyflakes`;
   - relevant small suite, not production DB or live external services.
7. Report exact changed files, passed checks, and that no commit/deploy/prod/DB action happened unless it did.

## Pitfalls

- A UI-level confirmation is weaker than a server-side gate. External actions need code-level `confirm=true` enforcement.
- Documentation-only confirmation rules are not enough; handlers must reject unsafe calls before side effects.
- Confirm-gate tests should prove ordering: the gate fires before DB lookups, org-structure resolution, API calls, file writes, dispatch, or deletes.
- If the local test import fails due to package resolution, fix the import/package marker; do not record a durable claim that the tool or test framework is broken.
- Do not let the first safety patch expand into cleanup of huge files, architecture extraction, or legacy API redesign.
