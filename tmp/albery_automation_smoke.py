# Smoke for per-agent automations on the Albery box (run with PYTHONPATH=/var/www/albery).
# 1) connector tools/list advertises the automation self-tools;
# 2) end-to-end automation run on the main agent's connector with a SILENT task
#    (real hermes turn, nothing delivered anywhere);
# 3) row lifecycle: insert -> run -> status -> delete.
import json

import requests

import app  # noqa: F401  (sys.path/бутстрап Flask)
import agent_automations
from app import pg_connect

# --- 1. connector advertises the new self-tools -----------------------------------------
with pg_connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT slug, mcp_token FROM agents WHERE slug = 'main'")
        agent_row = cur.fetchone()
resp = requests.post(
    f"http://127.0.0.1:5002/mcp-agent/main/{agent_row['mcp_token']}",
    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    timeout=30,
)
names = {t["name"] for t in resp.json()["result"]["tools"]}
need = {"schedule_my_automation", "list_my_automations", "delete_my_automation"}
print("tools/list:", "OK" if need <= names else f"MISSING {need - names}", f"({len(names)} tools)")

# --- 2+3. e2e run with the silence rule ---------------------------------------------------
with pg_connect() as conn:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("DELETE FROM agent_automations WHERE name = '__smoke__'")
            cur.execute(
                "INSERT INTO agent_automations (agent_slug, name, schedule, prompt, kind, created_by, creator_label) "
                "VALUES ('main', '__smoke__', '0 0 30 2 *', "
                "'Это тестовый запуск конвейера автоматизаций. Никаких инструментов не вызывай. "
                "Ответь ровно одним словом SILENT.', 'agent', 'owner', 'smoke') RETURNING id",
            )
            auto_id = cur.fetchone()["id"]

row = agent_automations._row_by_id(auto_id)
agent_automations._run_automation(row)
after = agent_automations._row_by_id(auto_id)
print("run:", json.dumps({"status": after["last_status"], "error": after["last_error"],
                          "result": (after["last_result"] or "")[:120]}, ensure_ascii=False))

with pg_connect() as conn:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("DELETE FROM agent_automations WHERE id = %s", (auto_id,))
print("cleanup: OK")

# list self-tool sanity (main agent sees its 4 system rows)
listing = agent_automations.automation_self_tool_call({"slug": "main", "name": "Агент Албери"},
                                                      "list_my_automations", {})
print("list_my_automations:", listing["count"], "rows")
