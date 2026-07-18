"""Было/стало: латентность ходов бота ДО и ПОСЛЕ смены модели (12.07 21:57 МСК) +
сколько MCP-инструментов агент звал за ход + что реально лежит в его системном промпте."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from shared.db import connect  # noqa: E402

SWITCH = "2026-07-12 18:57:00+00"  # смена на Terra (UTC)

print("=== ЛАТЕНТНОСТЬ ходов бота: до/после смены модели ===")
with connect() as conn, conn.cursor() as cur:
    cur.execute("""
        SELECT CASE WHEN created_at < %s THEN 'ДО (gpt-5.5)' ELSE 'ПОСЛЕ (terra)' END AS period,
               count(*) AS ходов,
               round((avg(latency_ms)/1000.0)::numeric, 1) AS средн_сек,
               round((percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms)/1000.0)::numeric, 1) AS медиана_сек,
               round(avg(length(answer))::numeric) AS средн_длина_ответа
        FROM bitrix_bot_interactions
        WHERE status = 'ok' AND created_at > now() - interval '10 days'
        GROUP BY 1 ORDER BY 1 DESC
    """, (SWITCH,))
    for r in cur.fetchall():
        print(f"  {r['period']:<16} ходов={r['ходов']:<4} средн={r['средн_сек']}с "
              f"медиана={r['медиана_сек']}с длина ответа={r['средн_длина_ответа']}")

print("\n=== ПОСЛЕДНИЕ ходы (что спрашивали / сколько думал) ===")
with connect() as conn, conn.cursor() as cur:
    cur.execute("""SELECT created_at, bitrix_user_id, latency_ms, question, answer
                   FROM bitrix_bot_interactions WHERE status='ok'
                   ORDER BY created_at DESC LIMIT 6""")
    for r in reversed(cur.fetchall()):
        q = (r["question"] or "").strip()
        msg = q.split("Текущее сообщение пользователя:")[-1].strip()[:110]
        print(f"  [{r['created_at']:%d.%m %H:%M}] {(r['latency_ms'] or 0)/1000:>5.0f}с  "
              f"«{msg}» → ответ {len(r['answer'] or '')} симв")

print("\n=== СКОЛЬКО ИНСТРУМЕНТОВ агент звал за ход (по журналу MCP) ===")
out = subprocess.run(
    ["bash", "-c",
     "journalctl -u albery --since '3 days ago' --no-pager | grep -oE 'POST /mcp[a-z-]*/' | sort | uniq -c"],
    capture_output=True, text=True).stdout
print(out.strip() or "  (нет данных)")

print("\n=== ЧТО ЛЕЖИТ В ПЕРСОНЕ (системный промпт всех ходов) ===")
cfg = Path("/root/.hermes/config.yaml").read_text(encoding="utf-8")
m = re.search(r"^    albery: [\"'](.+?)[\"']\s*$", cfg, re.S | re.M)
persona = m.group(1) if m else "(не найдена)"
print(" ", persona[:900].replace("\\n", " "))
print("\n  >>> содержит ли призыв к минимуму вызовов:",
      "1-2 вызова" in persona or "1–2 вызова" in persona)
print("  >>> model/effort:", re.search(r"model:\n  default: (\S+)", cfg).group(1),
      "/", re.search(r"reasoning_effort: (\S+)", cfg).group(1))
