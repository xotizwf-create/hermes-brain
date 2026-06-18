---
id: albery-deploy
type: project
project: albery
tags: [deploy]
updated: 2026-06-18
secret_refs: []
---

# Albery — deploy

> General principles: `engineering/deployment.md`.

## Flow
1. Work in a branch off `main` (`feature/...`, `bugfix/...`, `codex/...`), one task per branch.
2. Push to GitHub. Do not push directly to `main` without explicit ask.
3. On server: pull, apply migrations, restart service.

## Commands (on server / via _deploy_helper.py)
```bash
cd /var/www/albery
git status --short && git rev-parse --short HEAD
.venv/bin/python scripts/ensure_postgres.py    # apply migrations
systemctl restart albery
```

## Post-deploy checks
```bash
systemctl status albery --no-pager
journalctl -u albery -n 120 --no-pager
tail -n 120 /var/log/albery/daily-sync.log
nginx -t && systemctl reload nginx
```

## Notes
- Backend listens only on `127.0.0.1:5002`; public access via Nginx.
- Local watcher `scripts/watch_github_updates.ps1` fast-forwards only `main`.
- Push to GitHub before/after server deploy so `update_server.sh` won't overwrite manual edits.

## Pushing a server-made commit when the box has no `gh` / SSH key (2026-06-18)
The Albery prod box (`/var/www/albery`) has **no `gh` CLI and no repo SSH key** (`~/.ssh` empty) and its
`origin` is HTTPS, so `git push` from the box fails with
`fatal: could not read Username for 'https://github.com': No such device or address`.
Push from a host that *is* GitHub-authed (the brain host **217** has `gh` logged in as `xotizwf-create`,
token in `/root/.config/gh/hosts.yml`):

1. **On the box** — commit locally, then export the commit as a patch and copy it to 217:
   ```bash
   cd /var/www/albery && git add <files> && git commit -m "..."
   git format-patch -1 HEAD --stdout > /tmp/change.patch     # uncommitted? use `git diff > ...`
   ```
2. **On 217** — clone fresh (gh's credential helper supplies the token), apply, push:
   ```bash
   git clone https://github.com/xotizwf-create/Albery.git /tmp/albery-push
   cd /tmp/albery-push && git am /tmp/change.patch && git push      # or: git apply + commit
   ```
3. **Reconcile the prod box afterwards — MANDATORY, this is the step that bit us.** `git am`/re-commit
   produces a **new commit hash for the same content**, so the box's local commit and `origin/main` now
   **diverge** (identical tree, different SHA). The local watcher `scripts/watch_github_updates.ps1` is
   **fast-forward-only** and will **refuse** to update a diverged `main` → the manual edit silently stops
   receiving updates / next deploy conflicts. Snap the box to origin **only after a guarded identity check**:
   ```bash
   cd /var/www/albery && git fetch origin
   [ -z "$(git diff HEAD origin/main)" ] && [ -z "$(git status --porcelain -uno)" ] \
     && git reset --hard origin/main || echo "NOT identical/clean — do NOT reset, inspect"
   ```
   The guard (`git diff` empty **and** no tracked modifications) makes `reset --hard` safe: it only moves
   the branch pointer, changes **no files**, and leaves untracked backups in place. **Never `reset --hard`
   without that guard.**
4. **Clean up:** `rm -rf /tmp/albery-push /tmp/change.patch`.
