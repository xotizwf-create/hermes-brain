import pathlib
import subprocess
import sys

base = pathlib.Path("/var/www/albery")
sys.path.insert(0, str(base))

import webread

print("head=" + subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=base, text=True
).strip())
tracked = subprocess.check_output(
    ["git", "status", "--short", "--untracked-files=no"], cwd=base, text=True
).strip()
print("tracked_worktree=" + ("clean" if not tracked else "dirty"))

for service in ("albery", "albery-tg", "hermes-gateway", "nginx"):
    state = subprocess.check_output(
        ["systemctl", "is-active", service], text=True
    ).strip()
    print(f"service_{service}={state}")

try:
    webread.assert_public_http_url("http://127.0.0.1/private")
except Exception as exc:
    print(f"ssrf_loopback=blocked:{type(exc).__name__}")
else:
    print("ssrf_loopback=NOT_BLOCKED")

try:
    webread.assert_public_http_url("http://169.254.169.254/latest/meta-data")
except Exception as exc:
    print(f"ssrf_metadata=blocked:{type(exc).__name__}")
else:
    print("ssrf_metadata=NOT_BLOCKED")

for service in ("albery", "albery-tg", "hermes-gateway"):
    result = subprocess.run(
        [
            "journalctl",
            "-u",
            f"{service}.service",
            "-p",
            "err",
            "--since",
            "2026-07-29 13:34:00",
            "--no-pager",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    meaningful = [
        line for line in result.stdout.splitlines()
        if line.strip() and not line.startswith("-- No entries --")
    ]
    print(f"errors_{service}={len(meaningful)}")
