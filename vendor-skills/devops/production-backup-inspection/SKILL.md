---
name: production-backup-inspection
description: Use when inspecting backup status, schedules, sizes, or retention on a production server. Covers secure credential handling, SSH without leaking secrets, cron/systemd timer discovery, backup-file identification, log verification, and timezone-aware user reporting.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [devops, backups, cron, systemd, ssh, production, verification]
    related_skills: [systematic-debugging]
---

# Production Backup Inspection

## Overview

Use this skill when the user asks questions like "when was the last backup", "how big is it", "when does the backup run", "is the backup working", or "check backups on server X". The goal is to answer from the live server, not from documentation or memory, while avoiding credential leakage.

Treat backup inspection as a read-only production operation. Do not rotate, delete, run, or reconfigure backups unless the user explicitly asks for that next step. If the request is only informational, gather evidence from schedule definitions, actual logs, and actual files, then report the smallest useful answer.

## When to Use

- A production/server task asks for the latest backup time, size, path, schedule, retention, or success/failure status.
- The server credentials are in a protected secret store and must be used without echoing values.
- The schedule might be defined in `crontab`, `/etc/cron*`, or `systemd` timers.
- The user needs human-facing timezone interpretation, especially when server time differs from the user's default timezone.

Don't use for:

- Creating or changing backup systems from scratch; use a deployment/systemd/database-specific workflow as well.
- Restoring backups; that requires a separate restore plan and explicit confirmation.
- Destructive cleanup of old backups; inspect retention but do not delete without scope confirmation.

## Secure Access Pattern

1. Load project routing/secret metadata first if available; identify the right server and credential names before using secret values.
2. Read secret-bearing files only in a way that avoids printing values. It is safe to print variable names, existence checks, and non-secret metadata.
3. Prefer passing passwords via environment variables or SSH agent/key files. Never put passwords/tokens in command strings, chat, logs, or arguments visible in process listings.
4. If using password SSH from a local automation host, prefer:
   - `SSHPASS` environment variable + `sshpass -e ssh ...`, or
   - a Python SSH library that keeps the password in process memory and does not print it.
5. Redact scripts and logs before displaying if they might contain credentials. Use conservative filters for `PASSWORD`, `PASS`, `PGPASSWORD`, `DATABASE_URL`, and URL credentials.

## Inspection Sequence

### 1. Verify the target server

Run a minimal remote identity check:

```bash
echo OK
hostname
date '+%Y-%m-%d %H:%M:%S %Z %z'
whoami
```

Record server timezone from `date` and, if available, `timedatectl`. This matters because cron and user expectations may be in different timezones.

### 2. Discover schedules

Check both systemd timers and cron. Production backups are often in only one of them.

```bash
systemctl list-timers --all --no-pager | grep -Ei 'backup|dump|postgres|pg|db|baker|timer|project-name' || true
systemctl list-unit-files --no-pager | grep -Ei 'backup|dump|postgres|pg|db|project-name' || true
crontab -l 2>/dev/null || true
for f in /etc/crontab /etc/cron.d/* /etc/cron.daily/* /etc/cron.hourly/* /etc/cron.weekly/* /etc/cron.monthly/*; do
  [ -e "$f" ] || continue
  echo "--- $f"
  grep -nEi 'backup|dump|postgres|pg_dump|db|tar|zip|sql|project-name' "$f" 2>/dev/null || true
done
```

If cron contains `CRON_TZ=...`, treat it as intended timezone, but verify actual execution from syslog/journal before reporting confidently.

### 3. Locate backup artifacts

Search likely backup directories first, then broaden. For DB backups, include plain SQL, compressed SQL, dump files, tarballs, zips, and project-specific names.

```bash
find / -xdev \
  \( -path /proc -o -path /sys -o -path /dev -o -path /run -o -path /snap -o -path /tmp \) -prune -o \
  -type d \( -iname '*backup*' -o -iname '*backups*' -o -iname '*dump*' \) \
  -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort -r | head -100

find / -xdev \
  \( -path /proc -o -path /sys -o -path /dev -o -path /run -o -path /snap -o -path /tmp \) -prune -o \
  -type f \( -iname '*.sql' -o -iname '*.sql.gz' -o -iname '*.dump' -o -iname '*.backup' -o -iname '*.bak' -o -iname '*.tar' -o -iname '*.tar.gz' -o -iname '*.tgz' -o -iname '*.zip' -o -iname '*.gz' \) \
  -printf '%T@|%TY-%Tm-%Td %TH:%TM:%TS|%s|%p\n' 2>/dev/null | sort -nr | head -80
```

Be careful not to misidentify unrelated archives, application exports, package-manager backups, or log rotations as the database/application backup the user asked about. Prefer files whose names, paths, or logs match the backup script/schedule.

### 4. Verify with logs and script

Once you find a likely script or timer, inspect enough to confirm what it produces and where. Redact possible secrets.

```bash
stat -c '%y %s %n' /path/to/backup_script /path/to/backup.log 2>/dev/null
tail -80 /path/to/backup.log 2>/dev/null
find /confirmed/backup/dir -maxdepth 1 -type f -printf '%T@|%TY-%Tm-%Td %TH:%TM:%TS|%s|%p\n' | sort -nr | head -20
```

Cross-check:

- Schedule definition says when it should run.
- Cron/journal/syslog says when it actually ran.
- Log says backup creation succeeded and reports its output path/size.
- Filesystem `stat`/`find -printf` confirms newest artifact and byte size.

If these disagree, report the disagreement plainly instead of smoothing it over.

### 5. Convert sizes and timezones

Use a calculator/tool for byte conversion and current time/date. Report both human formats when useful:

- Decimal MB: `bytes / 1_000_000`
- MiB: `bytes / 1024 / 1024`

For timezone conversion, state the server timezone and the user's timezone interpretation. If the user's default timezone is known, use it; otherwise say "server time" explicitly.

## Reporting Format

Keep the final answer concise and operational:

- Last backup: date/time + timezone
- Size: decimal MB and/or MiB
- Schedule: cron/timer expression translated into human time
- Evidence: only if useful, mention script/log/backup directory path; do not include secrets
- Caveats: include only real discrepancies, e.g. schedule timezone says one thing but syslog shows another

Example:

```text
Проверил сервер.

- Последний бэкап БД: 29 мая 2026, 19:00:02 UTC
- Размер: 40,7 МБ / 38,8 MiB
- Расписание: каждый день в 19:00 по времени сервера; это 22:00 МСК

Нюанс: в cron указан CRON_TZ=Europe/Moscow, но журнал показывает фактический запуск в 19:00 UTC — поэтому расписание лучше считать по фактическому syslog до дополнительной проверки cron-конфига
```

## References

- `references/prostye-postavki-backup-check.md` — example of a real backup inspection with secret-free server details, cron/log/file cross-checks, and timezone caveat.

## Common Pitfalls

1. **Answering from memory or docs.** Backup state is live operational data. Always inspect the server/files/logs.
2. **Leaking credentials while trying to be helpful.** Do not print `.env` values, SSH passwords, DB URLs, or command lines containing secrets.
3. **Trusting schedule without logs.** A cron line tells intent; syslog/journal and backup log tell what actually happened.
4. **Trusting newest archive globally.** The newest `.zip` may be an export, not a backup. Match artifact path/name to the script or log.
5. **Ignoring timezone.** Server UTC, cron `CRON_TZ`, and user local time can all differ. State which one you are using.
6. **Treating setup gaps as durable facts.** Missing `sshpass`, missing Python libraries, or unavailable package managers are environment setup issues. Fix or work around them; do not encode them as claims that the tool cannot be used.
7. **Running backups during inspection.** If the user asked "when was the last backup", do not create a new one just to make the answer look good.

## Verification Checklist

- [ ] Target host, user context, and server time verified.
- [ ] At least one schedule source checked: root crontab, `/etc/cron*`, or systemd timers.
- [ ] Backup artifact path matched to schedule/script/log, not just guessed from newest archive.
- [ ] Latest file timestamp and byte size read from the filesystem.
- [ ] Backup log or journal/syslog checked for actual execution.
- [ ] Timezone conversion included when reporting to a human.
- [ ] No secrets or secret-bearing command lines included in the final answer.
