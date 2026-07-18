"""Read the last automation-37 run result + stored digest; make bot 80 leave the notify group."""
import json
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402
from shared.db import connect, load_env_value  # noqa: E402

with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT last_status, last_error, deliver_to FROM agent_automations WHERE id=37")
    print("automation:", dict(cur.fetchone()))
    cur.execute("SELECT id, created_at, length(summary) AS len FROM tg_news_digests ORDER BY created_at DESC LIMIT 1")
    d = cur.fetchone()
    print("stored digest:", dict(d) if d else "NONE")
    cur.execute("SELECT last_result FROM agent_automations WHERE id=37")
    print("\n--- last_result ---\n", (cur.fetchone()["last_result"] or "")[:3200])

# make the news bot leave the notifications group (app couldn't kick; bot leaves itself)
endpoint, token = b24bot._b24_app_access_token()
notify_chat = (load_env_value("ALBERY_BITRIX_NOTIFY_CHAT") or "chat728").strip()
notify_id = int(notify_chat.replace("chat", ""))
for method, payload in (
    ("imbot.chat.leave", {"BOT_ID": 80, "CHAT_ID": notify_id}),
    ("imbot.chat.leave", {"BOT_ID": 80, "DIALOG_ID": notify_chat}),
):
    try:
        r = b24bot._b24_app_call(endpoint, token, method, payload)
        print(f"{method} {list(payload)[1]}:", r.get("result"))
        break
    except Exception as exc:  # noqa: BLE001
        print(f"{method} failed:", str(exc)[:150])
