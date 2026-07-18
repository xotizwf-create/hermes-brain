"""A/B: gpt-5.5 vs gpt-5.6-terra on REAL Albery workloads (tool-calling + company knowledge).
Read-only prompts (no writes to Bitrix). Measures success, latency, tool usage, answer quality."""
import subprocess
import time

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
MODELS = ["gpt-5.5", "gpt-5.6-terra"]

CASES = [
    ("tools_tasks",
     "Сколько задач сейчас в работе у Александра Никитенко? Назови точное число и 2-3 названия. "
     "Используй инструменты, не выдумывай.",
     "albery,web"),
    ("knowledge",
     "Что записано в наших регламентах про ценообразование и работу с комиссиями? "
     "Назови конкретные документы. Если такого нет — честно скажи.",
     "albery,web"),
    ("news_agent",
     "Что важного по WB за неделю, кратко? Ответь по своей роли.",
     "agent-novostnoy-agent,web"),
]


def run(model, prompt, toolsets):
    t0 = time.time()
    r = subprocess.run(["hermes", "-z", prompt, "--provider", "openai-codex", "-m", model,
                        "-t", toolsets, "--yolo"],
                       capture_output=True, text=True, timeout=420, cwd="/root", env=ENV)
    return time.time() - t0, r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


for name, prompt, ts in CASES:
    print("=" * 70)
    print("CASE:", name)
    for model in MODELS:
        try:
            dt, rc, out, err = run(model, prompt, ts)
            ok = rc == 0 and out and not out.lower().startswith(("api call failed", "ошибка"))
            print(f"\n[{model}] {'OK ' if ok else 'FAIL'} {dt:.0f}s rc={rc} len={len(out)}")
            print("  " + (out[:420].replace("\n", "\n  ") if out else "(пусто) " + err[:200]))
        except subprocess.TimeoutExpired:
            print(f"\n[{model}] TIMEOUT >420s")
        except Exception as exc:  # noqa: BLE001
            print(f"\n[{model}] EXC {str(exc)[:150]}")
