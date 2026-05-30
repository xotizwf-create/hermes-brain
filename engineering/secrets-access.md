---
id: secrets-access
type: engineering
tags: [secrets,credentials,ssh,tokens]
updated: 2026-05-29
secret_refs: []
---

# Secrets And Access

Use this guide whenever a task needs credentials, tokens, SSH, GitHub access, service dashboards, APIs, deploy keys, webhooks, or production systems.

## Core Rule

Never store real passwords, tokens, private keys, cookies, or recovery codes in `agent-knowledge`, `agent.md`, git commits, chat messages, logs, command arguments, screenshots, or issue/PR text.

Store secrets only in approved secret stores:

- Server: `/root/.hermes/secure/secrets.yaml`, mode `600`, owner `root:root`.
- Server access map: `/root/.hermes/secure/access-map.yaml`, mode `600`, owner `root:root`.
- Local machine: `.env.local`, `agent-secrets/`, or an external password manager. These paths must stay gitignored.

## How The Agent Should Use Secrets

1. Read `/root/.hermes/secure/access-map.yaml` to identify the project, service, credential name, scope, and allowed use.
2. Read `/root/.hermes/secure/secrets.yaml` only when the task actually needs a secret value.
3. Prefer environment variables, config files, SSH agents, deploy keys, or SDK credential files over passing secrets in command-line arguments.
4. Redact all secret values in outputs. Show only names, last 4 characters, fingerprints, or existence checks.
5. Use least privilege: prefer project-specific deploy keys and scoped tokens over global owner/admin credentials.
6. If a token is missing, expired, over-scoped, or unclear, stop and ask for a replacement rather than improvising.
7. After using a one-time credential, document the location and scope in `access-map.yaml`; do not paste the value into knowledge files.

## Access Map Format

Use `/root/.hermes/secure/access-map.yaml` for non-secret metadata:

```yaml
projects:
  project-key:
    name: Human project name
    repo: git@github.com:owner/repo.git
    production_host: example-host
    working_dir: /var/www/project
    services:
      github:
        credential: github_project_key
        allowed_actions: [clone, pull, push, create_pr]
      database:
        credential: project_database_url
        allowed_actions: [migrate, backup, read, write]
```

Use `/root/.hermes/secure/secrets.yaml` for values:

```yaml
secrets:
  github_project_key:
    type: ssh_private_key
    value_path: /root/.ssh/project_ed25519
    scope: single repository deploy key
  project_database_url:
    type: env
    value: postgresql://user:password@host:5432/db
    scope: project database
```

## GitHub Policy

- Prefer SSH deploy keys per repository for server automation.
- Use fine-grained GitHub tokens only when API actions are required.
- Avoid classic PATs unless no safer option exists.
- Give write access only to repositories where the agent is allowed to push.
- For broad work across many repos, use a dedicated machine user with audited permissions.

### Server GitHub access (live, 2026-05-30)
Hermes (prod) has **account-wide** GitHub access as **`xotizwf-create`** so it can see/clone/edit/
create repos (not just the `hermes-brain` deploy key). Setup:
- `gh` CLI installed on prod (`/usr/bin/gh`).
- Auth = the owner's existing **gh OAuth token reused from the PC** (owner chose speed over a
  dedicated token). Scopes: `repo, read:org, gist` → broad: **read/write to ALL** the owner's repos.
- Token stored secret-free-of-the-brain at `/root/.hermes/secure/github_token` (600) and in
  `/root/.config/gh/hosts.yml`; git uses gh as the credential helper (`gh auth setup-git`). Brain
  holds **no** token — ref only: `agent/github/token`.
- Verify: `gh auth status`, `gh repo list`, `GIT_TERMINAL_PROMPT=0 git ls-remote <private repo>`.
- ⚠ Coupling: it's the **same** token as this PC. If the owner re-runs `gh auth login`/`logout` on the
  PC, the token may rotate and the server breaks → re-run the reuse step (see `logs/changelog.md`
  2026-05-30) or mint a dedicated fine-grained PAT. Consider narrowing to a dedicated token later.

## Owner-pasted secrets (the `.env` ingest exception)
The base rule is "the agent does not type secrets — the owner places them in `secrets.yaml`". There is
**one deliberate exception**: when the owner *pastes* a project's `.env` (or a prod-server password/key)
to Hermes and asks it to remember the project. Then Hermes **receives and stores** it — it must never
**echo, repeat, commit, or invent** a secret. Use skill `store-project-secrets` +
`skills/secure-access/scripts/save_project_secrets.py`, which writes to the secure zone and confirms with
variable **NAMES only**.
- Secure zone layout: `/root/.hermes/secure/projects/<slug>/` — `.env` (600), `server_password`/
  `server_key` (600), `server.txt` (non-secret host/user/port note). Dir 700, root-only.
- Reference names: `proj/<slug>/env`, `proj/<slug>/ssh/root`. Brain manifest keeps NAMES + refs only.
- The pasted message lives in Telegram; Hermes can't delete the owner's DM messages → ask the owner to
  delete their paste. Guarantee = no *further* exposure (not echoed, not in git, 600), not that Telegram forgets.

## Rotation Policy

- Rotate any secret that was pasted into chat, logs, git, or shell history.
- Rotate broad tokens every 90 days.
- Rotate project tokens after team/member changes.
- Remove unused credentials from both the provider and `/root/.hermes/secure/`.

## Verification

Before using production access:

- Confirm the target project from `access-map.yaml`.
- Confirm the current git remote and branch.
- Confirm deploy target and working directory.
- Back up databases before destructive migrations.
- Avoid printing command output that can include secrets.
