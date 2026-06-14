# Remote env MCP secret retrieval

Use this when an MCP server URL must be assembled from a secret that lives in a remote project's app `.env`, while the local secure project file only has SSH credentials.

## Trigger

- User says the MCP URL is `/mcp/<secret>` or similar.
- Project registry points to a production/remote host.
- `/opt/hermes/secure/projects/<slug>/.env` contains connection credentials but not the MCP secret.

## Safe flow

1. Locally parse `/opt/hermes/secure/projects/<slug>/.env` into a dict. Do not print values.
2. Run a light remote preflight first:
   - `nproc`
   - `free -m`
   - `swapon --show` / swap free from `free`
   - `df -Pm /`
   - current load
3. Search only likely env locations with a shallow command, e.g. `/var/www`, `/opt`, `/srv`, `/root`, and print file paths only.
4. On the remote host, parse the app `.env` using Python, collect likely keys (`MCP_*`, `*_SECRET`, `*_TOKEN`, `*_URL`, `*_HOST`), and print only key names plus booleans like `url_built=yes`.
5. Build the URL in the child process from known patterns:
   - `MCP_SHARED_SECRET`, `MCP_SECRET`, `MCP_TOKEN`, or `SHARED_SECRET`
   - base URL from `MCP_PUBLIC_BASE_URL`, `MCP_URL`, `MCP_BASE_URL`, or a documented default
   - if base ends in `/mcp`, append `/<secret>`
6. Consume the resulting URL in memory to run the MCP manager's `probe`, `add --apply`, `test`, and `list` operations. Redact the full URL and any `/mcp/<secret>` path in all output before showing it.
7. If a remote temporary file was used for the URL, remove it and verify deletion before finalizing.
8. Update any secret-free registry/docs with placeholders such as `{proj/<slug>/mcp/shared-secret}`, never the real token.

## Pitfalls

- Do not `source` remote `.env` files; parse `KEY=VALUE` lines. They may contain comments, shell fragments, or values that would execute unexpectedly.
- Do not put passwords or secret URLs into SSH command arguments; use environment variables or in-memory SSH libraries.
- If a manager slugifies a human label unexpectedly, normalize to the canonical project slug before finishing so future tool names are predictable.
- Treat temporary remote files containing assembled URLs as secrets; delete them even if they are under `/tmp`.
