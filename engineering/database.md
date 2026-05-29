---
id: database
type: engineering
tags: [db,migrations,backups,postgres]
updated: 2026-05-29
secret_refs: []
---

# Database Standards

Use this guide for schema design, migrations, PostgreSQL setup, backups, and production data changes.

## Defaults

- Prefer PostgreSQL for production unless a project has an established different database.
- Use explicit migrations. Do not edit production schema manually without capturing the migration.
- Use `created_at`, `updated_at`, and stable primary keys for business tables.
- Add indexes for lookup and join paths that are actually used by queries.
- Keep secrets out of migrations and seed files.

## Production Change Workflow

1. Inspect existing schema, migrations, and application data access patterns.
2. Create a forward migration and, when practical, a rollback migration.
3. Test migration locally or on staging with representative data.
4. Make a production backup before applying destructive or large migrations.
5. Apply migration through the project's standard command.
6. Verify application health, logs, and key queries.

## Safety Rules

- Never run destructive SQL on production without a backup and explicit target confirmation.
- For large tables, avoid blocking rewrites where possible.
- Prefer additive migrations before application deploys, then cleanup migrations later.
- Use transactions when the migration tool and operation support it.
- Document operational commands in the project notes after a new pattern is established.

## When To Use Skill

For installing, hardening, backing up, restoring, or operating PostgreSQL, use `agent-knowledge/skills/postgres-production/SKILL.md`.
