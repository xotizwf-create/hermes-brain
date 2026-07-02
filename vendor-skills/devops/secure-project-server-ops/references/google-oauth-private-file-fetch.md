# Google OAuth private file fetch fixes

Use this when a production agent already has a working Google OAuth account for creating/editing files, but its URL-reading path still fails on private Google Sheets/Docs.

## Durable lesson

A Google link can be shared with the agent account and still fail if the reader code rewrites it to a public export URL and downloads it with plain HTTP. Public export requests are anonymous; Google does not see the OAuth account.

## Fix pattern

1. Prove the OAuth account and existing Google write tools work before changing code.
2. Locate the URL-reading tool separately from sheet creation/editing tools. It may have a different HTTP-only path.
3. Keep normal web URLs on the existing HTTP path. Only special-case Google hosts:
   - `docs.google.com/spreadsheets/...` → extract spreadsheet id and optional `gid`, then read values through Google Sheets API using the existing OAuth credentials.
   - `docs.google.com/document/...` → export as `text/plain` through Google Drive API using the existing OAuth credentials. Prefer Drive export if Docs API is not enabled; do not enable a new Google API just to read document text unless the owner explicitly wants that operational change.
4. Preserve existing behavior around stripping HTML, max character caps, and returned shape so callers do not need code changes, but **verify the actual return keys** before probing. Albery `fetch_url` currently returns the body in `text`, not `content`; checking the wrong key can make a successful read look empty.
5. Update the tool contract shown to the LLM, not only the Python fetch code. If the MCP/tool description still says “Google Sheets are rewritten to CSV export” or “public Google Doc”, the model may keep explaining/choosing the old anonymous-export mental model even though the runtime code is fixed. Patch the description/input hint to say private Google Sheets/Docs are read with the agent’s authorized Google account, then restart the service that serves the MCP tools.
6. Clear stale business data that now contradicts the fixed behavior. If a registry/company sheet still contains old “Google 401” audit notes, the agent may treat them as current facts. Re-test the listed URLs with the live fetcher and update only the audit/access/status cells for files that now read successfully; leave genuinely forbidden files marked inaccessible.
7. Verify with private test artifacts, not just syntax:
   - create or find a private Sheet shared only with the agent account and confirm the fixed fetch path sees its cell marker;
   - create or find a private Google Doc shared only with the agent account and confirm text export sees its marker;
   - also run `py_compile`/service health checks and restart only the affected app/MCP service;
   - if a separate Hermes gateway caches/discovers tool schemas, restart that gateway too and verify it is active.
8. When the owner says “the fix did not apply”, read the agent’s recent conversation/session if available and compare three layers: (a) live code path, (b) tool schema/description the LLM saw, and (c) source data/knowledge rows the LLM cited. The failure is often in layer (b) or (c), not the OAuth fetch implementation.

## Remote deployment/push pitfall

A production server may have enough access to edit and commit locally but not enough GitHub credentials to push. Do not leave a live-only fix undocumented:

1. Commit locally on the production checkout for rollback/audit.
2. If remote push fails due to missing HTTPS/SSH auth, use the agent's own GitHub access from the controlling environment: fresh clone the canonical repo, copy/apply the exact patched file or diff from prod, commit, and push.
3. Record both hashes in the final report if they differ (server local commit and GitHub commit), and verify prod still compiles/runs after the GitHub sync.

## What not to save as a rule

Transient quoting failures while sending long heredocs over SSH are not themselves durable facts. The reusable tactic is: once an inline remote script becomes fragile, write a local script file, upload it, run it remotely, and verify the target file with `py_compile`/tests before restart.
