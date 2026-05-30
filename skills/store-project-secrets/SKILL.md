---
name: store-project-secrets
description: Use when the owner wants Hermes to securely take a project's secrets and remember the project — "найди на гитхабе проект X", store its .env / prod-server password, connect later. PRIMARY secure intake is the owner running secret_push.py on their PC to SFTP the .env straight into the server secure zone (never through Telegram or any LLM); pasting into chat is a discouraged fallback that exposes the secret (rotate after). Secrets land in /root/.hermes/secure/projects/<slug>/ (600, never echoed/committed) via save_project_secrets.py; Hermes records secret-free memory (repo, prod host/user, variable NAMES, refs) in projects/<slug>/.
---

# Skill: store-project-secrets

The owner says "запомни проект X", pastes its `.env` (and prod-server access); Hermes locks the values
into the secure zone and remembers the project. **This is the deliberate exception** to "the agent does
not type secrets" (`engineering/secrets-access.md`): *receiving* a pasted secret and storing it is
allowed; echoing, repeating, committing, or inventing it is not.

Helper: `skills/secure-access/scripts/save_project_secrets.py` → on prod
`/root/.hermes/agent-knowledge/skills/secure-access/scripts/save_project_secrets.py`.

## Golden rules (HARD)
1. **Never show a secret value** — not the `.env`, not a password/key, not a DB URL. Confirm with
   variable **NAMES only** (the helper prints exactly that). Never paste the value back "to double-check".
2. **Secrets only in the secure zone** `/root/.hermes/secure/projects/<slug>/` (dir 700, files 600,
   root-only). **Never** in the brain/git, never in a chat reply, never in a command-line argument.
3. **Brain = secret-free memory.** `projects/<slug>/project.yaml` holds repo, prod host/user, working
   dir, variable **NAMES**, and `secret_refs` — never values.
4. The owner pasted the secret into Telegram, so it exists in that chat. Hermes can't delete the
   owner's messages in a DM → **tell the owner to delete their paste** after you confirm it's stored.
   Be honest: you guarantee no further exposure (not echoed, not in git, 600 on the server), not that
   Telegram forgets it.

## Flow

### 1. Find the repo (gh is authed on prod as `xotizwf-create`)
```bash
gh repo list --limit 100 | grep -i "<query>"      # or: gh search repos "<query>" --owner xotizwf-create
gh repo view <owner>/<name> --json nameWithOwner,description,visibility,url
```
Show the owner the match, agree on a stable **slug** (kebab-case, == repo name is fine). Don't invent
a slug silently — confirm.

### 2. Store the `.env` — secure intake (PRIMARY: never through chat/LLM)
A secret pasted into Telegram has **already left the server** — it goes to Telegram *and* into the LLM
provider's context. So the secure path is **the owner pushes the file from their PC straight into the
secure zone over SSH**, bypassing the bot and the model entirely:
```text
# on the owner's PC:
python skills/secure-access/scripts/secret_push.py <slug> <path-to-.env>
```
`secret_push.py` SFTPs the file into `/root/.hermes/secure/projects/<slug>/.env` (600) via the server
helper and prints variable **NAMES only**. The value never touches Telegram or any LLM. Tell the owner
this is the way; you (Hermes) only get told the slug + names afterwards and then do step 4 (memory).

**Emergency fallback only (discouraged): owner pastes the `.env` into chat.** If the owner insists,
write the pasted text to a temp file with your file tool (never into a shell command string), then:
```bash
python3 .../save_project_secrets.py save-env <slug> --from /tmp/_paste_<slug>   # temp is shredded
```
Relay the helper's names-only line, remind the owner to **delete their paste**, and **treat those
secrets as exposed — schedule rotation** (they passed through Telegram + the LLM). Prefer `secret_push.py`.

### 3. Store prod-server access (so Hermes can connect later)
Host + user are **not** secret → they go in the manifest. The password or private key **is** secret →
secure zone via the helper (secret via temp/STDIN, never argv):
```bash
python3 .../save_project_secrets.py save-server <slug> --host <ip/domain> --user <u> [--port N] --as password   # secret on STDIN
# or  --as key   for a private key
```

### 4. Remember the project in the brain (secret-free) — approval-gated
Create `projects/<slug>/` from `projects/_template/` (skill `add-project`): fill `project.yaml` with the
repo URL, `production.host`/user/working_dir, the env variable **NAMES** (handy memory of what config
exists — names only), and `secret_refs`:
```yaml
secret_refs:
  - proj/<slug>/env            # -> /root/.hermes/secure/projects/<slug>/.env
  - proj/<slug>/ssh/root       # -> /root/.hermes/secure/projects/<slug>/server_password|server_key
```
Add a matching `access-map.yaml` entry server-side (service `env` → value_path the secure `.env`;
service `server-root` → the secret name; `allowed_actions`). Regenerate registry, `scripts/validate.py`,
show the diff, commit after the owner's ok, push (so PC + server share the memory). See `update-knowledge`.

### 5. Recall / use later
- "что у меня по проекту X" → `save_project_secrets.py show <slug>` (names + which secrets exist, no
  values) + read `projects/<slug>/` for the memory.
- Need to connect to prod / read the `.env` for a task → `secure-access` skill: read the secure file,
  use it through env/ssh, **never print it**. Connect with the stored host/user + `server_password`/`server_key`.
- Work on the code → `project-onboarding` (clone with the gh credential, branch, PR).

## Done when
`.env` (and any prod-server secret) is in the secure zone (600, confirmed by NAMES only), the project is
registered secret-free in the brain (manifest + access-map + registry + validator pass, committed), and
`show <slug>` lists it. The owner has been reminded to delete their pasted message.
