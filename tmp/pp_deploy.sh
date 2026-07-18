#!/usr/bin/env bash
# Runs ON miramed32 (prostye-postavki prod). Deploys branch fix/incoming-paste-single-cell.
set -uo pipefail
echo "=== preflight ==="
free -m | head -3
swapon --show || true
uptime
cd /var/www/prostye-postavki/app || exit 1
echo "=== git ==="
git status --porcelain | head -5
git fetch origin fix/incoming-paste-single-cell 2>&1 | tail -2
BEFORE=$(git rev-parse --short HEAD)
git pull --ff-only origin fix/incoming-paste-single-cell 2>&1 | tail -3
echo "before: $BEFORE  now: $(git rev-parse --short HEAD)"
export DEBIAN_FRONTEND=noninteractive
apt-get install -y -q poppler-utils >/dev/null 2>&1; echo "pdftoppm: $(command -v pdftoppm)"
echo "=== compile ==="
.venv/bin/python -m py_compile backend/app/main.py backend/app/mcp_prompts.py backend/app/contract_templates.py && echo COMPILE_OK || exit 1
echo "=== engine smoke (no DB) ==="
.venv/bin/python backend/tools/contract_template_smoke.py || exit 1
echo "=== import check (fails BEFORE restart, service keeps old code) ==="
if ! .venv/bin/python -c "import backend.app.main" > /tmp/pp_import_check.log 2>&1; then
  echo "IMPORT_FAILED - NOT restarting"; tail -15 /tmp/pp_import_check.log; exit 1
fi
echo IMPORT_OK
echo "=== restart ==="
systemctl restart prostye-backend
sleep 3
echo "active: $(systemctl is-active prostye-backend)"
code=000
for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health || true)
  [ "$code" = "200" ] && break
  sleep 0.5
done
echo "health: $code"
[ "$code" = "200" ] || { journalctl -u prostye-backend --no-pager | tail -20; exit 1; }
echo "=== live MCP checks ==="
SECRET=$(grep -a -m1 -E '^MCP_SERVER_SECRET=' .env.local | sed 's/^MCP_SERVER_SECRET=//' | tr -d '\r"')
TOOLS=$(curl -s -X POST "http://127.0.0.1:8000/mcp/$SECRET" -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | grep -o -E 'export_contract_template|create_contract_from_template|list_contract_templates|delete_contract_template|get_contract_files|view_incoming_contract_document' | sort -u | tr '\n' ' ')
echo "new tools visible: $TOOLS"
PROMPT_OK=$(curl -s -X POST "http://127.0.0.1:8000/mcp/$SECRET" -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_mcp_prompt","arguments":{"name":"contract_from_template_workflow"}}}' \
  | grep -o 'contract_from_template_workflow' | head -1)
echo "prompt served: ${PROMPT_OK:-MISSING}"
LIST_OK=$(curl -s -X POST "http://127.0.0.1:8000/mcp/$SECRET" -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_contract_templates","arguments":{}}}' \
  | grep -o '"templates"' | head -1)
echo "list_contract_templates works (DB schema created): ${LIST_OK:-FAILED}"
echo "DEPLOY_DONE"
