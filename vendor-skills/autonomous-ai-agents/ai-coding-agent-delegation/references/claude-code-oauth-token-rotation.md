# Claude Code OAuth token rotation notes

Use this when rotating a long-lived Claude Code OAuth token for a server-side Claude Code bridge/bot.

## Safe sequence

1. Read the project/runbook first for the exact bridge process, token file, service manager, and expected environment variable (`CLAUDE_CODE_OAUTH_TOKEN` or token-file wiring).
2. Preflight the host before spawning interactive CLIs, especially on ~1 GB VPS boxes: `free -m`, swap, disk, and current process manager status. Do not run builds or heavy diagnostics on the production box.
3. Record the current token file metadata only (`stat` mode/bytes/mtime), never the token value. Keep mode `600`.
4. Choose the correct Claude Code flow before asking the owner for a browser code:
   - `claude setup-token` creates/rotates a long-lived token for bridge-style `CLAUDE_CODE_OAUTH_TOKEN` usage.
   - `claude auth login --claudeai` logs the local Claude Code CLI into a Claude subscription and is what fixes `Not logged in · Please run /login` for normal `claude -p ...` use.
   - Authorization codes are bound to the exact command/URL attempt. If you started the wrong flow, stop it cleanly and ask for a fresh code from the new URL; do not reuse a code from `setup-token` for `auth login` or vice versa.
5. Run the selected command in a real PTY/background session so the owner can open the URL and paste the returned code. Prefer direct `terminal(..., pty=true, background=true)` plus `process.submit`; if wrapping with Python/PTY, do not exit just because background stdin is initially EOF.
6. Treat the returned browser value as sensitive. It may appear as `authorization_code#state`. For `claude auth login --claudeai`, if submitting only the part before `#` returns `Invalid code. Please make sure the full code was copied.`, immediately retry the same prompt with the full `authorization_code#state` fragment before asking the owner for a new browser code. For other flows, follow the CLI prompt/docs; do not blindly strip or blindly include the fragment.
7. If a live `claude auth login --claudeai` process is waiting on a PTY that is not attached to Hermes' process manager, `TIOCSTI` injection into the process' `/dev/pts/N` can submit the code; writing to `/dev/pts/N` normally may echo to output instead of feeding stdin. After submission, verify with `claude auth status` and a real lightweight Claude request using the same environment as the bridge or CLI, not by reading the token aloud. For normal local auth, `claude auth status` should report `loggedIn: true`, then a tiny `claude -p` smoke test should succeed.
8. Restart only the bridge process/service when a bridge token changed, then check status and fresh logs.

## Pitfalls

- Hermes/process output and some terminals may mask the final long-lived token as `*****` or otherwise redact it. Do not assume asterisks are the token. First check whether the target token file changed.
- If `setup-token` appears to hang after code submission, avoid repeated blind retries that invalidate URLs. Check process status, token-file mtime, and any CLI state/config locations without printing secrets.
- Do not confuse the two Claude Code OAuth surfaces: `setup-token` can complete or hang without making `claude auth status` logged in. If a later `claude -p` says `/login`, switch to `claude auth login --claudeai` and get a new browser code.
- Codes are single-attempt and URL-bound. When the CLI generates a new URL, tell the owner plainly that the previous code is stale and keep the waiting process open while they fetch the new code.
- When reading a code from a screenshot, crop/enlarge the input field and verify ambiguous glyphs (`0/O`, `l/1/I`) before submitting. A mistyped code wastes the whole OAuth attempt.
- If you need to capture raw CLI output for troubleshooting, write it only to a root-only secure or outbox file, immediately parse/save the token without displaying it, then remove the capture. Never paste raw token output into Telegram.
- Running `claude` manually without the bridge's `CLAUDE_CODE_OAUTH_TOKEN` can falsely look unauthenticated. Test exactly the bridge invocation/environment.
- Do not overwrite a known-good token until the new token has been validated.
