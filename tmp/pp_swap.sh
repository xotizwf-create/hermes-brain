#!/usr/bin/env bash
set -uo pipefail
ls -la /swapfile
swapon /swapfile 2>&1 || true
grep -q swapfile /etc/fstab && echo FSTAB_OK || { echo "/swapfile none swap sw 0 0" >> /etc/fstab; echo FSTAB_ADDED; }
swapon --show
free -m | head -3
