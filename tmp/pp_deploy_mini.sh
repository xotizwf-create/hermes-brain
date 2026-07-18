#!/usr/bin/env bash
set -uo pipefail
cd /var/www/prostye-postavki/app || exit 1
git fetch origin fix/incoming-paste-single-cell 2>&1 | tail -1
git pull --ff-only origin fix/incoming-paste-single-cell 2>&1 | tail -1
echo "now: $(git rev-parse --short HEAD)"
.venv/bin/python -m py_compile backend/app/main.py backend/app/mcp_prompts.py && echo COMPILE_OK || exit 1
if ! .venv/bin/python -c "import backend.app.main" > /tmp/pp_import_check.log 2>&1; then
  echo "IMPORT_FAILED - NOT restarting"; tail -10 /tmp/pp_import_check.log; exit 1
fi
echo IMPORT_OK
systemctl restart prostye-backend
sleep 3
code=000
for i in $(seq 1 30); do code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health || true); [ "$code" = "200" ] && break; sleep 0.5; done
echo "active: $(systemctl is-active prostye-backend) health: $code"
