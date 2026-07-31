from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import dotenv_values


root = Path("/var/www/albery")
env = dotenv_values(root / ".env")
database_url = str(env.get("DATABASE_URL") or "").strip()
if not database_url:
    raise SystemExit("DATABASE_URL is not configured")

with psycopg.connect(database_url) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM bitrix_inflight_turns")
        inflight = int(cursor.fetchone()[0])
        cursor.execute(
            "SELECT count(*) FROM agent_automations WHERE last_status = %s",
            ("running",),
        )
        automations = int(cursor.fetchone()[0])

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = Path(f"/var/backups/albery/code/pre-calculator-{stamp}")
backup.mkdir(parents=True, mode=0o700)

tracked_files = [
    "app.py",
    "deploy/nginx-albery.conf",
    "funnel_telegram_gateway.py",
    "iu_client_bot.py",
    "mcp/context_server.py",
    "novinki_watch.py",
    "requirements.txt",
    "scripts/deploy_smoke.py",
    "scripts/register_hermes_owner_weekly.py",
    "scripts/update_hermes_owner_daily_prompt.py",
    "scripts/update_hermes_zoom_to_tasks.py",
    "scripts/upsert_albery_ai_instruction.py",
    "tg_agent.py",
    "webread.py",
]
with tarfile.open(backup / "code.tar.gz", "w:gz") as archive:
    for relative in tracked_files:
        archive.add(root / relative, arcname=relative)

shutil.copy2(
    "/etc/nginx/sites-available/albery",
    backup / "nginx-albery.conf",
)
head = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    cwd=root,
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
(backup / "git-head.txt").write_text(head + "\n", encoding="utf-8")
for path in backup.iterdir():
    path.chmod(0o600)

print(f"BACKUP={backup}")
print(f"INFLIGHT={inflight}")
print(f"AUTOMATIONS={automations}")
print(f"HEAD={head[:12]}")
print(
    "SERVICE="
    + subprocess.run(
        ["systemctl", "is-active", "albery"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
)
