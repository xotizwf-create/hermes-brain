# Albery Zoom webhook URL validation

Use this when Zoom Marketplace says `URL validation failed. Try again later.` for the Albery `/zoom/events/<secret>` webhook.

## Key lesson from the session

A `200` from the webhook endpoint is not enough to prove Zoom will accept validation. Zoom validates the exact JSON body for `endpoint.url_validation`:

```json
{
  "plainToken": "<payload.plainToken>",
  "encryptedToken": "HMAC_SHA256_HEX(payload.plainToken, Zoom Secret Token)"
}
```

If the server self-test passes but the Zoom UI still fails, the most likely durable cause is that `ZOOM_WEBHOOK_SECRET_TOKEN` on the server does not match the **current Secret Token shown/regenerated in that same Zoom app/subscription**.

## Safe diagnostic sequence

1. Do the normal server preflight first; this is production.
2. Verify that Zoom actually reached the server using nginx/app logs around the owner’s validation click.
   - Zoom Marketplace user-agent may appear as `Zoom Marketplace/1.0a`.
   - A log entry with HTTP `200` means URL reachability is fine; it does **not** prove the HMAC secret is correct.
3. Run a local validation self-test against the public URL with a synthetic `plainToken` and confirm:
   - HTTP `200`;
   - `Content-Type: application/json`;
   - response keys exactly include `plainToken` and `encryptedToken`;
   - `plainToken` echoes the request token;
   - `encryptedToken` equals `hmac.new(ZOOM_WEBHOOK_SECRET_TOKEN, plainToken, sha256).hexdigest()`.
4. If the self-test passes and Zoom still fails, stop trying URL variants. Ask the owner to regenerate/copy the current Zoom **Secret Token** for that exact app and update only `ZOOM_WEBHOOK_SECRET_TOKEN`.
5. Restart only the Albery service, then repeat the self-test and ask the owner to click Validate again.

## Pitfalls

- Do not confuse `ZOOM_EVENT_SECRET` (the path secret in `/zoom/events/<secret>`) with `ZOOM_WEBHOOK_SECRET_TOKEN` (Zoom’s HMAC Secret Token). The first protects the route; the second is used to compute `encryptedToken`.
- Multiple candidate strings from the Zoom UI can look plausible. If one candidate was already on the server and failed, and swapping to another still fails while self-test passes, the UI likely has a newer regenerated token. Request a fresh token instead of cycling old candidates.
- Do not print tokens in chat or logs. Redact route secrets and long tokens in any diagnostic output.
- Keep the endpoint URL unchanged when logs show Zoom reaches it and receives `200`; changing URLs only adds noise.
