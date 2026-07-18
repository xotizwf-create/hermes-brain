"""Почему главный агент отдал «не ту» сводку: что он ответил, что лежит в базе, что у него в тулах."""
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import agent_center  # noqa: E402
from mcp import context_server as cs  # noqa: E402
from shared.db import connect  # noqa: E402

print("=== ЧТО ОТВЕТИЛ ГЛАВНЫЙ АГЕНТ (реальные ходы про сводку) ===")
with connect() as conn, conn.cursor() as cur:
    cur.execute("""SELECT created_at, question, answer FROM bitrix_bot_interactions
                   WHERE question ILIKE '%сводк%' AND status='ok'
                   ORDER BY created_at DESC LIMIT 2""")
    for r in reversed(cur.fetchall()):
        q = (r["question"] or "").split("Текущее сообщение пользователя:")[-1].strip()[:90]
        print(f"\n[{r['created_at']:%d.%m %H:%M}] В: «{q}»")
        print("О:", (r["answer"] or "")[:700].replace("\n", "\n   "))

print("\n\n=== ЧТО РЕАЛЬНО ЛЕЖИТ В СОХРАНЁННОЙ СВОДКЕ ===")
d = cs.tool_get_latest_news_digest({})
print("найдена:", d.get("found"), "| возраст:", d.get("age_days"), "дн | свежая:", d.get("is_fresh"))
print("текст (начало):\n", (d.get("summary") or "")[:600])

print("\n=== ИНСТРУМЕНТЫ ГЛАВНОГО АГЕНТА: есть ли доступ к сводкам? ===")
cfg = cs._mgmt_endpoint("GET", "/api/agent-center/agents/main/config",
                        agent_center.agent_center_agent_config, "main")
enabled = {t["name"] for t in cfg["tools"] if t["enabled"]}
for t in ("get_latest_news_digest", "save_news_digest", "get_tg_news"):
    print(f"  {t}: {'ЕСТЬ' if t in enabled else 'НЕТ'}")
print("  всего инструментов у main:", len(enabled))
