"""Diagnose the missed mention in «Рекомендации 09.07» (read-only)."""
import json
import subprocess
import sys
import urllib.request

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402
from shared.db import connect, load_env_value  # noqa: E402

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


# 1) find the task + its chat messages
res = call("tasks.task.list", {"filter": {"%TITLE": "Рекомендации 09.07"},
                               "select": ["ID", "TITLE", "STATUS", "RESPONSIBLE_ID", "CREATED_BY", "CHAT_ID"]})
tasks = (res.get("result") or {}).get("tasks") or []
for t in tasks:
    print("TASK", t.get("id"), "|", t.get("title"), "| resp", t.get("responsibleId"),
          "| createdBy", t.get("createdBy"), "| chat", t.get("chatId"))
if not tasks:
    print("task not found by title");  sys.exit(1)
task = tasks[0]
task_id, chat_id = int(task["id"]), task.get("chatId")

msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 15})
mention_id = None
for m in sorted((msgs.get("result") or {}).get("messages") or [], key=lambda x: int(x.get("id") or 0)):
    text = str(m.get("text") or "")
    print(f"  msg[{m.get('id')}] author={m.get('author_id')}: {text[:160]}")
    low = text.lower()
    if "албери" in low or "albery" in low.replace("_", ""):
        mention_id = int(m.get("id"))
print("mention candidate id:", mention_id)

# 2) did the EVENT arrive? journal for tasks-events endpoint + task-mention lines
out = subprocess.run(["bash", "-c",
                      "journalctl -u albery --since '-4 hours' --no-pager | "
                      "grep -E 'events/tasks|task-mention|task-comment' | tail -20"],
                     capture_output=True, text=True)
print("=== journal (events/tasks + mention) ===")
print(out.stdout[-3000:] or "(no lines)")

# 3) dedupe table
with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT * FROM bitrix_task_comment_seen ORDER BY created_at DESC LIMIT 5")
    for r in cur.fetchall():
        print("seen:", dict(r))

# 4) what would the handler say about the mention comment (WITHOUT claiming/replying)?
if mention_id:
    c = b24bot._b24_fetch_task_comment(task_id, mention_id)
    print("fetch_comment:", {k: str(v)[:100] for k, v in (c or {}).items()} if c else None)
    if c:
        targets = b24bot._b24_task_targets()
        tgt = b24bot._b24_task_pick_agent(c.get("text") or "", targets)
        print("picked agent:", (tgt or {}).get("name"))
        bot_authors = b24bot._b24_task_bot_author_ids() | {b24bot.to_int(t["bot_id"]) for t in targets if t.get("bot_id")}
        print("author in bot_authors:", b24bot.to_int(c.get("author_id")) in bot_authors,
              "| author:", c.get("author_id"))
        if tgt:
            allowed = (b24bot._b24_main_allows(c.get("author_id")) if tgt["is_main"]
                       else b24bot._b24_task_subagent_allows(tgt["slug"], c.get("author_id")))
            print("access allowed:", allowed)

# 5) event bindings still there?
endpoint, token = b24bot._b24_app_access_token()
data = b24bot._b24_app_call(endpoint, token, "event.get", {})
print("bindings:", [(e.get("event")) for e in (data.get("result") or [])])
