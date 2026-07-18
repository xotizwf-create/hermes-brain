"""Deploy the org tools + enable them for the main agent; verify tiering and a live agent turn."""
import subprocess
import sys
import time

REPO = "/var/www/albery"
sys.path.insert(0, REPO)


def sh(*cmd, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


print(sh("git", "-C", REPO, "pull", "--ff-only", "origin", "main")[1].splitlines()[-1])
rc, out = sh(f"{REPO}/.venv/bin/python", "-m", "py_compile", f"{REPO}/mcp/context_server.py")
print("compile rc:", rc, out[:150])
assert rc == 0

from shared.db import connect  # noqa: E402
for _ in range(24):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM bitrix_inflight_turns")
        n = cur.fetchone()["n"]
    if n == 0:
        break
    print("  ждём пустое окно, живых ходов:", n)
    time.sleep(15)
sh("systemctl", "restart", "albery")
time.sleep(5)
print("albery:", sh("systemctl", "is-active", "albery")[1])

import app  # noqa: E402,F401
import agent_center  # noqa: E402
from mcp import context_server as cs  # noqa: E402

ORG_TOOLS = ["get_bitrix_departments", "manage_bitrix_department", "assign_employee_department"]
cfg = cs._mgmt_endpoint("GET", "/api/agent-center/agents/main/config",
                        agent_center.agent_center_agent_config, "main")
valid = {t["name"] for t in cfg["tools"]}
enabled = {t["name"] for t in cfg["tools"] if t["enabled"]}
print("новые инструменты доступны в реестре:", [t for t in ORG_TOOLS if t in valid])
new = sorted(enabled | {t for t in ORG_TOOLS if t in valid})
cs._mgmt_endpoint("PUT", "/api/agent-center/agents/main/config",
                  agent_center.agent_center_agent_config_save, "main",
                  json_body={"tools": new,
                             "instructions": [i["id"] for i in cfg["instructions"] if i.get("selected")],
                             "skills": [s["id"] for s in cfg["skills"] if s.get("selected")]})
cfg2 = cs._mgmt_endpoint("GET", "/api/agent-center/agents/main/config",
                         agent_center.agent_center_agent_config, "main")
on = sorted(t["name"] for t in cfg2["tools"] if t["enabled"])
print("у главного агента инструментов:", len(on), "| оргструктура:", [t for t in ORG_TOOLS if t in on])

# тиринг: FAQ не должен видеть оргструктуру
print("в FAQ-тире (должно быть пусто):", [t for t in ORG_TOOLS if t in cs.FAQ_TOOL_NAMES])

rc, out = sh(f"{REPO}/.venv/bin/python", f"{REPO}/scripts/deploy_smoke.py", timeout=600)
print("\n".join(out.splitlines()[-3:]))
