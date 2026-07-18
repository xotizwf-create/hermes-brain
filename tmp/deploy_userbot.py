"""Finish the userbot deploy: verify telethon, pull, compile, restart albery-tg only."""
import subprocess
import time


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, **kw)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


rc, out = run(["/var/www/albery/.venv/bin/python", "-c", "import telethon;print(telethon.__version__)"])
print("telethon:", out.strip()[:40], "rc", rc)
if rc != 0:
    rc2, out2 = run(["/var/www/albery/.venv/bin/pip", "install", "-q", "telethon"])
    print("pip install rc", rc2, out2[-200:])
    rc, out = run(["/var/www/albery/.venv/bin/python", "-c", "import telethon;print(telethon.__version__)"])
    print("telethon now:", out.strip()[:40])

print(run(["git", "-C", "/var/www/albery", "pull", "--ff-only", "origin", "main"])[1].splitlines()[-1])
rc, out = run(["/var/www/albery/.venv/bin/python", "-m", "py_compile",
               "/var/www/albery/tg_agent.py", "/var/www/albery/tg_digest.py",
               "/var/www/albery/tg_userbot.py", "/var/www/albery/scripts/tg_userbot_login.py"])
print("compile rc", rc, out[:200])
assert rc == 0
subprocess.run(["systemctl", "restart", "albery-tg"], check=True)
time.sleep(6)
for unit in ("albery-tg", "albery"):
    rc, out = run(["systemctl", "is-active", unit])
    print(unit, out.strip())
print(run(["bash", "-c", "journalctl -u albery-tg --no-pager | tail -2"])[1])
