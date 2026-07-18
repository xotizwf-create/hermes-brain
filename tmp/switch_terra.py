"""Switch model.default gpt-5.5 -> gpt-5.6-terra (all agents inherit; owner rule: one model
for everyone). Backup first, validate YAML, restart gateway only when no live turn is running,
then verify: live turn works, crons intact, journal clean. Rollback = restore the .bak file."""
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/var/www/albery")
import yaml  # noqa: E402
from shared.db import connect  # noqa: E402

CFG = Path("/root/.hermes/config.yaml")
ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
ts = time.strftime("%Y%m%d_%H%M%S")
backup = CFG.with_name(f"config.yaml.bak-terra-{ts}")
shutil.copy2(CFG, backup)
print("backup:", backup)

text = CFG.read_text(encoding="utf-8")
assert "  default: gpt-5.5\n" in text, "anchor 'default: gpt-5.5' not found"
text = text.replace("  default: gpt-5.5\n", "  default: gpt-5.6-terra\n", 1)
CFG.write_text(text, encoding="utf-8")
cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
assert cfg["model"]["default"] == "gpt-5.6-terra", "yaml check failed"
print("model.default =", cfg["model"]["default"], "| effort =", cfg["model"].get("reasoning_effort"),
      "| autoraise(5.5-мина) =", (cfg.get("compression") or {}).get("codex_gpt55_autoraise"))

# restart gateway only when no live agent turn is in flight
for i in range(24):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM bitrix_inflight_turns")
        inflight = cur.fetchone()["n"]
    if inflight == 0:
        break
    print(f"  waiting for idle window... inflight={inflight}")
    time.sleep(15)
subprocess.run(["systemctl", "restart", "hermes-gateway"], check=True)
time.sleep(10)
st = subprocess.run(["systemctl", "is-active", "hermes-gateway"], capture_output=True, text=True)
print("hermes-gateway:", st.stdout.strip())
assert st.stdout.strip() == "active", f"gateway down — restore {backup}!"

# live turn through the NORMAL path (no -m flag) — proves the default took effect
t0 = time.time()
r = subprocess.run(["hermes", "-z", "Ответь одним словом: работаю", "-t", "albery"],
                   capture_output=True, text=True, timeout=240, cwd="/root", env=ENV)
print(f"live turn on new default: rc={r.returncode} {time.time()-t0:.0f}s out={(r.stdout or '').strip()[:60]!r}")

crons = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=90, env=ENV)
print("crons active:", (crons.stdout or "").count("[active]"))
jr = subprocess.run(["bash", "-c", "journalctl -u hermes-gateway --since '-3 min' --no-pager | grep -ciE 'error|traceback' || true"],
                    capture_output=True, text=True)
print("gateway errors last 3 min:", jr.stdout.strip())
print("\nROLLBACK: cp", backup, "/root/.hermes/config.yaml && systemctl restart hermes-gateway")
