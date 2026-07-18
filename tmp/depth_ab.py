"""Замер ГЛУБИНЫ: сколько инструментов агент зовёт за ход и насколько содержателен ответ.
Сравниваем: текущая персона (с «1-2 вызова») / персона без неё / effort=high.
Инструменты считаем по журналу MCP за окно хода."""
import re
import shutil
import subprocess
import time
from pathlib import Path

CFG = Path("/root/.hermes/config.yaml")
ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
BACKUP = CFG.with_name(f"config.yaml.bak-depthtest-{time.strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(CFG, BACKUP)
print("бэкап конфига:", BACKUP)

QUESTION = ("Кто ответственный за согласование отпуска у Натальи Горюновой? "
            "Проверь и оргструктуру, и регламенты.")


def tool_calls_since(ts: float) -> int:
    since = time.strftime("%H:%M:%S", time.localtime(ts))
    out = subprocess.run(
        ["bash", "-c", f"journalctl -u albery --since '{since}' --no-pager | "
                       f"grep -cE 'POST /mcp-agent/|POST /mcp-core/|POST /mcp/' || true"],
        capture_output=True, text=True).stdout.strip()
    return int(out or 0)


def run(label):
    t0 = time.time()
    r = subprocess.run(["hermes", "-z", QUESTION, "-t", "agent-main,web", "--yolo"],
                       capture_output=True, text=True, timeout=600, cwd="/root", env=ENV)
    dt = time.time() - t0
    out = (r.stdout or "").strip()
    calls = tool_calls_since(t0)
    print(f"\n[{label}] {dt:.0f}с | вызовов инструментов ≈{calls} | ответ {len(out)} симв")
    print("  " + out[:400].replace("\n", "\n  "))
    return dt, calls, len(out)


print("\n########## 1) КАК СЕЙЧАС (персона с «1-2 вызова», effort=medium) ##########")
run("сейчас")

print("\n########## 2) БЕЗ «1-2 вызова» в персоне ##########")
text = CFG.read_text(encoding="utf-8")
old = "правильный инструмент с первого раза, обычно 1-2 вызова, без пробных; факты проверяй инструментами, не выдумывай"
new = ("бери правильный инструмент, но НЕ экономь на глубине: проверяй столько источников, "
       "сколько нужно для точного ответа (оргструктура, регламенты, задачи, переписки), "
       "лучше лишний вызов, чем поверхностный ответ; факты проверяй инструментами, не выдумывай")
assert old in text, "якорь персоны не найден"
CFG.write_text(text.replace(old, new, 1), encoding="utf-8")
print("персона поправлена (без ограничения вызовов)")
run("без «1-2 вызова»")

print("\n########## 3) + effort=high ##########")
text = CFG.read_text(encoding="utf-8")
text = text.replace("  reasoning_effort: medium\n", "  reasoning_effort: high\n", 1)
CFG.write_text(text, encoding="utf-8")
print("effort:", re.search(r"model:\n  default: \S+\n  provider: \S+\n(?:.*\n)*?  reasoning_effort: (\S+)",
                           CFG.read_text(encoding='utf-8')).group(1))
run("без ограничений + high")

print("\n########## ОТКАТ конфига к исходному ##########")
shutil.copy2(BACKUP, CFG)
print("восстановлено из", BACKUP)
