---
id: deployment
type: engineering
tags: [deploy,systemd,nginx,server]
updated: 2026-05-31
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

## Production resource safety (never OOM the box)

**Run the universal preflight first: `engineering/server-preflight.md` (assess → plan budget →
protect → execute).** It is mandatory before any server work and scales from a 512 MB VPS to a big
dedicated box. The deploy-specific notes below assume that preflight has already set your budget.

Hard rule #7 in `CLAUDE.md`. Many client servers are tiny VPSs (≈1 GB RAM, often no swap). A heavy
step on such a box gets OOM-killed by the kernel, which then cascades: the killed Node process drops
its Postgres connections, in-flight auth/payment requests fail, `Set-Cookie`/session writes are lost,
and users see errors. **Assume every prod host is fragile until a preflight proves otherwise.**

**Preflight before any memory-heavy work** (build/bundle/`vite build`, `tsc`/typecheck, full test
suite, a trial/long-running app instance, a bulk migration):

```bash
free -m            # check available + swap
swapon --show      # is there any swap at all?
nproc; uptime      # cores + current load
```

If available RAM is small or there is no swap, **do not run the heavy step on the box.**

**Build off-box, ship a prebuilt release:**
- Build `dist/` and run typecheck + the full test suite **locally or in CI**, on a tested commit.
- Upload the already-built, already-tested release to a timestamped dir
  (`/var/www/<app>/releases/<ts>`). On the server run only: `npm ci`, a `test -f dist/index.html`
  style asset check, and a lightweight smoke check (e.g. one API request on a scratch port).
- Switch atomically (flip the `app` symlink / move) and `systemctl restart` **only** the affected
  services, with the previous release kept as a one-command rollback.
- Keep releases finite: the active release, the immediately previous rollback release, and only a
  small bounded history (usually the last 3–5 timestamped releases). After a successful deploy and
  verification, prune older release directories so the server does not accumulate unbounded copies.

**Never touch live data with non-prod processes:**
- Do not point a trial/dev/test instance or a smoke run at the **production database** — it can
  mutate live rows (e.g. rewrite a device-binding / session row whose cookie never reaches the real
  browser, permanently locking that user out). Use a scratch DB or read-only checks.
- If management access (SSH/`systemctl`) starts timing out mid-deploy, **stop at the safe point** —
  do not switch the release or restart services until the box responds reliably.

**Add a safety margin once, up front:** if a needed box has no swap, add a swapfile before the
deploy (e.g. 2 GB) so a transient spike degrades instead of killing processes — but swap is a
cushion, not a license to run heavy builds on prod.

This is the standing rule behind the 2026-05-31 LiteExams incident, where a server-side `vite build`
on a 1 GB box was OOM-killed (exit 137), dropped DB connections, and contributed to a wave of
"bound to another device" lockouts. The cross-project skill that implements this on real boxes is
`secure-project-server-ops` (its "Low-downtime Node/Vite release workflow").
