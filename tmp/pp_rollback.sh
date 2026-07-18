#!/usr/bin/env bash
set -uo pipefail
cd /var/www/prostye-postavki/app
git reset --hard c10aa1b
systemctl restart prostye-backend
sleep 4
echo "active: $(systemctl is-active prostye-backend)"
code=000
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health || true)
  [ "$code" = "200" ] && break
  sleep 0.5
done
echo "health: $code"
