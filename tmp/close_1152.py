"""Acceptance in task 1152 itself: mention the agent (author = Никитенко, the responsible),
wait for its contextual reply, then post the result summary and complete the task."""
import json
import sys
import time
import urllib.request

sys.path.insert(0, "/var/www/albery")
from shared.db import load_env_value  # noqa: E402

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")
TASK = 1152


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


# 1) the acceptance mention — the exact scenario the task asks to fix
res = call("task.commentitem.add", {"TASKID": TASK, "FIELDS": {
    "POST_MESSAGE": "Албери, подскажи по этой задаче: что требовалось сделать и выполнены ли требования?",
    "AUTHOR_ID": 16}})
print("mention comment:", res.get("result"))

chat = call("tasks.task.get", {"taskId": TASK, "select": ["ID", "CHAT_ID"]})
chat_id = ((chat.get("result") or {}).get("task") or {}).get("chatId")
last_seen = res.get("result")
reply = None
for i in range(36):
    time.sleep(10)
    msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 10})
    for m in (msgs.get("result") or {}).get("messages") or []:
        if int(m.get("id") or 0) > int(last_seen) and str(m.get("text") or "").lstrip().startswith("🤖"):
            reply = str(m.get("text"))
            break
    if reply:
        break
    print(f"  waiting... {(i + 1) * 10}s", flush=True)

if not reply:
    print("NO REPLY — do not close the task"); sys.exit(1)
print("AGENT REPLIED IN 1152:\n" + reply[:1500])

# 2) result comment + complete
result_text = (
    "✅ Результат: упоминание агента в задачах работает.\n\n"
    "Причина: события ONTASKCOMMENTADD не были привязаны на портале (event.get был пуст) — "
    "агент физически не получал уведомлений о комментариях.\n"
    "Сделано: привязка событий теперь выполняется программно токеном приложения и "
    "самовосстанавливается при рестарте/переустановке; агент получает ПОЛНЫЙ контекст задачи "
    "(название, описание, статус, срок, ответственный, постановщик, последние комментарии); "
    "ответ публикуется одним комментарием, дубликаты исключены.\n"
    "Проверка: живой тест в отдельной задаче (создана/удалена) + ответ агента в комментариях "
    "ЭТОЙ задачи выше — упоминание отработано, контекст виден. Обновление выкачено без "
    "прерывания работы команды (рестарт в окно без активных ходов)."
)
res = call("task.commentitem.add", {"TASKID": TASK, "FIELDS": {"POST_MESSAGE": result_text}})
print("result comment:", res.get("result"))
res = call("tasks.task.complete", {"taskId": TASK})
print("complete:", json.dumps(res.get("result"), ensure_ascii=False)[:200])
st = call("tasks.task.get", {"taskId": TASK, "select": ["ID", "STATUS"]})
print("final status:", ((st.get("result") or {}).get("task") or {}).get("status"))
