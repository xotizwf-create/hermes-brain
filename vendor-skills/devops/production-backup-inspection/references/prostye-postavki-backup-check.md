# Простые поставки — backup inspection example

Session date: 2026-05-30

This is a secret-free example for the `production-backup-inspection` skill. Do not store IPs, passwords, DB credentials, or MCP secrets here unless they are already public and approved for documentation.

## What was known

- Project: «Простые поставки» / `prostye-postavki`
- Secret-bearing server login file: `/opt/hermes/secure/projects/prostye-postavki/.env`
- Safe variable names in that file: `IP`, `USER`, `PASSWORD`
- Server hostname observed after SSH: `miramed32`

## Access pattern used

1. Read only the variable names from the `.env` first to confirm the shape.
2. Load values inside a local script without printing them.
3. Use password SSH with `SSHPASS` environment variable and `sshpass -e ssh ...`, so the password is not in the command line.
4. Run read-only remote commands.

## Findings

- Root crontab contained:
  - `CRON_TZ=Europe/Moscow`
  - `0 19 * * * /usr/local/bin/prostavki_db_backup.sh >> /var/log/prostavki_db_backup.log 2>&1`
- Backup script: `/usr/local/bin/prostavki_db_backup.sh`
- Backup log: `/var/log/prostavki_db_backup.log`
- Backup directory: `/root/db_backups`
- Script behavior: creates plain SQL dumps named `prostavki_<timestamp>.sql` and deletes matching dumps older than 7 days

Latest confirmed DB backup at the time:

- File: `/root/db_backups/prostavki_2026-05-29_19-00-01.sql`
- Filesystem mtime: `2026-05-29 19:00:02 UTC`
- Size: `40,718,327` bytes = `40.7 MB` decimal / `38.8 MiB`

Previous related backups also existed:

- `/root/db_backups/prostavki_2026-05-28_19-53-22.sql`
- older compressed one-off files in `/root/prostavki_db_backup_*.sql.gz`

## Timezone caveat

The server timezone was UTC (`Etc/UTC`). Although the crontab included `CRON_TZ=Europe/Moscow`, syslog showed the actual 2026-05-29 run at `19:00:01` server time, and the backup file/log were created at `19:00:02` UTC.

When reporting to Александр, say:

- observed schedule/run: 19:00 server time / UTC
- Moscow interpretation of the observed run: 22:00 MSK
- caveat: cron contains `CRON_TZ=Europe/Moscow`, but actual syslog evidence showed 19:00 UTC, so treat the observed behavior as authoritative unless further cron-version/timezone testing is done

## Reporting style that worked

Keep it short:

- Last backup time
- Size
- Schedule translated to MSK
- One caveat if schedule timezone and actual syslog behavior differ
