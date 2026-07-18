"""Health of the REAL brain creds + safe update of the codex CLI (not in the agents' path).
Backs up hermes auth.json first; checks RAM before npm (2GB box rule)."""
import shutil
import subprocess
import time
from pathlib import Path


def run(cmd, timeout=300):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str),
                       env={"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"})
    return (r.returncode, (r.stdout or "") + (r.stderr or ""))

print("=== RAM before (2GB box rule) ===")
print(run("free -m | head -2")[1])

print("=== brain creds health (this is what agents actually use) ===")
rc, out = run(["hermes", "auth", "status", "openai-codex"], timeout=90)
print(out[:600])

ts = time.strftime("%Y%m%d_%H%M%S")
src = Path("/root/.hermes/auth.json")
bak = Path(f"/root/.hermes/auth.json.bak-{ts}")
shutil.copy2(src, bak)
bak.chmod(0o600)
print(f"backup of brain creds: {bak} ({bak.stat().st_size} bytes, 600)")

print("\n=== codex CLI: 0.134.0 -> latest (npm global; NOT used by agents) ===")
rc, out = run("npm install -g @openai/codex@latest 2>&1 | tail -4", timeout=600)
print(out.strip()[:600])
print("new version:", run("codex --version")[1].strip()[:60])

print("\n=== agents still fine after the update? (real turn on the default model) ===")
t0 = time.time()
rc, out = run(["hermes", "-z", "Ответь одним словом: работаю", "-t", "albery"], timeout=240)
print(f"turn rc={rc} {time.time()-t0:.0f}s out={out.strip()[:80]!r}")

print("\n=== codex CLI login state (separate from the brain; only for coding delegation) ===")
print(run(["codex", "login", "status"], timeout=60)[1].strip()[:200])
print("\nRAM after:")
print(run("free -m | head -2")[1])
