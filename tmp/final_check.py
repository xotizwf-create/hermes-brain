"""Final verification after the model switch: services, config, real tool-using turn, crons."""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/var/www/albery")
import yaml  # noqa: E402

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
cfg = yaml.safe_load(Path("/root/.hermes/config.yaml").read_text(encoding="utf-8"))
print("model.default:", cfg["model"]["default"], "| effort:", cfg["model"].get("reasoning_effort"))

for unit in ("hermes-gateway", "albery", "albery-tg"):
    r = subprocess.run(["systemctl", "is-active", unit], capture_output=True, text=True)
    print(f"{unit}: {r.stdout.strip()}")

# real tool-using turn on the DEFAULT model (what employees actually get)
t0 = time.time()
r = subprocess.run(["hermes", "-z", "Сколько задач в работе у Александра Никитенко? Кратко.",
                    "-t", "albery,web", "--yolo"],
                   capture_output=True, text=True, timeout=300, cwd="/root", env=ENV)
print(f"\nreal agent turn: rc={r.returncode} {time.time()-t0:.0f}s")
print((r.stdout or r.stderr).strip()[:400])

c = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=90, env=ENV)
print("\ncrons active:", (c.stdout or "").count("[active]"))
print("cron names:", [ln.split(":", 1)[1].strip() for ln in (c.stdout or "").splitlines() if "Name:" in ln])
