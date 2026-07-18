"""Живой ход агента на запрос, который раньше рождал markdown-таблицу; проверяем, что
в чат уходит чисто (прогоняем ответ через тот же путь отправки)."""
import subprocess
import sys
import time

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from b24bot import bb_sanitize  # noqa: E402

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
t0 = time.time()
r = subprocess.run(["hermes", "-z",
                    "У кого какая должность? Собери полную картину по всем сотрудникам, "
                    "оформи наглядно.", "-t", "agent-main,web", "--yolo"],
                   capture_output=True, text=True, timeout=600, cwd="/root", env=ENV)
raw = (r.stdout or "").strip()
sent = bb_sanitize(raw)  # ровно это уходит в Битрикс
print(f"ход {time.time()-t0:.0f}с | модель вернула markdown-таблицу: {'|' in raw and '---' in raw}")
print("\n=== ЧТО УВИДИТ ЧЕЛОВЕК В ЧАТЕ ===")
print(sent[:1600])
print("\n=== ПРОВЕРКИ ===")
print("палок нет:", "|" not in sent)
print("markdown нет:", "**" not in sent and "##" not in sent and "`" not in sent)
