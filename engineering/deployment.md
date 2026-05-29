---
id: deployment
type: engineering
tags: [deploy,systemd,nginx,server]
updated: 2026-05-29
secret_refs: []
---

# Server And Deploy Standards

Use this guide for Linux server setup, deploys, services, nginx, logs, and production operations.

## Defaults

- Confirm host, user, project directory, git remote, branch, and service name before changing production.
- Use systemd for long-running services.
- Use nginx or the existing reverse proxy pattern for public HTTP services.
- Store project env in root-owned `.env` or systemd environment files, never in git.
- Keep deploy commands repeatable and documented.

## Deploy Workflow

1. Check `git status --short`, current branch, and current commit.
2. Pull or upload code using the project's established deploy path.
3. Install dependencies only with the project's lockfile/package manager.
4. Run migrations if required.
5. Run focused tests or smoke checks.
6. Restart/reload the service.
7. Check service status and recent logs.

## Safety Rules

- Back up configs before editing `/etc`, systemd units, nginx sites, or production env files.
- Prefer `systemctl reload` when supported; use restart when code/env changed.
- Do not expose secrets in process listings or shell history.
- Keep firewall changes minimal and reversible.
- Record non-obvious production changes in project documentation.
