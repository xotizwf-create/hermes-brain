#!/usr/bin/env bash
set -euo pipefail

TARGET_KEY="${1:?Usage: sudo ./enroll-linux-personal.sh <TARGET_KEY> [hostname]}"
HOSTNAME_ARG="${2:-$(hostname)}"
LOGIN_SERVER="${LOGIN_SERVER:-https://vpn.andigital.ru}"

if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi

id codex >/dev/null 2>&1 || useradd -m -s /bin/bash codex
id codexadmin >/dev/null 2>&1 || useradd -m -s /bin/bash codexadmin

# Admin role: passwordless sudo only for the separate admin user.
if command -v sudo >/dev/null 2>&1; then
  usermod -aG sudo codexadmin 2>/dev/null || usermod -aG wheel codexadmin 2>/dev/null || true
  cat >/etc/sudoers.d/90-codexadmin <<'EOF'
codexadmin ALL=(ALL) NOPASSWD:ALL
EOF
  chmod 440 /etc/sudoers.d/90-codexadmin
fi

tailscale up \
  --login-server "$LOGIN_SERVER" \
  --authkey "$TARGET_KEY" \
  --advertise-tags=tag:personal-target \
  --accept-dns=true \
  --ssh \
  --hostname="$HOSTNAME_ARG"

systemctl enable --now tailscaled 2>/dev/null || true

echo "OK: personal connector installed. Roles: codex (regular), codexadmin (admin)."
