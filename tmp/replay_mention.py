"""Replay the missed mention (task 1254, comment 15632) through the REAL handler, then verify."""
import json
import sys
import time
import urllib.request

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402
from shared.db import load_env_value  # noqa: E402

res = b24bot._b24_handle_task_comment_event(1254, 15632)
print("handler result:", res)

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


time.sleep(3)
msgs = call("im.dialog.messages.get", {"DIALOG_ID": "chat1708", "LIMIT": 8})
for m in sorted((msgs.get("result") or {}).get("messages") or [], key=lambda x: int(x.get("id") or 0)):
    print(f"  msg[{m.get('id')}] author={m.get('author_id')}: {str(m.get('text'))[:220]}")
