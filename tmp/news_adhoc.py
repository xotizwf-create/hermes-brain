"""Prove ad-hoc reuse: ask the news agent a question; it must use the STORED digest (fast),
not rebuild via get_tg_news. Timed hermes turn on the agent's own connector."""
import subprocess
import time

prompt = ("Пользователь спрашивает: «Что важного по WB за эту неделю, кратко?» "
          "Ответь по своей роли.")
cmd = ["hermes", "-z", prompt, "-t", "agent-novostnoy-agent,web", "--yolo"]
t0 = time.time()
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                      cwd="/root", env={"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"})
dt = time.time() - t0
out = (proc.stdout or "").strip()
print(f"turn took {dt:.0f}s, rc={proc.returncode}")
print("mentions stored-digest reuse:", "сохранённ" in out.lower() or "13.07" in out or "ИРП" in out)
print("\n--- answer ---\n", out[:1800])
