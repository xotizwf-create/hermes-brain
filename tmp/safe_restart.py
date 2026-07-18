"""Restart albery ONLY when no live agent turns / automations are running.
Checks bitrix_inflight_turns and running agent_automations; waits up to ~6 min, then
restarts (graceful drain is built into the unit) and verifies the service came back."""
import subprocess
import sys
import time

sys.path.insert(0, "/var/www/albery")
from shared.db import connect  # noqa: E402


def busy_counts():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM bitrix_inflight_turns")
        inflight = cur.fetchone()["n"]
        try:
            cur.execute("SELECT COUNT(*) AS n FROM agent_automations WHERE status = 'running'")
            running = cur.fetchone()["n"]
        except Exception:  # noqa: BLE001
            conn.rollback()
            running = 0
    return inflight, running


for attempt in range(24):  # up to ~6 minutes
    inflight, running = busy_counts()
    print(f"check {attempt + 1}: inflight_turns={inflight} running_automations={running}", flush=True)
    if inflight == 0 and running == 0:
        break
    time.sleep(15)
else:
    print("STILL BUSY after 6 min — NOT restarting. Re-run later.")
    sys.exit(2)

subprocess.run(["systemctl", "restart", "albery"], check=True)
time.sleep(5)
state = subprocess.run(["systemctl", "is-active", "albery"], capture_output=True, text=True)
print("albery:", state.stdout.strip())
sys.exit(0 if state.stdout.strip() == "active" else 1)
