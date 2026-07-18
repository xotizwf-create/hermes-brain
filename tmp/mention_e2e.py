"""Live e2e of the in-task mention: create a TEST task, mention the agent in a comment
(author = Никитенко id 16), wait for the agent's reply in the task chat, then clean up."""
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


# 1) test task
res = call("tasks.task.add", {"fields": {
    "TITLE": "ТЕСТ упоминания агента — УДАЛИТЬ",
    "DESCRIPTION": "Проверка: агент должен ответить в комментарии при упоминании. "
                   "Ответственный должен подготовить отчёт по продажам до пятницы.",
    "RESPONSIBLE_ID": 16, "CREATED_BY": 16}})
task = (res.get("result") or {}).get("task") or {}
task_id = int(task.get("id"))
print("test task:", task_id)

# 2) mention comment authored by a real employee (Никитенко)
res = call("task.commentitem.add", {"TASKID": task_id, "FIELDS": {
    "POST_MESSAGE": "Албери, о чём эта задача и что нужно сделать?", "AUTHOR_ID": 16}})
print("comment id:", res.get("result"))

# 3) wait for the agent's reply in the task chat (event -> service -> LLM turn -> comment)
chat = call("tasks.task.get", {"taskId": task_id, "select": ["ID", "CHAT_ID"]})
chat_id = ((chat.get("result") or {}).get("task") or {}).get("chatId")
reply = None
for i in range(36):  # up to 6 min
    time.sleep(10)
    msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 20})
    for m in (msgs.get("result") or {}).get("messages") or []:
        if str(m.get("text") or "").lstrip().startswith("🤖"):
            reply = str(m.get("text"))
            break
    if reply:
        break
    print(f"  waiting... {(i + 1) * 10}s", flush=True)

if reply:
    print("AGENT REPLIED:\n" + reply[:1200])
else:
    print("NO REPLY after 6 min — check journal")

# full thread — verify there is exactly ONE agent reply and no meta-duplicates
time.sleep(15)  # let any stray second comment land before judging
msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 20})
agent_replies = 0
print("FULL THREAD:")
for m in sorted((msgs.get("result") or {}).get("messages") or [], key=lambda x: int(x.get("id") or 0)):
    text = str(m.get("text") or "")
    if text.lstrip().startswith("🤖"):
        agent_replies += 1
    print(f"  [{m.get('id')}] author={m.get('author_id')}: {text[:400]}")
print("agent replies in thread:", agent_replies)

# 4) dedupe row proof
with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT * FROM bitrix_task_comment_seen ORDER BY 1 DESC LIMIT 3")
    for r in cur.fetchall():
        print("seen:", dict(r))

# 5) cleanup the test task
call("tasks.task.delete", {"taskId": task_id})
print("test task deleted")
sys.exit(0 if reply else 1)
