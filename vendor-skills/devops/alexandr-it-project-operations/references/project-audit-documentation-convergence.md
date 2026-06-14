# Project Audit Documentation Convergence Pattern

Use this after a messy project audit has produced component/risk/action matrices and the next goal is to standardize documentation without changing production behavior.

## Trigger

Александр asks to continue after an audit and wants the project brought to one consistent view, especially after README/docs drift was found.

## Pattern

1. **Do not make README the only source of truth.** Use README as the short entry point, then create/expand deeper docs.
2. **Build a layered documentation set:**
   - `README.md` — concise current project overview: purpose, components, active/legacy contours, safety rules, links.
   - `docs/about-project.md` — product/business overview: roles, sources, data flows, integrations, Hermes/MCP behavior, who reads/writes what.
   - `docs/architecture-standard.md` — enforceable rules: MCP-first, action classes, confirmation policy, legacy API/UI policy, migration policy, testing policy, refactor policy, documentation policy, production/secrets policy, definition of done.
   - `mcp/README.md` — MCP tool contract and side-effect/confirmation behavior.
   - `docs/playbooks/` — operational runbooks for deploy, migrations, AI instructions, cron/prompts, rollback.
   - for MCP/AI-agent projects, add an agent workflow playbook that maps intents to tool routes, required live/local instructions, confirmation gates, and large-artifact delivery rules.
   - audit artifacts — evidence base and risk/action matrices.
3. **Separate narrative from rules.** `about-project` explains what the system is and how data flows; `architecture-standard` tells future agents/developers what is allowed.
4. **Preserve recent feature notes as subsections, not the whole project description.** If an existing `about-project` only describes the latest feature, wrap it under a feature/add-on section and add the full system overview above it.
5. **Make safety vocabulary consistent across docs.** Reuse action classes such as `read_only`, `external_read`, `local_export`, `webhook_ingest_sync`, `db_write_draft`, `db_write_current`, `external_action`.
6. **State the non-actions explicitly.** Documentation updates should say that production, DB, secrets, deploys, and external services were not touched.
7. **Verify docs like code:** check required headings/terms, run `git diff --check`, inspect `git status`, and scan new docs for accidental secrets or production credentials.

## Architecture-standard sections to include

- Sources of truth and precedence
- MCP-first control plane
- Action classes
- Confirmation policy
- MCP tool registry policy
- Legacy HTTP API policy
- UI policy
- AI-instructions policy
- External read / fetch URL policy
- Migration policy
- Testing policy
- Refactoring policy
- Documentation policy
- Production and secrets policy
- Definition of done

## Pitfalls

- Replacing stale README with another long monolith instead of layered docs.
- Leaving old wording that calls a write/action MCP server “read-only”.
- Treating UI confirmation as equivalent to server-side `confirm=true`.
- Embedding real server credentials, tokens, webhook URLs, or connection strings in docs.
- Treating a specific latest feature as the entire project description.
- Starting god-object refactoring before safety gates, risk metadata, and documentation are stable.
