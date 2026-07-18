"""Force-run automation 37 once through the LIVE service scheduler, then restore Sunday cron."""
import json
import sys
import time
import urllib.request
from datetime import timedelta

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from config import MSK_TZ  # noqa: E402
from datetime import datetime  # noqa: E402
from shared.db import connect, load_env_value  # noqa: E402

AUTO_ID = 37
fire = datetime.now(MSK_TZ) + timedelta(minutes=2)
once_cron = f"{fire.minute} {fire.hour} {fire.day} {fire.month} *"
print("firing at", fire.strftime("%H:%M"), "cron:", once_cron)

with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule = %s WHERE id = %s", (once_cron, AUTO_ID))
    conn.commit()

status = None
for i in range(60):  # up to 15 min
    time.sleep(15)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT last_status, last_error, last_run_at FROM agent_automations WHERE id = %s",
                    (AUTO_ID,))
        row = dict(cur.fetchone())
    if row["last_run_at"] and row["last_status"] != "running":
        status = row
        break
    if i % 4 == 3:
        print(f"  waiting... {(i + 1) * 15}s status={row['last_status']}", flush=True)

with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule = %s WHERE id = %s", ("0 10 * * 0", AUTO_ID))
    conn.commit()
print("schedule restored to Sunday 10:00")
print("run result:", json.dumps(status, ensure_ascii=False, default=str) if status else "NOT FINISHED in 15 min")

# show the delivered message (the agent's bot posts to the notifications chat by default)
import b24bot  # noqa: E402
try:
    endpoint, token = b24bot._b24_app_access_token()
    chat = (load_env_value("ALBERY_BITRIX_NOTIFY_CHAT") or "chat728").strip()
    data = b24bot._b24_app_call(endpoint, token, "im.dialog.messages.get",
                                {"DIALOG_ID": chat, "LIMIT": 3})
    for m in sorted((data.get("result") or {}).get("messages") or [], key=lambda x: int(x.get("id") or 0)):
        print(f"\n--- chat msg [{m.get('id')}] author={m.get('author_id')} ---")
        print(str(m.get("text") or "")[:2500])
except Exception as exc:  # noqa: BLE001
    print("notify chat read failed:", str(exc)[:200])
