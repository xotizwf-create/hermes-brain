---
id: server-preflight
type: engineering
tags: [server, preflight, safety, resources, capacity, oom, deploy, migration]
updated: 2026-05-31
secret_refs: []
---

# Universal Server Preflight — assess, plan, protect, then work

**Mandatory before ANY work on a server** (deploy, build, migration, bulk import, long-running
process, heavy query) — on a 512 MB VPS and on a 64 GB dedicated box alike. The rule is **not**
"small box = be careful". The rule is: **always reason from the server's current headroom, never
from habit or from how the last box behaved.** The order is fixed and you never skip ahead:

> **1) ASSESS → 2) PLAN a budget → 3) PROTECT → 4) EXECUTE within the budget.**

This is what was missing in the 2026-05-31 LiteExams incident: a `vite build` + full test suite ran
on a 1 GB / no-swap box, got OOM-killed, dropped DB connections, and locked users out. The protocol
below makes that impossible to repeat regardless of server size.

## 1. ASSESS — read-only, costs nothing, do it first

```bash
CORES=$(nproc)
TOTAL=$(free -m | awk '/^Mem:/{print $2}')        # total RAM MB
AVAIL=$(free -m | awk '/^Mem:/{print $7}')        # available RAM MB (free + reclaimable)
SWAPF=$(free -m | awk '/^Swap:/{print $4}')       # free swap MB
LOAD1=$(awk '{print $1}' /proc/loadavg)           # 1-min load
DISKF=$(df -Pm . | awk 'NR==2{print $4}')         # free disk MB on the working FS
echo "cores=$CORES total=${TOTAL}M avail=${AVAIL}M swapfree=${SWAPF}M load1=$LOAD1 diskfree=${DISKF}M"
systemctl list-units --type=service --state=running --no-pager | grep -iE 'app|api|bot|node|python|nginx|postgres|mysql|redis|pm2' || true
```

Record: cores, total/available RAM, free swap, 1-min load, free disk, **which running services serve
users** (app / API / bot / DB / proxy), and **whether this is production** (live users or a live DB).
If it's production, every later step is also bound by the deploy-safety rules in `deployment.md`.

## 2. PLAN — derive a memory budget from the numbers (don't guess)

Keep a reserve for the OS + live services at all times, then the rest is the budget for your work:

```bash
RESERVE=$(( TOTAL/5 > 512 ? TOTAL/5 : 512 ))      # reserve max(20% of RAM, 512 MB)
BUDGET=$(( AVAIL - RESERVE ))                       # MB your operation may use on-box
echo "reserve=${RESERVE}M budget=${BUDGET}M"
```

Then decide, by comparing the operation's **expected peak memory** to `BUDGET`:

- **If `BUDGET <= 0`, or the op's peak clearly exceeds `BUDGET`, or you cannot bound its peak →
  run it OFF the box** (build `dist/` + typecheck + full tests locally or in CI) and ship only the
  prebuilt, tested artifact. On the box do only light steps (`npm ci`, asset check, one smoke call).
- **If the peak fits inside `BUDGET` →** you may run it on-box, but **always capped + de-prioritised**
  (step 4), never bare.

Tiers are just a sanity shortcut for the same math:

| Available RAM / swap | Tier | On-box heavy work (build/tests/migration)? |
|---|---|---|
| `< ~1 GB` avail **or no swap** | Constrained | **No.** Off-box only. Add swap first (step 3). |
| `~1–4 GB` avail, swap present | Moderate | Only if peak fits `BUDGET`, and only capped + niced. |
| `> ~4 GB` avail, `load1 < cores` | Roomy | Yes, still capped + niced. |

**Non-negotiable regardless of tier:**
- **Never run a build / test suite / migration against the LIVE production database.** Use a scratch
  DB, a disposable schema, or a transaction you roll back. A stray process on the prod DB can mutate
  live rows (e.g. rewrite a session/binding row) and break users.
- **Have rollback ready before you mutate** (previous release kept, symlink/backup, DB dump for
  migrations).
- **Stop if management access degrades** (SSH / `systemctl` start timing out) — do not switch a
  release or restart services until the box responds reliably.

## 3. PROTECT — make a mistake survivable before you make it

```bash
# a) If constrained and there is no swap, add a cushion ONCE (size ~= max(2G, RAM)).
if [ "$SWAPF" -eq 0 ]; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# b) Tell the kernel to sacrifice heavy JOBS, never the live services, under memory pressure.
for svc in <app>.service <bot>.service postgresql.service; do
  systemctl set-property "$svc" OOMScoreAdjust=-900 2>/dev/null || true
done
```

Swap is a cushion so a transient spike *degrades* instead of killing processes — it is **not** a
licence to run heavy builds on a small prod box.

## 4. EXECUTE — run heavy steps inside a hard cap, then switch safely

Run anything heavy inside a transient cgroup capped to `BUDGET`, de-prioritised on CPU and IO. If it
exceeds the cap, **only that scope is killed** — the app and DB survive (this is the hard guarantee
the written rule alone can't give):

```bash
systemd-run --scope --unit="hermes-heavy-$$" \
  -p MemoryMax=${BUDGET}M -p MemorySwapMax=${SWAPF}M \
  -p CPUWeight=20 -p IOWeight=20 \
  nice -n 19 ionice -c3 \
  <your heavy command>          # e.g. an on-box install/migration that genuinely must run here
```

Then: smoke-check on a scratch port → **atomic switch** (flip the release symlink / move) →
`systemctl restart` **only the affected services** → verify (`is-active`, an HTTP health check, logs)
→ keep the previous release one command away. If anything looks wrong, roll back immediately.

## One-paragraph version (if you remember nothing else)

Before touching a server, measure `free -m`/`swapon`/`nproc`/load. Reserve headroom for the live
services, and only run on-box what fits in what's left — cap it with `systemd-run -p MemoryMax=…`
and `nice`/`ionice` so a runaway dies instead of the app. Build and test **off the box** when it
won't fit, never point a build/test/migration at the live DB, protect critical services with
`OOMScoreAdjust=-900`, and always keep a one-command rollback. Assess, plan, protect, then work.
