# Archive a Project and Remove It from Regular Digests

Use when Александр says a project should stop appearing in routine checks, watchdogs, or morning digests, but should remain findable for explicit future work.

## Pattern

1. Treat the request as broader than a single cron pause. Check for all active paths that can surface the project:
   - project registry / Hermes Brain project card
   - per-project `servers.md`, `deploy.md`, `runbook.md`
   - active cron jobs and chained context jobs
   - auto-loaded MCP server entries
   - compact persistent memory pointers
2. In the project card, mark the project as archived or otherwise excluded from automation:
   - `status: archived`
   - summary says it is excluded from regular digests/checks
   - tags include `archived` rather than operational/active tags where appropriate
   - add an `automation_policy` block such as:
     ```yaml
     automation_policy:
       include_in_regular_digests: false
       read_mcp_only_on_owner_request: true
     ```
3. In project operational docs, add the explicit rule near MCP/admin operations: routine jobs must not read/start the MCP; use it only after direct owner request.
4. Rebuild and validate the brain/project registry with the repository's normal scripts. Commit the knowledge-base change if that is the repo convention.
5. Disable auto-loaded MCP through the official Hermes config command rather than hand-editing protected config files. Example shape:
   ```bash
   hermes config set mcp_servers.<server_name>.enabled false
   ```
6. Update cron prompts, not only job status. If a morning digest has a data-collection job plus a delivery job, patch both:
   - collector must not inspect the archived project
   - formatter must not render a block for it
   - if the prompt still mentions the project, make the mention a clear exclusion rule, not a reporting instruction
7. Verify by reading back:
   - MCP enabled flag is false
   - project status/policy is archived/excluded
   - relevant cron prompts contain the exclusion rule
   - digest delivery target still follows the current automation-delivery policy
8. Update compact memory only with the durable routing rule, not the task narrative.

## Pitfalls

- Pausing one watchdog is not enough: another digest or context-producing cron may still report the project.
- Do not delete the project from the brain unless Александр explicitly asks. Archived means discoverable on request, silent otherwise.
- Do not encode a transient complaint as a permanent ban on all future project access. The stable rule is: access only on direct owner request.
- For protected Hermes config files, prefer `hermes config set ...` so the write goes through the supported path.
