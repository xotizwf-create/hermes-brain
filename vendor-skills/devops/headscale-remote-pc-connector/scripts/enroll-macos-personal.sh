#!/usr/bin/env bash
set -euo pipefail

TARGET_KEY="${1:?Usage: sudo ./enroll-macos-personal.sh <TARGET_KEY> [hostname]}"
HOSTNAME_ARG="${2:-$(scutil --get ComputerName 2>/dev/null || hostname)}"
LOGIN_SERVER="${LOGIN_SERVER:-https://vpn.andigital.ru}"

if ! command -v tailscale >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install tailscale
  else
    echo "Install Tailscale first from https://tailscale.com/download/mac or Homebrew, then rerun." >&2
    exit 1
  fi
fi

sudo tailscaled install-system-daemon 2>/dev/null || true

# macOS users are usually better created manually in System Settings if they do not exist yet.
# This script joins the machine to Headscale and enables Tailscale SSH policy for users codex/codexadmin.
sudo tailscale up \
  --login-server "$LOGIN_SERVER" \
  --authkey "$TARGET_KEY" \
  --advertise-tags=tag:personal-target \
  --accept-dns=true \
  --ssh \
  --hostname="$HOSTNAME_ARG"

echo "OK: personal connector installed. Ensure local users exist: codex (regular), codexadmin (admin)."
