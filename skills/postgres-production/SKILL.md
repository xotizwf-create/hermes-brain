---
name: postgres-production
description: Install, configure, harden, back up, restore, migrate, and operate PostgreSQL for production or staging servers. Use when Codex needs to set up PostgreSQL, create databases or roles, design production-safe migration steps, configure backups, inspect slow queries, or recover data.
---

# Postgres Production

## Workflow

1. Confirm host, project, database name, database owner, expected app user, and backup location.
2. Read `../../engineering/secrets-access.md` before handling credentials.
3. For installation or hardening, read `references/install-hardening.md`.
4. For backups or restore work, read `references/backup-restore.md`.
5. For migrations, follow `../../engineering/database.md`.
6. Before destructive work, make a backup and verify the target database.
7. After changes, verify connectivity, service status, logs, and the application health check.

## Defaults

- Prefer one database role per application.
- Do not use the PostgreSQL superuser in application connection strings.
- Store `DATABASE_URL` only in root-owned env files or the approved secret store.
- Use `pg_dump` for logical backups before risky migrations.
- Use system package PostgreSQL unless the project already standardizes on Docker.

## Useful Scripts

- `scripts/check_postgres.sh`: checks service, readiness, version, databases, and basic disk information.
