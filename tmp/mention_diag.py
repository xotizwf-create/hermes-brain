"""Diagnose the in-task mention pipeline (read-only)."""
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402  (import order: app first)
import b24bot  # noqa: E402
from shared.db import connect, load_env_value  # noqa: E402

# 1) app-token event bindings
try:
    endpoint, token = b24bot._b24_app_access_token()
    data = b24bot._b24_app_call(endpoint, token, "event.get", {})
    print("event.get bindings:")
    for e in data.get("result") or []:
        print("  ", e.get("event"), "->", str(e.get("handler"))[:100])
except Exception as exc:  # noqa: BLE001
    print("event.get FAILED:", str(exc)[:200])

# 2) dedupe table: has ANY comment ever been claimed?
with connect() as conn, conn.cursor() as cur:
    try:
        cur.execute("SELECT COUNT(*) AS n, MAX(seen_at) AS last FROM bitrix_task_comment_seen")
        row = cur.fetchone()
        print("bitrix_task_comment_seen:", dict(row))
        cur.execute("SELECT * FROM bitrix_task_comment_seen ORDER BY seen_at DESC LIMIT 5")
        for r in cur.fetchall():
            print("  ", dict(r))
    except Exception as exc:  # noqa: BLE001
        print("seen table read failed:", str(exc)[:200])

# 3) targets + trigger matching against the REAL test comment text
text = "[USER=24]Агент Албери[/USER] О чем эта задача?"
tgt = b24bot._b24_task_pick_agent(text)
print("pick_agent on native mention:", (tgt or {}).get("name"), "| is_main:", (tgt or {}).get("is_main"))
print("bot_author_ids (loop guard):", b24bot._b24_task_bot_author_ids())

# 4) mention kill-switch + comment fetch for the real comment
print("mention enabled:", b24bot._b24_task_mention_enabled())
c = b24bot._b24_fetch_task_comment(1152, 14664)
print("fetch_comment(1152,14664):", {k: (str(v)[:80]) for k, v in (c or {}).items()} if c else None)
print("B24_TESTBOT_WEBHOOK_BASE set:", bool(load_env_value("B24_TESTBOT_WEBHOOK_BASE")))
