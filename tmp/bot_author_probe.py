"""Probe: can a task comment be authored AS a bot user (AUTHOR_ID=<bot id>)?
Creates a test task, posts comments with AUTHOR_ID 24 (Агент Албери bot) and 70 (юрист bot),
reads back the authors, deletes the task. Also: agent access lists for the refusal test."""
import json
import sys
import time
import urllib.request

sys.path.insert(0, "/var/www/albery")
from shared.db import connect, load_env_value  # noqa: E402

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


res = call("tasks.task.add", {"fields": {"TITLE": "ТЕСТ автор-бот — УДАЛИТЬ", "RESPONSIBLE_ID": 16}})
task_id = int(((res.get("result") or {}).get("task") or {}).get("id"))
print("task:", task_id)

for author in (24, 70):
    r = call("task.commentitem.add", {"TASKID": task_id, "FIELDS": {
        "POST_MESSAGE": f"проба автора {author}", "AUTHOR_ID": author}})
    print(f"add as {author}:", r.get("result"))

time.sleep(2)
chat = call("tasks.task.get", {"taskId": task_id, "select": ["ID", "CHAT_ID"]})
chat_id = ((chat.get("result") or {}).get("task") or {}).get("chatId")
msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 10})
for m in (msgs.get("result") or {}).get("messages") or []:
    print(f"  msg[{m.get('id')}] author={m.get('author_id')}: {str(m.get('text'))[:60]}")
users = (msgs.get("result") or {}).get("users") or []
for u in users:
    print("  user:", u.get("id"), u.get("name"), "bot:" , u.get("bot"))

call("tasks.task.delete", {"taskId": task_id})
print("task deleted")

# access lists: who can talk to each subagent (empty members = open to non-none tier)
with connect() as conn, conn.cursor() as cur:
    cur.execute("""SELECT a.slug, a.name, a.bitrix_bot_id,
                          ARRAY(SELECT m.bitrix_user_id FROM agent_members m WHERE m.agent_id = a.id) AS members
                   FROM agents a WHERE a.is_active ORDER BY a.slug""")
    for r in cur.fetchall():
        print("agent:", dict(r))
    cur.execute("SELECT bitrix_user_id, tier FROM agent_access ORDER BY bitrix_user_id LIMIT 30")
    for r in cur.fetchall():
        print("access:", dict(r))
