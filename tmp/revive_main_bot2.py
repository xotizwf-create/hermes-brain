# One-off, attempt 2: find the main bot via im.recent.get and ping it.
import sys
import time

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from b24bot import _b24_load_state, _b24_testbot_call, b24_testbot_client  # noqa: E402

client = b24_testbot_client()
found = []
try:
    data = _b24_testbot_call(client, "im.recent.get", {})
    result = data.get("result")
    items = result.get("items") if isinstance(result, dict) else (result or [])
    for it in items:
        u = (it or {}).get("user") or {}
        if u and (u.get("bot") or str(u.get("type") or "") == "bot"):
            found.append((u.get("id"), u.get("name")))
except Exception as exc:  # noqa: BLE001
    print("im.recent.get failed:", str(exc)[:200])

print("bots in recent:", found)
if found:
    bot_uid, bot_name = sorted(found, key=lambda x: int(x[0]))[0]
    print("pinging:", bot_uid, bot_name)
    r = _b24_testbot_call(client, "im.message.add", {"DIALOG_ID": bot_uid, "MESSAGE": "/new"})
    print("ping sent, message id:", r.get("result"))
    time.sleep(6)
    state = _b24_load_state()
    print("state after ping: application_token:", bool(state.get("application_token")),
          "| bot_id:", state.get("bot_id"),
          "| app_tokens:", bool((state.get("app_tokens") or {}).get("access_token")))
