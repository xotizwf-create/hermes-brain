# PostgreSQL Backup And Restore

## Backup Before Risky Work

Use a timestamped file and keep it outside the web root:

```bash
mkdir -p /root/backups/postgres
pg_dump --format=custom --file=/root/backups/postgres/project_$(date +%Y%m%d_%H%M%S).dump "$DATABASE_URL"
```

## Verify Backup

```bash
pg_restore --list /root/backups/postgres/project_YYYYmmdd_HHMMSS.dump | head
```

## Restore Pattern

- Restore into a new database first when possible.
- Confirm the target database before overwriting data.
- Stop application writes during a destructive restore.
- Keep the original backup until the application is verified.

## Scheduled Backups

- Use a project-specific script or systemd timer.
- Log backup success/failure.
- Periodically test restore, not just dump creation.
- Keep credentials in root-only env files or the approved secret store.
