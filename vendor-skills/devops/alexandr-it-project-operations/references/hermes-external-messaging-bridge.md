# Hermes external messaging bridge pattern

Use when Александр wants Hermes reachable from a platform that is not supported by the built-in gateway adapters, such as VK.

## Safe MVP architecture

Prefer a small external bridge over editing the live Hermes gateway first:

1. Keep the existing Telegram/Hermes gateway untouched.
2. Put the new bridge behind nginx HTTPS on a single hidden callback path.
3. Bind the bridge only to `127.0.0.1` and expose it through nginx, not a public listening port.
4. Store third-party platform tokens in a root-only `.env`/secret file; never put tokens in code, logs, memory, or skills.
5. Add a user allowlist before calling Hermes or sending any response.
6. Validate the provider callback secret/group/app id before processing events.
7. Acknowledge callback providers quickly (`ok`/confirmation response), then process the user message asynchronously so provider retries do not duplicate long LLM runs.
8. Deduplicate callback events by event id for at least a short TTL.
9. For text-only MVPs, explicitly reject or explain unsupported attachments instead of trying to guess.
10. Use a separate Hermes session/source name for the external platform so conversations do not pollute Telegram context.

## VK-specific notes

- Callback API confirmation requires returning `groups.getCallbackConfirmationCode` for the group.
- VK callback `secret` may reject URL-safe symbols; use an alphanumeric-only secret for compatibility.
- Resolve the owner’s screen name to a numeric VK user id via `users.get` and put that numeric id in the allowlist.
- Enable only the minimal event type for MVP: `message_new` / incoming message.
- `messages.send` needs a unique `random_id` for every send.

## Deployment checks

- Run a lightweight server preflight first on small VPSes; avoid package-heavy installs or builds.
- Verify locally before exposing: `/health`, confirmation payload, invalid group/secret rejection, non-allowlisted user rejection.
- Add nginx config with a backup stored outside active `sites-enabled`; backups left in `sites-enabled` can create duplicate server blocks.
- Run `nginx -t`, reload nginx only if syntax passes, then verify the public HTTPS callback returns the expected confirmation string.
- Install a dedicated systemd unit with restart policy and resource caps. Check `systemctl is-active` and recent logs.

## Security after first setup

If a third-party access token was pasted into chat during setup, recommend rotating it after the first successful end-to-end test and updating the server-side secret store with the new token.