"""Виден ли get_latest_news_digest на коннекторе main? Есть ли маршрут в start_here?"""
import subprocess
import sys
import time

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from mcp import context_server as cs  # noqa: E402

# 1) что отдаёт tools/list коннектора агента main
names = cs.allowed_tools_for_agent("main") if hasattr(cs, "allowed_tools_for_agent") else None
if names is None:
    from shared.db import connect
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT tools FROM agents WHERE slug='main'")
        names = list(cur.fetchone()["tools"] or [])
print("get_latest_news_digest в наборе main:", "get_latest_news_digest" in names, "| всего:", len(names))

# 2) есть ли маршрут в инструкциях, которые агент получает через start_here
sh = cs.tool_start_here_always_read_ai_instructions({}) if hasattr(
    cs, "tool_start_here_always_read_ai_instructions") else {}
blob = str(sh)
print("маршрут про сводку в start_here:", "get_latest_news_digest" in blob)
print("длина start_here:", len(blob))

# 3) прямой вызов инструмента — работает ли он вообще
d = cs.tool_get_latest_news_digest({})
print("\nинструмент отдаёт сводку:", d.get("found"), "| символов:", len(d.get("summary") or ""))

# 4) живой ход с ЯВНОЙ формулировкой
ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
for q in ("Что было в последней новостной сводке от Новостного агента? Дай полный текст.",
          "Скинь полный текст последней новостной сводки"):
    t0 = time.time()
    r = subprocess.run(["hermes", "-z", q, "-t", "agent-main,web", "--yolo"],
                       capture_output=True, text=True, timeout=420, cwd="/root", env=ENV)
    ans = (r.stdout or "").strip()
    hit = sum(m in ans for m in ("34,5", "46 ₽", "ИРП", "Коротко"))
    print(f"\n[{time.time()-t0:.0f}с | совпало маркеров сводки: {hit}/4] В: {q}")
    print("О:", ans[:400].replace("\n", " / "))
