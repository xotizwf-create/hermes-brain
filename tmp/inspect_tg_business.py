import hashlib
import json
import pathlib
import subprocess

base = pathlib.Path("/var/www/albery")
state_path = base / ".tg_agent_state.json"
raw = state_path.read_bytes()
state = json.loads(raw)
business = state.get("business") or {}

print(f"state_exists={state_path.exists()}")
print(f"state_mtime={state_path.stat().st_mtime_ns}")
print(f"state_sha256={hashlib.sha256(raw).hexdigest()}")
print(f"business_count={len(business)}")
for idx, (connection_id, info) in enumerate(business.items(), 1):
    info = info or {}
    masked = hashlib.sha256(str(connection_id).encode()).hexdigest()[:12]
    print(
        f"connection_{idx}=sha256:{masked} "
        f"enabled={info.get('enabled')!r} "
        f"can_reply={info.get('can_reply')!r} "
        f"updated_at={info.get('at')!r}"
    )

result = subprocess.run(
    [
        "journalctl",
        "-u",
        "albery-tg.service",
        "--since",
        "2026-07-29 13:33:00",
        "--no-pager",
        "-n",
        "120",
    ],
    capture_output=True,
    text=True,
    check=False,
)
print("journal_begin")
for line in result.stdout.splitlines():
    lowered = line.lower()
    if any(
        marker in lowered
        for marker in (
            "business",
            "poll",
            "error",
            "exception",
            "failed",
            "started",
            "stopped",
            "conflict",
            "unauthorized",
        )
    ):
        print(line[:500])
print("journal_end")
