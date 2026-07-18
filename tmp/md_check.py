"""Deploy + проверка: markdown-таблица, прогнанная через РЕАЛЬНЫЙ путь отправки бота."""
import subprocess
import sys
import time

REPO = "/var/www/albery"
sys.path.insert(0, REPO)


def sh(*cmd, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


print(sh("git", "-C", REPO, "pull", "--ff-only", "origin", "main")[1].splitlines()[-1])
rc, out = sh(f"{REPO}/.venv/bin/python", "-m", "py_compile",
             f"{REPO}/b24bot.py", f"{REPO}/agent_automations.py")
print("compile rc:", rc, out[:200])
assert rc == 0

from shared.db import connect  # noqa: E402
for _ in range(24):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM bitrix_inflight_turns")
        n = cur.fetchone()["n"]
    if n == 0:
        break
    print("  ждём пустое окно, живых ходов:", n)
    time.sleep(15)
sh("systemctl", "restart", "albery")
time.sleep(5)
print("albery:", sh("systemctl", "is-active", "albery")[1])

import app  # noqa: E402,F401
from b24bot import bb_sanitize  # noqa: E402

RAW = """## Должности сотрудников

Собрал **полную** картину по 17 профилям:

| Сотрудник | ID | Должность | Статус |
|---|---:|---|---|
| Евгений Палей | 14 | Генеральный директор | подтверждено |
| Артур Степанян | 28 | Руководитель проекта | подтверждено |
| Анастасия Андрусяк | 42 | Бухгалтер | заполнено в Битрикс |

Подробности в `штатном расписании`, см. [документ](https://docs.google.com/x).
* уточнить: Софья
---
"""
print("\n=== БЫЛО (как уходило в чат) ===")
print(RAW)
print("=== СТАЛО (после фильтра) ===")
clean = bb_sanitize(RAW)
print(clean)
print("\n=== ПРОВЕРКИ ===")
print("палок «|» не осталось:", "|" not in clean)
print("markdown-звёздочек нет:", "**" not in clean and "* " not in clean)
print("решёток нет:", "#" not in clean)
print("ссылка стала BB:", "[URL=https://docs.google.com/x]документ[/URL]" in clean)
print("жирный стал BB:", "[b]" in clean)
