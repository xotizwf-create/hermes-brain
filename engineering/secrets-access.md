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
