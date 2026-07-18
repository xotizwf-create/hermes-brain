"""Тот самый провалившийся запрос на обеих моделях: кто ленится — Terra или наши инструкции?
Считаем, скольких сотрудников с должностями нашёл каждый прогон."""
import re
import subprocess
import time

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
PROMPT = ("Почитай документацию нашей компании и уточни, у кого какая должность. "
          "У кого должности нет — напиши мне, уточним вручную.")

# кого агент НАШЁЛ только со второй попытки (после «повнимательнее») — эталон полноты
EXPECTED = ["Палей", "Андрусяк", "Школьникова", "Степанян", "Горюнова", "Строгонов",
            "Хапова", "Тагирова"]


def run(model):
    t0 = time.time()
    cmd = ["hermes", "-z", PROMPT, "-t", "agent-main,web", "--yolo"]
    if model:
        cmd = ["hermes", "-z", PROMPT, "--provider", "openai-codex", "-m", model,
               "-t", "agent-main,web", "--yolo"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd="/root", env=ENV)
    out = (r.stdout or "").strip()
    found = [n for n in EXPECTED if n in out]
    return time.time() - t0, out, found


for model in ("gpt-5.5", "gpt-5.6-terra", "gpt-5.6-terra"):
    try:
        dt, out, found = run(model)
        print(f"\n[{model}] {dt:.0f}с | нашёл должностей: {len(found)}/{len(EXPECTED)} {found}")
        print("  ответ:", out[:300].replace("\n", " / "))
    except subprocess.TimeoutExpired:
        print(f"\n[{model}] TIMEOUT")
