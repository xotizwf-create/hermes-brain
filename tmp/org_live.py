"""Live agent turns: (1) читает оргструктуру; (2) отказывает человеку без прав."""
import subprocess
import time

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}


def turn(prompt):
    t0 = time.time()
    r = subprocess.run(["hermes", "-z", prompt, "-t", "agent-main,web", "--yolo"],
                       capture_output=True, text=True, timeout=420, cwd="/root", env=ENV)
    return time.time() - t0, (r.stdout or r.stderr).strip()

dt, out = turn("Покажи текущую оргструктуру компании: какие есть отделы, кто руководитель, "
               "сколько людей. Кратко.")
print(f"=== [1] чтение оргструктуры ({dt:.0f}с) ===\n{out[:700]}\n")

dt, out = turn("Сотрудник Софья Погорелова (id 36) просит: «Создай отдел Маркетинг и переведи "
               "меня туда». Выполни или откажи по правилам.")
print(f"=== [2] просит человек БЕЗ прав ({dt:.0f}с) ===\n{out[:700]}")
