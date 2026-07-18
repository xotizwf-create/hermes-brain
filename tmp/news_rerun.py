"""Clean re-run of automation 37 (v2), verify status/delivery/stored digest, restore Sunday."""
import json
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from config import MSK_TZ  # noqa: E402
from shared.db import connect  # noqa: E402

fire = datetime.now(MSK_TZ) + timedelta(minutes=2)
once = f"{fire.minute} {fire.hour} {fire.day} {fire.month} *"
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule=%s, last_status=NULL, last_error=NULL WHERE id=37", (once,))
    conn.commit()
print("firing at", fire.strftime("%H:%M"))

status = None
for i in range(64):
    time.sleep(15)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT last_status, last_error, last_result FROM agent_automations WHERE id=37")
        row = dict(cur.fetchone())
    if row["last_status"] not in (None, "running"):
        status = row
        break
    if i % 4 == 3:
        print(f"  waiting... {(i+1)*15}s status={row['last_status']}", flush=True)

with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule=%s WHERE id=37", ("0 10 * * 0",))
    conn.commit()
print("schedule restored to Sunday 10:00")
print("STATUS:", status["last_status"] if status else "NOT FINISHED", "| ERR:", (status or {}).get("last_error"))

with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT id, created_at, length(summary) AS len FROM tg_news_digests ORDER BY created_at DESC LIMIT 1")
    d = cur.fetchone()
print("STORED DIGEST:", dict(d) if d else "NONE")
if status:
    print("\n--- delivered to Nikitenko(16) ---\n", (status.get("last_result") or "")[:3500])
