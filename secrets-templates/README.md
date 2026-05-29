---
id: secrets-templates-readme
type: schema
tags: [secrets, security]
updated: 2026-05-29
secret_refs: []
---

# Secret model

The brain stores **references only**. Real values live on the server, root-only.

## Two files (server-side, NEVER committed)
- `/root/.hermes/secure/access-map.yaml` (mode 600) — non-secret routing:
  project → service → credential **name** + allowed actions. Template: `access-map.template.yaml`.
- `/root/.hermes/secure/secrets.yaml` (mode 600) — real values or `value_path`.
  Template: `secrets.template.yaml`.
- Directory `/root/.hermes/secure` must be mode 700, owner `root:root`.

## Reference namespace
`proj/<slug>/<service>/<credential>` — e.g. `proj/albery/database/url`.
Project manifests and docs cite these names; the `secure-access` skill resolves them to values.

## Rules
- A real secret value in any committed file is a hard error (caught by `scripts/validate.py`).
- Local scratch only in `.env.local` / a password manager — never committed.
- Rotate per `rotate_after` in `secrets.yaml`.

## Verify permissions on server
```bash
python _deploy_helper.py new "stat -c '%a %U:%G %n' /root/.hermes/secure /root/.hermes/secure/access-map.yaml /root/.hermes/secure/secrets.yaml"
```
