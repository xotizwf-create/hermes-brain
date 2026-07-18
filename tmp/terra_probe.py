"""Probe: is gpt-5.6-terra reachable on our codex account? Current model config + a live turn."""
import re
import subprocess
from pathlib import Path

cfg = Path("/root/.hermes/config.yaml").read_text(encoding="utf-8")
for ln in cfg.splitlines()[:6]:
    print("cfg:", ln)

# codex CLI version (need 0.144.0+ for 5.6)
for exe in ("codex",):
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
        print(f"{exe} --version:", (r.stdout or r.stderr).strip()[:80])
    except Exception as exc:  # noqa: BLE001
        print(f"{exe}: {str(exc)[:80]}")

# does codex list 5.6?
try:
    r = subprocess.run(["codex", "--help"], capture_output=True, text=True, timeout=30)
    print("codex models in help:", [w for w in re.findall(r"gpt-5\.[0-9a-z-]+", r.stdout or "")][:8])
except Exception as exc:  # noqa: BLE001
    print("codex help:", str(exc)[:80])

# live hermes turn on gpt-5.6-terra (does the account accept it?)
for model in ("gpt-5.6-terra", "gpt-5.6-sol"):
    try:
        r = subprocess.run(["hermes", "-z", "Ответь одним словом: работаю", "-m", model],
                           capture_output=True, text=True, timeout=180,
                           cwd="/root", env={"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"})
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        print(f"\n[{model}] rc={r.returncode} out={out[:120]!r}")
        if err:
            print(f"  stderr: {err[:250]}")
    except Exception as exc:  # noqa: BLE001
        print(f"[{model}] EXC {str(exc)[:120]}")
