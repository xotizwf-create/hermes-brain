"""E2E #2: (a) the reply must be authored by the summoned bot itself;
(b) summoning a bot the author cannot use -> refusal FROM that bot.
Test task is created and deleted; authors: 16 (admin, has access) and 28 (no access to юрист)."""
import json
import sys
import time
import urllib.request

sys.path.insert(0, "/var/www/albery")
from shared.db import load_env_value  # noqa: E402

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")
BOT_IDS = {24, 70, 72, 78}
FAILED = []


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def wait_bot_reply(chat_id, after_id, tries=36):
    for i in range(tries):
        time.sleep(10)
        msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 15})
        for m in sorted((msgs.get("result") or {}).get("messages") or [],
                        key=lambda x: int(x.get("id") or 0)):
            if int(m.get("id") or 0) > int(after_id) and int(m.get("author_id") or 0) in BOT_IDS:
                return m
        print(f"  waiting... {(i + 1) * 10}s", flush=True)
    return None


res = call("tasks.task.add", {"fields": {
    "TITLE": "ТЕСТ ответов ботов — УДАЛИТЬ",
    "DESCRIPTION": "Проверка: ответ от позванного бота; отказ при отсутствии доступа.",
    "RESPONSIBLE_ID": 16}})
task_id = int(((res.get("result") or {}).get("task") or {}).get("id"))
chat = call("tasks.task.get", {"taskId": task_id, "select": ["ID", "CHAT_ID"]})
chat_id = ((chat.get("result") or {}).get("task") or {}).get("chatId")
print("task:", task_id, "chat:", chat_id)

# (a) main agent, author WITH access -> reply authored by bot 24
c1 = call("task.commentitem.add", {"TASKID": task_id, "FIELDS": {
    "POST_MESSAGE": "Албери, кто ответственный по этой задаче?", "AUTHOR_ID": 16}}).get("result")
m = wait_bot_reply(chat_id, c1)
if m and int(m["author_id"]) == 24 and not str(m.get("text", "")).startswith("🤖"):
    print(f"OK  main reply authored by bot 24: {str(m.get('text'))[:150]}")
else:
    FAILED.append("main reply not from bot 24")
    print("ERR main reply:", (m or {}).get("author_id"), str((m or {}).get("text"))[:150])
last = int((m or {}).get("id") or c1)

# (b) юрист, author id 28 WITHOUT access -> refusal from bot 70
c2 = call("task.commentitem.add", {"TASKID": task_id, "FIELDS": {
    "POST_MESSAGE": "Агент-юрист, проверь договор", "AUTHOR_ID": 28}}).get("result")
m = wait_bot_reply(chat_id, max(last, int(c2)), tries=12)
if m and int(m["author_id"]) == 70 and "нет доступа" in str(m.get("text", "")):
    print(f"OK  refusal from bot 70: {str(m.get('text'))[:150]}")
else:
    FAILED.append("no refusal from bot 70")
    print("ERR refusal:", (m or {}).get("author_id"), str((m or {}).get("text"))[:200])

call("tasks.task.delete", {"taskId": task_id})
print("task deleted")
print("E2E " + ("FAILED: " + ", ".join(FAILED) if FAILED else "OK"))
sys.exit(1 if FAILED else 0)
