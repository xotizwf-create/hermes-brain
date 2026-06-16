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
- **Google Sheets / Drive write + Apps Script projects** — full-access token installed 2026-06-16 at the same secure token paths. Verified after enabling `script.googleapis.com` for project `700568547840`: creating a spreadsheet, writing cells, creating a bound Apps Script project, uploading `Code` + `appsscript` files, reading script content back, and building a working Sheets dashboard with formulas, validation, formatting, Apps Script menu, and charts all work. If Apps Script REST calls fail with `SERVICE_DISABLED`, use activation URL `https://console.developers.google.com/apis/api/script.googleapis.com/overview?project=700568547840`. The `script.google.com/home/usersettings` toggle alone is not enough for REST project creation. For the repeatable build/verify workflow, see `references/sheets-apps-script-automation.md`.
- **Google Calendar (read + WRITE)** — read agenda via `skills/google-account/scripts/gcal_read.py
  [--days N] [--max N]` (Russian) or the bundled `google_api.py calendar list`. **Create/delete events**
  via the bundled tool: `python3 /root/.hermes/skills/productivity/google-workspace/scripts/google_api.py
  calendar create --summary "…" --start "2026-05-31T12:00:00+03:00" --end "…+03:00" [--description/--location/--attendees]`
  and `… calendar delete <event_id>`. Times are ISO 8601 **with** timezone (MSK = `+03:00`). Editing an
  event = delete + create. Writes are outward-facing → confirm with the owner first (per `profile/`).
- **Gmail** — the `gmail.readonly` scope is granted, but day-to-day mail watching already runs via
  **himalaya** (skill `reminders-and-watchers`, cron `mail-watch`). Add a Gmail-API reader only if the
  owner wants search over the whole mailbox; otherwise prefer himalaya.
- Web pages (non-Google) → see skill `read-links`.

## Where the credential lives (no secret in git)
- Token file — `/root/.hermes/secure/google_oauth_token.json` (mode 600, root-only). Ref name
  `agent/google/oauth-token`. **Never** in git (gitignored). Holds the OAuth refresh token.
- Scopes: `drive.readonly`, `spreadsheets.readonly`, **`calendar` (read/write)**, `gmail.readonly`,
  **`gmail.send`**. Calendar upgraded 2026-05-30; **gmail.send added 2026-06-11** (re-consent on the
  PC) — отправка писем живёт в skill `skills/send-email/` (Gmail API по HTTPS, потому что исходящий
  SMTP на 217 заблокирован хостером). Drive/Sheets stay read-only.
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

Current scopes: `drive.readonly`, `spreadsheets.readonly`, **`calendar`** (read/write),
`gmail.readonly`, **`gmail.send`** (2026-06-11). Enough for listing/searching Drive, reading
Docs/Sheets/Gmail, Calendar read/write — **and sending mail as the owner** (use
`skills/send-email/scripts/gmail_send.py`, NOT SMTP — outbound SMTP is provider-blocked on 217).
Still NOT enough for editing Docs/Sheets or sharing (those would need their own write scopes —
see "Adding write access later").

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
- Scopes are read-only **except Google Calendar** (read/write) and **Gmail send** (`gmail.send`,
  added 2026-06-11 — the agent can send mail as the owner; keep both behind owner confirmation).
  It still cannot edit Docs/Sheets or delete Drive files/mail.
- The token grants **read of the owner's whole account** (+ Calendar write); it lives only in the server secure store
  (600). If the server is compromised, that read access is exposed.
- **Revoke** anytime: myaccount.google.com → Security → **Your connections to third-party apps** →
  remove the app. Then re-run the PC login to reconnect.
- Re-auth (new token): re-run step 4–5; overwrite `/root/.hermes/secure/google_oauth_token.json`.

## Adding write access later (separate trust step)
Pattern (done for Calendar 2026-05-30 and for `gmail.send` 2026-06-11): add the matching
**write** scope to the SCOPES list in `read-links/scripts/google_oauth_login.py`, re-run the PC login
(re-consent in the browser), deliver the new token to **both** `/root/.hermes/secure/google_oauth_token.json`
and the bundled-tool compat path `/root/.hermes/google_token.json` (600), then use the action tool
(`google_api.py`). For more: `gmail.send`, `drive.file`/`drive`, `spreadsheets`. Keep every write behind
explicit owner confirmation, like other outward-facing actions.

### Apps Script / full Google automation scopes
If the owner wants the agent to create/edit Sheets and bind/manage Apps Script projects, the existing
read-only Drive/Sheets token is not enough. Prepare a PC-side OAuth login bundle that requests at least:

- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/script.projects`
- `https://www.googleapis.com/auth/script.deployments`
- keep any already-needed Calendar/Gmail scopes if the same token should replace the existing one.

Owner-side prerequisites/pitfalls:

1. The owner must enable Apps Script API at `https://script.google.com/home/usersettings` before Apps
   Script API calls work.
2. Windows `.bat` launchers are fragile with Cyrillic paths/OneDrive/Desktop folders and UTF-8 BOM/codepage
   quirks. Prefer giving a simple manual fallback in every bundle README:
   - unpack to `C:\google-auth` (ASCII path, no spaces/Cyrillic);
   - open that folder, type `cmd` in Explorer address bar;
   - run `py -3 authorize_google_full_access.py`, or `python authorize_google_full_access.py` if `py` is absent.
3. If a screenshot shows commands like `orize_google_full_access.py`, Russian explanatory text being executed
   as commands, or `@echo off` rendered incorrectly, do not debug Google/OAuth first — the batch file text or
   quoting/encoding is broken and the Python script never started. Use the manual command above or replace the
   launcher with a minimal ASCII-path-safe version.
4. The resulting token file is secret-bearing. Ask the owner to send it as a document/file, never paste token
   contents into chat.

## Pointers
- Reading links/docs/sheets/web: skill `read-links`. Mail watcher: skill `reminders-and-watchers`.
- Connector reference: `connectors/google-workspace.md`. Communication rules: `profile/communication.md`.
