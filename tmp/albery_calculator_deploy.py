from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tarfile
import time
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import dotenv_values


root = Path("/var/www/albery").resolve()
expected_commit = "df4d4cd4dc55360ff3bbc36dcac765cd22af3fff"
expected_archive_sha = "d3f9803677726ba6bfe84e20a1ba97c3a555ce8beef8a5d7abbf54ed5a2bcb60"
archive_path = Path("/root/claude_tasks/calculator-dist-df4d4cd.tar.gz")
backup_path = Path("/var/backups/albery/code/pre-calculator-20260729_132946")
nginx_path = Path("/etc/nginx/sites-available/albery")


def run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    print("+", " ".join(args))
    return subprocess.run(args, cwd=cwd, check=True, text=True)


def output(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if not backup_path.is_dir():
    raise SystemExit(f"Required backup is missing: {backup_path}")
if not archive_path.is_file():
    raise SystemExit(f"Release archive is missing: {archive_path}")
actual_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
if actual_sha != expected_archive_sha:
    raise SystemExit(f"Release archive checksum mismatch: {actual_sha}")
if output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root):
    raise SystemExit("Tracked production tree is dirty; deployment stopped.")

run(["git", "fetch", "origin", "main"], cwd=root)
origin_commit = output(["git", "rev-parse", "origin/main"], cwd=root)
if origin_commit != expected_commit:
    raise SystemExit(
        f"origin/main moved unexpectedly: {origin_commit[:12]} != {expected_commit[:12]}"
    )
run(["git", "pull", "--ff-only", "origin", "main"], cwd=root)
if output(["git", "rev-parse", "HEAD"], cwd=root) != expected_commit:
    raise SystemExit("Production HEAD did not reach the expected commit.")

run([str(root / ".venv/bin/pip"), "install", "defusedxml>=0.7.1"], cwd=root)
run([
    str(root / ".venv/bin/python"),
    "-m",
    "py_compile",
    "app.py",
    "webread.py",
    "mcp/context_server.py",
    "iu_client_bot.py",
    "funnel_telegram_gateway.py",
    "scripts/deploy_smoke.py",
], cwd=root)

calculator_dir = (root / "calculator").resolve()
if calculator_dir.parent != root:
    raise SystemExit("Calculator path escaped the project root.")
staging = calculator_dir / "dist.new-df4d4cd"
if staging.exists():
    shutil.rmtree(staging)
staging.mkdir(parents=True)
with tarfile.open(archive_path, "r:gz") as archive:
    archive.extractall(staging)
index_text = (staging / "index.html").read_text(encoding="utf-8")
if "Калькулятор ИУ" not in index_text or not list((staging / "assets").glob("*.js")):
    raise SystemExit("Calculator release does not contain the expected build markers.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
live_dist = calculator_dir / "dist"
previous_dist = calculator_dir / f"dist.bak.pre-df4d4cd-{stamp}"
if live_dist.exists():
    live_dist.rename(previous_dist)
staging.rename(live_dist)
print(f"CALCULATOR_DIST={live_dist}")
print(f"PREVIOUS_DIST={previous_dist if previous_dist.exists() else 'none'}")

nginx_deploy_backup = nginx_path.with_name(f"albery.bak-calculator-{stamp}")
shutil.copy2(nginx_path, nginx_deploy_backup)
shutil.copy2(root / "deploy/nginx-albery.conf", nginx_path)
try:
    run(["nginx", "-t"])
except Exception:
    shutil.copy2(nginx_deploy_backup, nginx_path)
    raise
print(f"NGINX_BACKUP={nginx_deploy_backup}")

env = dotenv_values(root / ".env")
database_url = str(env.get("DATABASE_URL") or "").strip()
if not database_url:
    raise SystemExit("DATABASE_URL is not configured.")

deadline = time.monotonic() + 360
while True:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM bitrix_inflight_turns")
            bitrix_inflight = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT count(*) FROM agent_automations WHERE last_status = %s",
                ("running",),
            )
            automations = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT count(*) FROM funnel_workspace_ai_jobs "
                "WHERE processing_status = %s",
                ("leased",),
            )
            ai_leased = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT count(*) FROM funnel_workspace_outbox "
                "WHERE delivery_status IN (%s, %s)",
                ("leased", "sending"),
            )
            outbox_active = int(cursor.fetchone()[0])
    active = bitrix_inflight + automations + ai_leased + outbox_active
    print(
        "EMPTY_WINDOW="
        f"bitrix:{bitrix_inflight},automations:{automations},"
        f"ai:{ai_leased},outbox:{outbox_active}"
    )
    if active == 0:
        break
    if time.monotonic() >= deadline:
        raise SystemExit("No empty restart window within 360 seconds.")
    time.sleep(5)

run(["systemctl", "restart", "albery"])
run(["systemctl", "restart", "albery-tg"])
run(["systemctl", "is-active", "albery"])
run(["systemctl", "is-active", "albery-tg"])
run(["systemctl", "reload", "nginx"])
run([str(root / ".venv/bin/python"), "scripts/deploy_smoke.py"], cwd=root)

print("DEPLOYED_COMMIT=" + output(["git", "rev-parse", "--short", "HEAD"], cwd=root))
print("DEPLOY_OK")
