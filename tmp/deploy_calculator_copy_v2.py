from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import tarfile
from datetime import datetime


ROOT = pathlib.Path("/var/www/albery").resolve()
EXPECTED_COMMIT = "6eded8eef965e0f209ecf7b9f6825b6553e5e583"
ARCHIVE = pathlib.Path("/root/claude_tasks/calculator-dist-6eded8e.tar.gz")
EXPECTED_SHA256 = "a1f1e91b75595a4af40d0add7d7499c2f6415f7df00af0a99c26d510536b25b6"


def output(args: list[str], *, cwd: pathlib.Path | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run(args: list[str], *, cwd: pathlib.Path | None = None) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=cwd, check=True, text=True)


if ROOT != pathlib.Path("/var/www/albery"):
    raise SystemExit("Unexpected production root.")
if not ARCHIVE.is_file():
    raise SystemExit("Release archive is missing.")
archive_sha = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
if archive_sha != EXPECTED_SHA256:
    raise SystemExit(f"Release archive checksum mismatch: {archive_sha}")
if output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
    raise SystemExit("Tracked production worktree is dirty.")
for service in ("albery", "albery-tg", "hermes-gateway", "nginx"):
    if output(["systemctl", "is-active", service]) != "active":
        raise SystemExit(f"Service is not active before deploy: {service}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = pathlib.Path(f"/var/backups/albery/code/pre-calculator-copy-{stamp}")
backup.mkdir(mode=0o700, parents=True)
(backup / "git-head.txt").write_text(
    output(["git", "rev-parse", "HEAD"], cwd=ROOT) + "\n",
    encoding="utf-8",
)
shutil.copy2(ROOT / "calculator/index.html", backup / "index.html")
shutil.copy2(ROOT / "calculator/src/App.tsx", backup / "App.tsx")
with tarfile.open(backup / "calculator-dist.tar.gz", "w:gz") as archive:
    archive.add(ROOT / "calculator/dist", arcname="dist")
os.chmod(backup / "git-head.txt", 0o600)
os.chmod(backup / "index.html", 0o600)
os.chmod(backup / "App.tsx", 0o600)
os.chmod(backup / "calculator-dist.tar.gz", 0o600)
print(f"BACKUP={backup}")

run(["git", "fetch", "origin", "main"], cwd=ROOT)
origin_commit = output(["git", "rev-parse", "origin/main"], cwd=ROOT)
if origin_commit != EXPECTED_COMMIT:
    raise SystemExit(
        f"origin/main moved unexpectedly: {origin_commit[:12]}"
    )
run(["git", "pull", "--ff-only", "origin", "main"], cwd=ROOT)
if output(["git", "rev-parse", "HEAD"], cwd=ROOT) != EXPECTED_COMMIT:
    raise SystemExit("Production did not reach the expected commit.")

calculator = (ROOT / "calculator").resolve()
if calculator.parent != ROOT:
    raise SystemExit("Calculator path escaped production root.")
staging = calculator / f"dist.new-{stamp}"
staging.mkdir(mode=0o755)
with tarfile.open(ARCHIVE, "r:gz") as archive:
    for member in archive.getmembers():
        target = (staging / member.name).resolve()
        if staging not in target.parents and target != staging:
            raise SystemExit("Unsafe path in release archive.")
    archive.extractall(staging)

index_text = (staging / "index.html").read_text(encoding="utf-8")
if "Калькулятор расчёта ИУ" not in index_text:
    raise SystemExit("Expected page title is absent from the release.")
if not list((staging / "assets").glob("*.js")):
    raise SystemExit("Release JavaScript asset is absent.")

live = calculator / "dist"
previous = calculator / f"dist.bak.pre-6eded8e-{stamp}"
live.rename(previous)
staging.rename(live)
print(f"PREVIOUS_DIST={previous}")

html = output(
    [
        "curl",
        "-fsS",
        "https://www.m4s.ru/Калькулятор/",
    ]
)
if "Калькулятор расчёта ИУ" not in html:
    raise SystemExit("Public page did not return the new release.")
asset_path = next((live / "assets").glob("*.js"))
asset_url = (
    "https://www.m4s.ru/Калькулятор/assets/"
    + asset_path.name
)
run(["curl", "-fsS", "-o", "/dev/null", asset_url])
if output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
    raise SystemExit("Tracked production worktree became dirty.")
for service in ("albery", "albery-tg", "hermes-gateway", "nginx"):
    if output(["systemctl", "is-active", service]) != "active":
        raise SystemExit(f"Service is not active after deploy: {service}")

print("DEPLOYED_COMMIT=" + output(["git", "rev-parse", "HEAD"], cwd=ROOT))
print("DEPLOY_OK")
