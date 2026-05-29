---
name: secure-access
description: Use project credentials, SSH keys, GitHub access, API tokens, service logins, database URLs, webhook secrets, and production access safely. Use whenever Codex must read, create, rotate, verify, or apply credentials or connect to protected projects/services.
---

# Secure Access

## Workflow

1. Read `../../engineering/secrets-access.md`.
2. Identify the target project and service from `/root/.hermes/secure/access-map.yaml`.
3. Read `/root/.hermes/secure/secrets.yaml` only if the task requires the secret value.
4. Use credentials through files, environment variables, SDK config, SSH config, or deploy keys.
5. Never print secret values. Redact logs and command output.
6. Prefer scoped, project-specific credentials over broad credentials.
7. If access is missing, document the needed credential name, scope, and provider instead of inventing a workaround.

## Common Actions

- For GitHub clone/push: prefer SSH deploy key or a dedicated machine user key.
- For GitHub API: prefer fine-grained token with only required repositories and permissions.
- For databases: prefer project `DATABASE_URL` from the secret store, not app config committed to git.
- For webhooks: store signing secrets in project env files and keep endpoint URLs documented without secret path segments when possible.
- For SaaS dashboards: use password manager/manual approval unless an official API token exists.

## Verification

Use `scripts/check_secret_permissions.sh` to verify server secret file permissions.
