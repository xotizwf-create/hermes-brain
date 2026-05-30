---
id: google-workspace
type: connector
tags: [google, docs, sheets, drive, service-account, read-links]
updated: 2026-05-30
secret_refs: [agent/google/service-account-key]
---

# Connector: Google Workspace (agent service account)

The agent's own Google identity for reading **private** Google Docs/Sheets/Slides/Drive (read-only).
Used by skill `read-links` (`scripts/gauth_read.py`). Public-by-link docs work even without this.

## How it works
- A Google Cloud **service account** = the agent's Google profile, with an e-mail like
  `hermes-reader@<project>.iam.gserviceaccount.com`. The owner shares a doc/folder with that e-mail
  (role **Viewer**); the agent then reads it via the read-only Drive/Sheets APIs.
- Key file: `/root/.hermes/secure/google_service_account.json` (mode 600, root-only). **Never in git**
  — referenced by name only (`agent/google/service-account-key`). Scopes: `drive.readonly`,
  `spreadsheets.readonly`.
- No interactive login → no datacenter-IP block (unlike OAuth/Codex). Works headless 24/7.

## One-time setup (owner, in Google Cloud Console)
1. console.cloud.google.com → create/pick a project.
2. **APIs & Services → Enable APIs**: enable **Google Drive API** and **Google Sheets API**.
3. **IAM & Admin → Service Accounts → Create**: name e.g. `hermes-reader`. No roles needed (access is
   granted by sharing docs, not IAM).
4. Open the service account → **Keys → Add key → Create new key → JSON** → download the JSON.
5. Note the service-account **e-mail** (ends with `…iam.gserviceaccount.com`).
6. Deliver the JSON to the server as `/root/.hermes/secure/google_service_account.json` (chmod 600).
   (Workspace admins who want ALL company docs without per-file sharing can instead enable
   domain-wide delegation — bigger setup; per-file sharing is simpler and safer.)

## Daily use
- **Share** any doc/folder you want the agent to read with the service-account e-mail (Viewer). Once a
  folder is shared, everything inside is readable.
- Paste the link to the agent → it reads the content. If not shared yet, it replies with the e-mail to
  share with.

## Notes
- Read-only by design (`*.readonly` scopes) — the agent cannot edit or delete anything.
- Limitation: a service account can't see docs that are neither shared with it nor public.
- For an interactive/OAuth profile instead, see `connectors/google-drive.md` (different mechanism).
