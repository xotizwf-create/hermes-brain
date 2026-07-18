"""Find the rename-button task (read-only)."""
import json
import sys
import urllib.request

sys.path.insert(0, "/var/www/albery")
from shared.db import load_env_value  # noqa: E402

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


for needle in ("кнопк", "переимен", "предложени"):
    res = call("tasks.task.list", {"filter": {"%TITLE": needle, "!STATUS": 5},
                                   "select": ["ID", "TITLE", "STATUS", "RESPONSIBLE_ID", "DESCRIPTION"]})
    for t in (res.get("result") or {}).get("tasks") or []:
        print(f"[{needle}] TASK {t.get('id')} | {t.get('title')} | status {t.get('status')} | resp {t.get('responsibleId')}")
        print("  DESC:", str(t.get("description") or "")[:800].replace("\n", " ⏎ "))
