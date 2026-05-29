#!/usr/bin/env bash
set -euo pipefail

echo "== postgresql service =="
systemctl is-active postgresql || true

echo "== readiness =="
pg_isready || true

echo "== version =="
sudo -u postgres psql -Atc "select version();" 2>/dev/null || true

echo "== roles =="
sudo -u postgres psql -c "\\du" 2>/dev/null || true

echo "== databases =="
sudo -u postgres psql -c "\\l" 2>/dev/null || true

echo "== disk =="
df -h / /var/lib/postgresql 2>/dev/null || df -h
