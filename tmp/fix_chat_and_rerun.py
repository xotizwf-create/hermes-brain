"""Add the news bot (80) to the notifications chat, then re-fire automation 37 once."""
import json
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402
from config import MSK_TZ  # noqa: E402
from shared.db import connect, load_env_value  # noqa: E402

endpoint, token = b24bot._b24_app_access_token()
chat = (load_env_value("ALBERY_BITRIX_NOTIFY_CHAT") or "chat728").strip()
chat_id = int(chat.replace("chat", ""))

try:
    r = b24bot._b24_app_call(endpoint, token, "im.chat.user.add",
                             {"CHAT_ID": chat_id, "USERS": [80]})
    print("im.chat.user.add:", r.get("result"))
except Exception as exc:  # noqa: BLE001
    print("user.add failed:", str(exc)[:200])
    # fallback: as the MAIN bot (24), which owns the notifications chat
    try:
        r = b24bot._b24_app_call(endpoint, token, "imbot.chat.user.add",
                                 {"BOT_ID": b24bot._b24_load_state().get("bot_id"),
                                  "CHAT_ID": chat_id, "USERS": [80]})
        print("imbot.chat.user.add:", r.get("result"))
    except Exception as exc2:  # noqa: BLE001
        print("imbot fallback failed:", str(exc2)[:200])

# re-fire once
fire = datetime.now(MSK_TZ) + timedelta(minutes=2)
once = f"{fire.minute} {fire.hour} {fire.day} {fire.month} *"
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule = %s, last_status = NULL, last_error = NULL "
                "WHERE id = 37", (once,))
    conn.commit()
print("re-firing at", fire.strftime("%H:%M"))

status = None
for i in range(60):
    time.sleep(15)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT last_status, last_error, last_run_at FROM agent_automations WHERE id = 37")
        row = dict(cur.fetchone())
    if row["last_run_at"] and row["last_status"] not in (None, "running"):
        status = row
        break
    if i % 4 == 3:
        print(f"  waiting... {(i + 1) * 15}s status={row['last_status']}", flush=True)

with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule = %s WHERE id = 37", ("0 10 * * 0",))
    conn.commit()
print("schedule restored to Sunday 10:00")
print("run result:", json.dumps(status, ensure_ascii=False, default=str) if status else "NOT FINISHED")

data = b24bot._b24_app_call(endpoint, token, "im.dialog.messages.get", {"DIALOG_ID": chat, "LIMIT": 2})
for m in sorted((data.get("result") or {}).get("messages") or [], key=lambda x: int(x.get("id") or 0)):
    print(f"\n--- chat msg [{m.get('id')}] author={m.get('author_id')} ---")
    print(str(m.get("text") or "")[:3500])
