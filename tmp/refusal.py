# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, '/var/www/albery'); os.chdir('/var/www/albery')
from dotenv import load_dotenv; load_dotenv('/var/www/albery/.env')
import psycopg
conn = psycopg.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("""
select id, created_at at time zone 'Europe/Moscow', dialog_id, bitrix_user_id, tier,
       question, answer, latency_ms, status, error, agent_slug
from bitrix_bot_interactions
where created_at >= '2026-07-29 22:00:00+03'
order by created_at
""")
rows = cur.fetchall()
print("ходов после деплоя:", len(rows))
for r in rows:
    a = r[6] or ''
    q = r[5] or ''
    hit = any(w in (a+q).lower() for w in ('документ', 'docs.google.com/document', 'доступ', 'редактир', 'не умею', 'александр'))
    mark = ' <<< ПРО ДОКУМЕНТЫ/ДОСТУП' if hit else ''
    print("="*100)
    print(f"ID={r[0]} {r[1]} DLG={r[2]} user={r[3]} tier={r[4]} lat={r[7]} st={r[8]} agent={r[10]}{mark}")
    print("--- Q ---"); print(q[:1200])
    print("--- A ---"); print(a[:2500])
