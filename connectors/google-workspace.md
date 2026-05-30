---
id: google-workspace
type: connector
tags: [google, docs, sheets, drive, oauth, read-links]
updated: 2026-05-30
secret_refs: [agent/google/oauth-token]
---

# Connector: Google (agent reads the owner's Drive, read-only)

The agent's Google profile = **the owner's own Google account via OAuth, read-only**. The agent reads
**everything the owner can access** — no per-document sharing. Used by skill `read-links`
(`scripts/gauth_read.py`). Public-by-link docs work even without this.

## How it works
- One-time browser consent on the **owner's PC** (Google blocks the consent screen from datacenter
  IPs — same issue as Codex), which yields a **refresh token**. We copy it to the server; after that
  the agent works headless, refreshing access tokens itself, no further logins.
- Token file: `/root/.hermes/secure/google_oauth_token.json` (mode 600, root-only). **Never in git**
  (gitignored) — referenced by name only (`agent/google/oauth-token`). Scopes: `drive.readonly`,
  `spreadsheets.readonly` (read-only — the agent cannot edit or delete anything).
- Reads via the Drive/Sheets APIs: Docs/Slides → text, Sheets → all tabs as CSV.

## One-time setup
**A. In Google Cloud Console (owner):**
1. console.cloud.google.com → create/pick a project.
2. **APIs & Services → Enable APIs**: enable **Google Drive API** and **Google Sheets API**.
3. **OAuth consent screen**: User type **External**; fill app name + your email; add scope
   `…/auth/drive.readonly`; add **yourself as a Test user** (lets you consent without app verification).
4. **Credentials → Create credentials → OAuth client ID → Application type: Desktop app** → download
   the client JSON (`client_id` + `client_secret`).

**B. Login on the PC (driven by the agent on the workstation):**
- `skills/read-links/scripts/google_oauth_login.py <client_secret.json>` → opens the browser, you
  consent → writes `token.json` (refresh token). Needs `pip install google-auth-oauthlib`.

**C. Deliver to the server:**
- `token.json` → `/root/.hermes/secure/google_oauth_token.json` (chmod 600). Then private docs work.

## Daily use
- Just paste any Google Doc/Sheet/Slides link to the agent — it reads it (yours, no sharing needed).
- Multi-tab sheets come back tab-by-tab; `--gid <N>` for one tab.

## Security notes
- The token grants **read** of the owner's whole Drive. It lives only in the server secure store
  (600). If the server is compromised, that read access is exposed — rotate by revoking the token in
  the Google account (Security → Third-party access) and re-running the login.
- Read-only scopes — no write/delete possible.

## Alternative: service account
Instead of the owner's account, a Google **service account** can be used (the agent gets its own
e-mail; you share specific docs/folders with it). Safer blast radius, no login, but requires per-doc
sharing. `gauth_read.py` supports it too via `/root/.hermes/secure/google_service_account.json`.
For the interactive OAuth MCP-layer connector (different mechanism) see `connectors/google-drive.md`.
