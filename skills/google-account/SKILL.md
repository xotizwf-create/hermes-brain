---
name: google-account
description: How the agent is connected to the owner's Google account (read-only) and how to use it — reading Google Calendar, Drive, Docs, Sheets, Slides, and (scope-ready) Gmail. Use when the owner asks about Google access, pastes a Google link, asks "что у меня в календаре / на диске", or when the Google connection needs re-auth / rotation / more scopes. The connection is OAuth with the owner's own account; the token lives server-side only.
---

# Skill: google-account — the agent's Google profile

The agent reads the **owner's own Google account, read-only**, via OAuth. No per-document sharing —
it sees everything the owner can. Set up 2026-05-30.

## What the agent can read & how
- **Google Doc / Sheet / Slides / Drive file** — owner pastes a link → `read-links/fetch_url.py "<url>"`
  (uses the token automatically; Docs/Slides → text, Sheets → all tabs as CSV, `--gid N` for one tab).
- **Google Calendar** — `skills/google-account/scripts/gcal_read.py [--days N] [--max N]` →
  agenda for the next N days (Russian).
- **Gmail** — the `gmail.readonly` scope is granted, but day-to-day mail watching already runs via
  **himalaya** (skill `reminders-and-watchers`, cron `mail-watch`). Add a Gmail-API reader only if the
  owner wants search over the whole mailbox; otherwise prefer himalaya.
- Web pages (non-Google) → see skill `read-links`.

## Where the credential lives (no secret in git)
- Token file — `/root/.hermes/secure/google_oauth_token.json` (mode 600, root-only). Ref name
  `agent/google/oauth-token`. **Never** in git (gitignored). Holds the OAuth refresh token.
- Scopes (read-only): `drive.readonly`, `spreadsheets.readonly`, `calendar.readonly`, `gmail.readonly`.
- The reader code resolves creds in `read-links/scripts/gauth_read.py` and
  `google-account/scripts/gcal_read.py`.
- Some Hermes Google Workspace tools instead expect a compatibility token at
  `/root/.hermes/google_token.json`; see the fallback section below.

## How it was set up (the procedure, for the future)
Google Cloud project `gen-lang-client-0802797266` (owner's). One-time:
1. **Enable APIs** (APIs & Services → Library → Enable): Google **Drive**, **Sheets**, **Calendar**,
   **Gmail** APIs.
2. **Google Auth Platform → Audience**: User type **External**; add the owner as a **Test user**
   (and see "Keep the token alive" below — publish to Production).
3. **Clients (or Credentials) → Create OAuth client ID → Application type: Desktop app** → download
   the `client_secret_*.json`.
4. **Browser login MUST run on the owner's PC** — Google blocks the consent screen from datacenter
   IPs (same as Codex). Run `read-links/scripts/google_oauth_login.py <client_secret.json> token.json`
   (needs `pip install google-auth-oauthlib`). On the consent screen click through the "Google hasn't
   verified this app" warning → **Advanced → Go to … (unsafe)** → **Allow**. It writes `token.json`
   with the refresh token.
5. **Deliver the token to the server** at `/root/.hermes/secure/google_oauth_token.json` (chmod 600).
   Gotcha: Git-Bash mangles `/root/...` args (MSYS path conversion) — prefix `MSYS_NO_PATHCONV=1`, or
   stream the file via base64 over the SSH channel. Never paste the token into chat or commit it.
6. After that the agent works **headless** — google-auth refreshes the access token itself.


## Hermes Google Workspace compatibility token
Some bundled Hermes Google Workspace commands (for example `productivity/google-workspace/scripts/setup.py`
and `google_api.py`) look for the OAuth token at the legacy/default path:

```text
/root/.hermes/google_token.json
```

If the secure Google OAuth token already exists at `/root/.hermes/secure/google_oauth_token.json`, do **not**
make the owner redo OAuth just because `setup.py --check` says `NOT_AUTHENTICATED: No token at
/root/.hermes/google_token.json`. First verify the secure token exists and inspect only non-secret metadata
(scopes/field names, never token values). If it has the needed scopes, install it into the compatibility path:

```bash
install -m 600 /root/.hermes/secure/google_oauth_token.json /root/.hermes/google_token.json
python /root/.hermes/skills/productivity/google-workspace/scripts/setup.py --check
```

Read-only scopes (`drive.readonly`, `spreadsheets.readonly`, `calendar.readonly`, `gmail.readonly`) are enough
for listing/searching Drive, reading Docs/Sheets/Gmail metadata/content, and Calendar reads. They are not enough
for creating, editing, deleting, sending, sharing, or label modifications.

If the Google Workspace scripts fail with `ModuleNotFoundError` and system Python has no usable `pip`, install the
Google API client deps with `uv`:

```bash
uv pip install --system google-api-python-client google-auth-oauthlib google-auth-httplib2
```

Then verify again with `setup.py --check` and use `google_api.py drive search "" --max 10` (or a narrower query)
to confirm Drive access. Keep `/root/.hermes/google_token.json` out of git and treat it as a secret-bearing local
compatibility copy.

## ⚠ Keep the token alive — publish the app to Production
If the OAuth app stays in **Testing**, refresh tokens for sensitive scopes (Drive/Gmail/Calendar)
**expire after ~7 days** → the agent would lose access weekly. Fix: in **Google Auth Platform →
Audience → Publish app** (move Testing → In production; the "unverified" warning is fine for personal
single-user use). If the current token was minted in Testing, **re-run the PC login once after
publishing** to get a long-lived token.

## Security & rotation
- Read-only scopes — the agent cannot edit, send, or delete anything.
- The token grants **read of the owner's whole account**; it lives only in the server secure store
  (600). If the server is compromised, that read access is exposed.
- **Revoke** anytime: myaccount.google.com → Security → **Your connections to third-party apps** →
  remove the app. Then re-run the PC login to reconnect.
- Re-auth (new token): re-run step 4–5; overwrite `/root/.hermes/secure/google_oauth_token.json`.

## Adding write access later (separate trust step)
To let the agent create calendar events, send mail, or edit docs: add the matching **write** scope
(e.g. `calendar.events`, `gmail.send`, `drive.file`) to the SCOPES lists in `google_oauth_login.py`
and the reader modules, re-run the PC login (re-consent), then build the action tool. Keep write
behind explicit owner confirmation, like other outward-facing actions.

## Pointers
- Reading links/docs/sheets/web: skill `read-links`. Mail watcher: skill `reminders-and-watchers`.
- Connector reference: `connectors/google-workspace.md`. Communication rules: `profile/communication.md`.
