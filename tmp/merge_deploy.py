"""On prod (Linux): merge feat/org-structure into main, rename the colon-file so Windows clones
work again, push, then apply the deploy (compile + safe restart + smoke)."""
import subprocess
import time
from pathlib import Path

REPO = "/var/www/albery"


def git(*args, check=True):
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, timeout=180)
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} -> {out[:300]}")
    return out


print("status before:", git("status", "--short")[:200] or "(clean)")
git("fetch", "origin")
print("merge:", git("merge", "--no-edit", "origin/feat/org-structure")[-200:])

# rename the file whose name breaks Windows checkouts
bad = list(Path(REPO, "agent_knowledge/agents").glob("*/learned/*:*"))
for p in bad:
    new = p.with_name(p.name.replace(":", "∶"))
    print("renaming:", p.name, "->", new.name)
    git("mv", str(p.relative_to(REPO)), str(new.relative_to(REPO)))
if bad:
    git("commit", "-m", "fix(registry): rename learned instruction with a colon (Windows clones)")
print("push:", git("push", "origin", "main")[-120:])

# deploy
rc = subprocess.run([f"{REPO}/.venv/bin/python", "-m", "py_compile",
                     f"{REPO}/mcp/context_server.py", f"{REPO}/agent_knowledge.py"],
                    capture_output=True, text=True)
print("compile rc:", rc.returncode, (rc.stderr or "")[:200])
assert rc.returncode == 0

import sys
sys.path.insert(0, REPO)
from shared.db import connect  # noqa: E402
for _ in range(24):
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM bitrix_inflight_turns")
        n = cur.fetchone()["n"]
    if n == 0:
        break
    print("  waiting for idle window, inflight =", n)
    time.sleep(15)
subprocess.run(["systemctl", "restart", "albery"], check=True)
time.sleep(5)
print("albery:", subprocess.run(["systemctl", "is-active", "albery"], capture_output=True, text=True).stdout.strip())
smoke = subprocess.run([f"{REPO}/.venv/bin/python", f"{REPO}/scripts/deploy_smoke.py"],
                       capture_output=True, text=True, timeout=600)
print("\n".join((smoke.stdout or "").strip().splitlines()[-3:]))
