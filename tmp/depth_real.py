"""Воспроизводим РЕАЛЬНЫЙ провал: вопрос ровно как у владельца (без подсказок «проверь то и это»).
Сравниваем текущую персону и персону без «1-2 вызова»."""
import shutil
import subprocess
import time
from pathlib import Path

CFG = Path("/root/.hermes/config.yaml")
ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
BACKUP = CFG.with_name(f"config.yaml.bak-depthreal-{time.strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(CFG, BACKUP)

Q = "Кто ответственный за согласование отпуска у Натальи Горюновой?"

OLD = "правильный инструмент с первого раза, обычно 1-2 вызова, без пробных; факты проверяй инструментами, не выдумывай"
NEW = ("бери правильный инструмент, но НЕ экономь на глубине: проверяй ВСЕ релевантные источники "
       "(оргструктура, регламенты, матрица решений, задачи, переписки), пока ответ не станет полным; "
       "лучше лишний вызов, чем поверхностный ответ; факты проверяй инструментами, не выдумывай")


def run(label):
    t0 = time.time()
    r = subprocess.run(["hermes", "-z", Q, "-t", "agent-main,web", "--yolo"],
                       capture_output=True, text=True, timeout=600, cwd="/root", env=ENV)
    out = (r.stdout or "").strip()
    # признаки глубины: упомянул ли несколько источников
    depth = sum(k in out.lower() for k in ("оргструктур", "регламент", "матриц", "документ", "задач"))
    print(f"\n[{label}] {time.time()-t0:.0f}с | ответ {len(out)} симв | источников упомянуто: {depth}")
    print("  " + out[:450].replace("\n", "\n  "))


print("########## СЕЙЧАС (персона с «1-2 вызова») ##########")
run("сейчас")
run("сейчас, повтор")

text = CFG.read_text(encoding="utf-8")
assert OLD in text
CFG.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
print("\n########## ПОСЛЕ ФИКСА персоны (глубина вместо экономии) ##########")
run("фикс")
run("фикс, повтор")

shutil.copy2(BACKUP, CFG)
print("\nконфиг возвращён к исходному (бэкап:", BACKUP, ")")
