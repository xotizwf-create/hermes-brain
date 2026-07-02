# Remote Hermes `openai-codex` device-code re-auth

Use this reference when a remote Hermes gateway needs a fresh `openai-codex` OAuth session and the normal `hermes auth add openai-codex --type oauth`/interactive SSH path hangs or does not stream the device-code prompt.

## Durable lessons

- Prefer a clean per-agent re-auth over copying another agent's refresh token. Shared refresh tokens can invalidate each other.
- Treat the OpenAI Codex flow as **device-code auth**, not browser callback auth: the user opens `https://auth.openai.com/codex/device` and enters a short code.
- Do not print or store access/refresh tokens in conversation logs. Only show the user the device URL and short user code.
- If SSH/Python wrappers buffer or hide the prompt, probe the device-code endpoint directly from the remote Hermes venv and then run a small remote poller that saves the returned token into Hermes' credential pool.
- Keep the polling process running while the owner confirms the login, then verify with a real model ping and restart only the affected gateway service.

## Safe flow

1. Parse the local project secure `.env` with Python; do not `source` it unless you already know it contains only shell-safe assignments. Some secure files include human notes.
2. Confirm remote Hermes location/profile/service from systemd or the project card. For Albery, the live legacy server can differ from the newer Andigital host.
3. From the remote Hermes checkout/venv, verify a direct device-code request works:
   ```bash
   ./venv/bin/python -u - <<'PY'
   import httpx
   from hermes_cli import auth as a
   r = httpx.post(
       'https://auth.openai.com/api/accounts/deviceauth/usercode',
       json={'client_id': a.CODEX_OAUTH_CLIENT_ID},
       headers={'Content-Type': 'application/json'},
       timeout=15,
   )
   print('status', r.status_code)
   print(r.text[:200])  # contains user_code/device_auth_id, no OAuth tokens yet
   PY
   ```
4. Show only the URL and `user_code` to the owner. Ask them to sign in with the paid/Plus account.
5. While they sign in, run a remote poller with the returned `device_auth_id` + `user_code`; after success exchange the authorization code using `auth_mod.CODEX_OAUTH_TOKEN_URL`, add a `PooledCredential(provider='openai-codex', auth_type=AUTH_TYPE_OAUTH, source='manual:device_code')` via `load_pool('openai-codex').add_entry(entry)`, and never print token values.
6. Clear stale `last_status`/`exhausted` auth markers if the old credential was marked failed, then smoke-test a one-line prompt through the exact remote Hermes home/profile.
7. Restart only the remote Hermes gateway service and inspect fresh logs for `openai-codex` auth errors.

## Pitfalls

- A command that appears to “hang before printing the code” may simply be hidden by SSH/heredoc buffering or by an import/wrapper path. Test the raw HTTP device-code call separately before changing provider config.
- `sshpass -p` leaks passwords through argv in timeout/error output. Use `SSHPASS` + `sshpass -e`.
- Killing broad process patterns over SSH can match the current shell/awk/grep and terminate your own diagnostic command. Prefer read-only `ps` first and exact PIDs only when cleanup is necessary.
- Do not solve a remote Codex auth failure by switching permanently to an unrelated provider unless the owner explicitly wants that trade-off; when a paid Plus account exists, re-auth is usually the cleaner first fix.
