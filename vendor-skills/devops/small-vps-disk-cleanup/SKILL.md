---
name: small-vps-disk-cleanup
description: "Safely clean disk pressure on a small Linux/VPS production host without touching live apps, databases, secrets, or project data."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [devops, linux, disk, cleanup, production, vps]
---

# Small VPS Disk Cleanup

Use when a small production server is low on disk space or Hermes/gateway feels laggy and the owner asks for cleanup.

## Rules

1. Run the server preflight first: check load, RAM, swap, disk, failed services, and identify live services.
2. Do not delete application directories, databases, secrets, `/opt/hermes/secure`, live checkouts, or unknown project data.
3. Prefer safe/regenerable targets first: package caches, stale package lists, bounded journals, temporary tool sandboxes, npm/npx caches, old non-current kernels, and known old maintenance snapshots.
4. After every cleanup wave, verify disk, memory, failed services, and key service health.
5. If adding a journal size cap, use a small drop-in under `/etc/systemd/journald.conf.d/` and restart only journald.

## Safe inspection commands

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
uptime
free -h
df -h /
df -ih /
systemctl --failed --no-pager
ps -eo pid,stat,pcpu,pmem,rss,comm,args --sort=-rss | head -n 15
journalctl --disk-usage
du -xhd1 / /var /root /opt /usr 2>/dev/null | sort -h | tail -n 80
```

## Safe cleanup waves

### Wave 1 — very safe caches/log pressure

```bash
apt-get clean
rm -rf /var/lib/apt/lists/*
journalctl --vacuum-size=50M || true
: > /var/log/btmp || true
rm -f /var/log/*.gz /var/log/*.[0-9] /var/log/*.[0-9].gz 2>/dev/null || true
rm -rf /root/.hermes/cache/screenshots/* /root/.hermes/cache/documents/* /root/.hermes/cache/vision/* 2>/dev/null || true
rm -f /root/.hermes/audio_cache/* 2>/dev/null || true
npm cache clean --force >/dev/null 2>&1 || true
```

### Wave 2 — only after confirming current kernel

Check current kernel with `uname -r`, then purge only older installed kernel packages:

```bash
apt-get purge -y linux-image-<old>-generic linux-modules-<old>-generic linux-headers-<old> linux-headers-<old>-generic
apt-get autoremove --purge -y
apt-get clean
rm -rf /var/lib/apt/lists/*
```

### Wave 3 — known temporary agent/tool leftovers

Only remove clearly temporary tool folders, never auth/config/state DBs:

```bash
rm -rf /root/.codex/tmp/* 2>/dev/null || true
rm -rf /root/.npm/_cacache /root/.npm/_npx 2>/dev/null || true
rm -f /root/.hermes/cache/brain_index.sqlite 2>/dev/null || true
```

Known old Hermes maintenance snapshots may be removed only when they are not the live DB/state and are dated/labelled as pre-update or maintenance backups.

## Prevent journal regrowth

```bash
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/99-hermes-disk-budget.conf <<'EOF'
[Journal]
SystemMaxUse=64M
RuntimeMaxUse=32M
MaxRetentionSec=14day
EOF
systemctl restart systemd-journald
journalctl --vacuum-size=64M || true
```

## Verification

```bash
df -h /
free -h
journalctl --disk-usage
systemctl --failed --no-pager
systemctl is-active hermes-gateway.service nginx postgresql meshcentral 2>/dev/null || true
```

Report the before/after free disk, percent used, memory availability, and whether failed services exist. Keep user-facing output practical and avoid dumping paths unless needed.
