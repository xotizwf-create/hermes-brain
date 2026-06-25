# Простые поставки — MCP prompt navigation

Use this reference when extending or repairing the «Простые поставки» MCP instruction layer: prompt texts, prompt discovery, instruction search, or agent/operator guidance for commercial offers and incoming contracts.

## Durable pattern

- Keep the canonical prompt text in the project repo near the MCP implementation, not duplicated in Hermes memory.
- Attach metadata to each prompt next to the text: stable `name`, human title, category, description, keywords, `use_when`, and full text.
- Expose prompt navigation as **read-only MCP tools**:
  - `list_mcp_prompt_topics` — compact map of available instructions.
  - `search_mcp_prompts` — ordinary-language search over names, titles, descriptions, keywords, and prompt text.
  - `get_mcp_prompt` — read the full chosen prompt before acting.
- Build any `get_mcp_prompt` schema enum dynamically from `MCP_PROMPTS.keys()`; do not maintain a second hard-coded prompt list.
- For new scenarios, add keywords in the owner's natural language as well as system terms. Example: commercial offer rules should be findable by “КП”, legal entity names, template names, and business terms.

## Safe implementation workflow

1. Read the project card first (`projects/registry.yaml` → `projects/prostye-postavki/servers.md`/`deploy.md`) and use the secure project env without printing secrets.
2. Preflight production before editing; on constrained hosts keep checks light and avoid full builds or prod DB trial runs.
3. Patch only the MCP prompt/handler layer and project operator notes unless the task explicitly requires broader behavior.
4. Verify locally or on the server without DB writes:
   - Python syntax for the prompt module and MCP handler module.
   - `list_mcp_prompt_topics()` includes the expected prompt.
   - `search_mcp_prompts(<real owner wording>)` ranks the expected prompt first.
   - live MCP `tools/list` includes the navigation tools after restarting only the backend service.
   - live MCP `search_mcp_prompts` returns the expected result through the real endpoint.
5. Commit on the current live branch and push `HEAD:<current-branch>`; do not blindly switch/push `main` from a production checkout.
6. Document the durable map in Hermes Brain under `projects/prostye-postavki/` and add a pointer from `INDEX.md` so future sessions can find it without re-discovery.

## Pitfalls

- Do not treat MCP prompt navigation as a DB/content migration. It should be read-only and side-effect-free.
- Do not duplicate prompt bodies in multiple brain docs; write a map/procedure and read the current prompt via MCP.
- Do not infer the backend service name from memory; discover it from systemd/processes (`prostye-backend.service` was the active service in the session that produced this reference).
- If a remote inline Python import hangs because app startup code is heavy, fall back to syntax/static checks plus live MCP HTTP/JSON-RPC checks rather than repeatedly running the same import.
