# VK → Hermes MVP bridge runbook

Use this when adding or debugging a lightweight VK community bot that forwards messages to a local Hermes CLI/gateway without modifying the existing Telegram gateway.

## Architecture

- Keep VK as a separate bridge service, not a deep Hermes gateway change, for MVP safety.
- Bind the bridge to `127.0.0.1`; expose only one hidden HTTPS Callback API path through nginx.
- Store `VK_GROUP_TOKEN`, callback secret, confirmation code, group id, and allowlisted user id in a root-only `.env`; never put tokens in code or chat/log output.
- Process VK Callback API asynchronously: return `ok`/confirmation immediately, then run Hermes and send the answer back via `messages.send` so VK does not retry slow requests.
- For a personal MVP, enforce a strict VK user-id allowlist and ignore all other senders silently.

## Safe setup checklist

1. Run server preflight first; these VPSes may have ~1 GB RAM. Keep the bridge dependency-free if possible.
2. Create a minimal Python bridge under its own directory and a systemd service with tight scope:
   - localhost bind only;
   - `NoNewPrivileges=true`;
   - small `MemoryMax`;
   - `ReadWritePaths` limited to the bridge dir and Hermes home as needed.
3. Add an nginx location for the Callback URL and verify with `nginx -t` before a soft reload.
4. In VK community settings:
   - configure Callback API URL and secret;
   - enable only `message_new` for the MVP;
   - keep community messages enabled.
5. Verify in order:
   - local `/health`;
   - local `confirmation` POST returns the confirmation code;
   - external HTTPS Callback URL returns the confirmation code;
   - non-allowlisted sender is ignored;
   - a real allowlisted text event produces a VK reply.

## Hermes CLI integration pitfall

Do not start the bridge with `hermes chat --continue <session-name>` unless that named session already exists. Current Hermes exits with:

```text
No session found matching '<session-name>'.
```

A robust bridge should either:

- first call Hermes without `--continue`, then rename the returned `session_id` to the VK session name; or
- detect the “No session found matching” output, retry without `--continue`, and then name the created session.

Capture stderr/stdout only in redacted logs; do not log prompts containing secrets.

## Clearing old VK bot leftovers

If the community had an old bot, old UI may persist even after the new Callback API works.

- Old custom keyboard/buttons can be cleared by sending one message to the user with an empty keyboard payload, e.g. `{"buttons": [], "one_time": true}`.
- Check `groups.getCallbackServers`: there should be only the intended Callback server for the MVP.
- Check `groups.getLongPollSettings`: if the MVP uses Callback API, disable Long Poll so an old poller cannot consume or answer messages in parallel.

## User-facing guidance

Keep the owner-facing message practical and short:

- what was fixed;
- whether Telegram was untouched;
- what to test in VK next;
- if old buttons remain, tell them to reopen the dialog or send another message because VK clients cache keyboards.

Never repeat VK access tokens in replies. If the owner pasted a token in chat, recommend rotating it after the first successful test.
