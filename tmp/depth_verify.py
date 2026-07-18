"""Проверка фикса: те же вопросы, где агент угадывал имена. Должен проверять источники,
не угадывать и показывать, на чём основан ответ."""
import subprocess
import time

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
QUESTIONS = [
    "Кто ответственный за согласование отпуска у Натальи Горюновой?",
    "Кто ответственный за согласование отпуска у Натальи Горюновой?",
    "Кто у нас отвечает за закупки и какие по ним правила?",
]

for q in QUESTIONS:
    t0 = time.time()
    r = subprocess.run(["hermes", "-z", q, "-t", "agent-main,web", "--yolo"],
                       capture_output=True, text=True, timeout=600, cwd="/root", env=ENV)
    out = (r.stdout or "").strip()
    low = out.lower()
    sources = sum(k in low for k in ("оргструктур", "регламент", "матриц", "документ", "базе знаний"))
    guessy = any(k in low for k in ("вероятно", "скорее всего", "предположительно"))
    print(f"\n[{time.time()-t0:.0f}с | {len(out)} симв | источников: {sources} | догадки: {guessy}]")
    print("В: " + q)
    print("О: " + out[:600].replace("\n", "\n   "))
