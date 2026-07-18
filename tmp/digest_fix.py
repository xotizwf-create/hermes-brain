"""Деплой + подключить главному агенту доступ к сводкам + маршрут в Маршрутной карте + проверка."""
import subprocess
import sys
import time
from pathlib import Path

REPO = "/var/www/albery"
sys.path.insert(0, REPO)


def sh(*cmd, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


print(sh("git", "-C", REPO, "pull", "--ff-only", "origin", "main")[1].splitlines()[-1])
rc, out = sh(f"{REPO}/.venv/bin/python", "-m", "py_compile", f"{REPO}/mcp/context_server.py")
assert rc == 0, out
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
from agent_knowledge import parse_doc  # noqa: E402
from mcp import context_server as cs  # noqa: E402

# 1) дать главному агенту доступ к сохранённым сводкам (только чтение)
cfg = cs._mgmt_endpoint("GET", "/api/agent-center/agents/main/config",
                        agent_center.agent_center_agent_config, "main")
valid = {t["name"] for t in cfg["tools"]}
enabled = {t["name"] for t in cfg["tools"] if t["enabled"]}
add = {"get_latest_news_digest"} & valid
cs._mgmt_endpoint("PUT", "/api/agent-center/agents/main/config",
                  agent_center.agent_center_agent_config_save, "main",
                  json_body={"tools": sorted(enabled | add),
                             "instructions": [i["id"] for i in cfg["instructions"] if i.get("selected")],
                             "skills": [s["id"] for s in cfg["skills"] if s.get("selected")]})
cfg2 = cs._mgmt_endpoint("GET", "/api/agent-center/agents/main/config",
                         agent_center.agent_center_agent_config, "main")
on = {t["name"] for t in cfg2["tools"] if t["enabled"]}
print("get_latest_news_digest у main:", "get_latest_news_digest" in on, "| всего:", len(on))

# 2) маршрут в Маршрутной карте
md = Path(REPO, "agent_knowledge/instructions/Маршрутная карта.md")
_m, content = parse_doc(md.read_text(encoding="utf-8"))
ANCHOR = "- Дочитать конкретную инструкцию:"
ROUTE = ("- Новостная сводка («что было в сводке», «скинь сводку», «полный текст сводки», новости "
         "рынка/WB): get_latest_news_digest — и отдай сохранённый текст ДОСЛОВНО, как есть. Не "
         "пересказывай своими словами и не собирай сводку сам: её готовит Новостной агент.\n")
if "get_latest_news_digest" not in content:
    content = content.replace(ANCHOR, ROUTE + ANCHOR, 1)
    r = cs.tool_upsert_ai_instruction({"path": "Маршрутная карта", "content": content})
    body = ((r or {}).get("folder") or {}).get("content") or ""
    print("маршрут добавлен:", "get_latest_news_digest" in body)
else:
    print("маршрут уже есть")

# 3) живая проверка: агент должен отдать РЕАЛЬНЫЙ текст
stored = (cs.tool_get_latest_news_digest({}) or {}).get("summary") or ""
ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
t0 = time.time()
r = subprocess.run(["hermes", "-z", "Скинь пожалуйста полный текст последней новостной сводки",
                    "-t", "agent-main,web", "--yolo"],
                   capture_output=True, text=True, timeout=420, cwd="/root", env=ENV)
ans = (r.stdout or "").strip()
print(f"\n=== ЖИВОЙ ХОД ({time.time()-t0:.0f}с) ===")
print(ans[:900])
# сверка: совпадают ли характерные куски сохранённой сводки
marks = ["34,5% → 43,5%", "46 ₽", "ИРП", "Коротко"]
print("\n=== СВЕРКА С СОХРАНЁННОЙ СВОДКОЙ ===")
for m in marks:
    print(f"  «{m}»: в сводке {'да' if m in stored else 'нет'} | в ответе {'да' if m in ans else 'НЕТ'}")
