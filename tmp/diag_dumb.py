"""Разбор жалобы «агент стал тупее»: последние ходы в Bitrix-боте + что вернули инструменты."""
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from shared.db import connect  # noqa: E402

with connect() as conn, conn.cursor() as cur:
    cur.execute("""SELECT column_name FROM information_schema.columns
                   WHERE table_name='bitrix_bot_interactions' ORDER BY ordinal_position""")
    print("колонки:", [r["column_name"] for r in cur.fetchall()])

    cur.execute("""SELECT id, created_at, dialog_id, bitrix_user_id, agent_slug, status,
                          latency_ms, question, answer
                   FROM bitrix_bot_interactions
                   ORDER BY created_at DESC LIMIT 8""")
    rows = cur.fetchall()

for r in reversed(rows):
    print("\n" + "=" * 90)
    print(f"[{r['created_at']:%d.%m %H:%M}] диалог={r['dialog_id']} юзер={r['bitrix_user_id']} "
          f"агент={r['agent_slug'] or 'main'} статус={r['status']} {(r['latency_ms'] or 0)/1000:.0f}с")
    q = (r["question"] or "").strip()
    # вопрос содержит служебный префикс — покажем хвост (само сообщение человека)
    print("ВОПРОС (хвост):", q[-500:].replace("\n", " / "))
    print("ОТВЕТ:", (r["answer"] or "").strip()[:700].replace("\n", " / "))
