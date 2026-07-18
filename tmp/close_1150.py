"""Verify the deployed keyboard label, then close task 1150 with the release comment."""
import json
import sys
import urllib.request

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402
from shared.db import load_env_value  # noqa: E402

btn = next(b for b in b24bot._b24_keyboard() if b["COMMAND"] == "report_error")
print("deployed button:", btn["TEXT"])
assert btn["TEXT"] == "⚠️ Ошибка/Предложение", "label mismatch"

wh = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")


def call(method, payload):
    req = urllib.request.Request(f"{wh}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


result_text = (
    "✅ Результат: кнопка переименована в «⚠️ Ошибка/Предложение» и уже на проде (релиз 09.07.2026).\n\n"
    "Что изменилось:\n"
    "- кнопка в клавиатуре бота теперь называется «⚠️ Ошибка/Предложение» (у всех агентов; "
    "появится под следующим сообщением каждого бота);\n"
    "- бот просит описать «ошибку или предложение», принимает и то и другое;\n"
    "- уведомление в группу и лента мониторинга переформулированы под оба типа;\n"
    "- канал доставки и журнал (bitrix_error_reports) прежние — ничего из текущего не сломано.\n\n"
    "Проверка: авто-тест фиксирует новое название кнопки; команда report_error сохранена, "
    "старые регистрации кнопок работают."
)
res = call("task.commentitem.add", {"TASKID": 1150, "FIELDS": {"POST_MESSAGE": result_text}})
print("result comment:", res.get("result"))
res = call("tasks.task.complete", {"taskId": 1150})
st = call("tasks.task.get", {"taskId": 1150, "select": ["ID", "STATUS"]})
print("final status:", ((st.get("result") or {}).get("task") or {}).get("status"))
