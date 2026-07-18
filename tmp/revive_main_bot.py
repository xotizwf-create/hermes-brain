# One-off: find the main bot's user id via the webhook client and ping it so Bitrix
# fires an imbot event -> the new self-heal code re-adopts application_token + bot_id.
import sys
import time

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401 — import order matters: app fully initializes b24bot/agent_center
from b24bot import _b24_load_state, _b24_testbot_call, b24_testbot_client  # noqa: E402

client = b24_testbot_client()
bots = []
try:
    data = _b24_testbot_call(client, "user.get", {"USER_TYPE": "bot", "ACTIVE": True})
    bots = [u for u in (data.get("result") or []) if isinstance(u, dict)]
except Exception as exc:  # noqa: BLE001
    print("user.get USER_TYPE=bot failed:", str(exc)[:200])

print("bots found:", [(u.get("ID"), (u.get("NAME") or "") + " " + (u.get("LAST_NAME") or "")) for u in bots])

if bots:
    # The main bot is the oldest one (lowest id) — subagent test bots have higher ids.
    main = sorted(bots, key=lambda u: int(u["ID"]))[0]
    print("pinging bot:", main["ID"], main.get("NAME"))
    r = _b24_testbot_call(client, "im.message.add",
                          {"DIALOG_ID": main["ID"], "MESSAGE": "/new"})
    print("ping sent:", r.get("result"))
    time.sleep(5)
    state = _b24_load_state()
    print("state after ping: application_token:", bool(state.get("application_token")),
          "| bot_id:", state.get("bot_id"),
          "| app_tokens:", bool((state.get("app_tokens") or {}).get("access_token")))
