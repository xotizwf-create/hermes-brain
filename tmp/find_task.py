"""Find Nikitenko's task about agent mentions + its comments (read-only)."""
import sys

sys.path.insert(0, "/var/www/albery")
import json
import urllib.request

from shared.db import load_env_value

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


res = call("tasks.task.list", {
    "filter": {"%TITLE": "упоминание"},
    "select": ["ID", "TITLE", "DESCRIPTION", "STATUS", "DEADLINE", "RESPONSIBLE_ID", "CREATED_BY", "CHAT_ID"],
})
tasks = (res.get("result") or {}).get("tasks") or []
if not tasks:
    res = call("tasks.task.list", {
        "filter": {"%TITLE": "агент"},
        "select": ["ID", "TITLE", "STATUS", "DEADLINE", "RESPONSIBLE_ID"],
    })
    tasks = (res.get("result") or {}).get("tasks") or []
for t in tasks:
    print("TASK", t.get("id"), "|", t.get("title"), "| status", t.get("status"),
          "| resp", t.get("responsibleId"), "| deadline", t.get("deadline"))
    desc = str(t.get("description") or "")
    if desc:
        print("  DESCRIPTION:", desc[:1200].replace("\n", " ⏎ "))
    chat_id = t.get("chatId")
    if chat_id:
        msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 20})
        for m in reversed((msgs.get("result") or {}).get("messages") or []):
            print(f"  comment[{m.get('id')}] author={m.get('author_id')}: "
                  + str(m.get("text") or "")[:500].replace("\n", " ⏎ "))
