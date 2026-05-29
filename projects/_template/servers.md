---
id: example-project-servers
type: project
project: example-project
tags: [servers, access]
updated: 2026-05-29
secret_refs: []
---

# {Project name} — servers & access

> Credentials are referenced by NAME only. Real values via `secure-access` skill from
> `/root/.hermes/secure/`. Never print or commit secrets.

## Production
- Host alias: `prod-...`
- Host: `...`
- User: `...`
- Connection: SSH via configured key (`proj/<slug>/ssh/key`)
- Working dir: `/var/www/...`

## Connectivity check (prints nothing secret)
```bash
# verify SSH reachability + service health without revealing secrets
```

## Forbidden
- Не печатать секреты в чат/лог.
- Не коммитить `.env`.
- Не копировать ключи в этот репозиторий.
