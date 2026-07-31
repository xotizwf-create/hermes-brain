from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import tarfile
from datetime import datetime


ROOT = pathlib.Path("/var/www/albery").resolve()
EXPECTED_SERVER_HEAD = "a88fce9a6f4b8d2359777f31b4170de3ff7b3e23"
ARCHIVE = pathlib.Path("/root/claude_tasks/calculator-dist-cta-a88fce9.tar.gz")
EXPECTED_SHA256 = "6251ef93afa977ca66dff17a3b7b8452996ce46f2bf23c12c65020657985483b"


def output(args: list[str], *, cwd: pathlib.Path | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


if ROOT != pathlib.Path("/var/www/albery"):
    raise SystemExit("Unexpected production root.")
if not ARCHIVE.is_file():
    raise SystemExit("Release archive is missing.")
if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() != EXPECTED_SHA256:
    raise SystemExit("Release archive checksum mismatch.")
if output(["git", "rev-parse", "HEAD"], cwd=ROOT) != EXPECTED_SERVER_HEAD:
    raise SystemExit("Production HEAD changed; static-only deploy stopped.")
if output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
    raise SystemExit("Tracked production worktree is dirty.")
for service in ("albery", "albery-tg", "hermes-gateway", "nginx"):
    if output(["systemctl", "is-active", service]) != "active":
        raise SystemExit(f"Service is not active before deploy: {service}")

calculator = (ROOT / "calculator").resolve()
if calculator.parent != ROOT:
    raise SystemExit("Calculator path escaped production root.")
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = pathlib.Path(f"/var/backups/albery/code/pre-calculator-cta-{stamp}")
backup.mkdir(mode=0o700, parents=True)
with tarfile.open(backup / "calculator-dist.tar.gz", "w:gz") as archive:
    archive.add(calculator / "dist", arcname="dist")
os.chmod(backup / "calculator-dist.tar.gz", 0o600)
print(f"BACKUP={backup}")

staging = calculator / f"dist.new-cta-{stamp}"
staging.mkdir(mode=0o755)
with tarfile.open(ARCHIVE, "r:gz") as archive:
    for member in archive.getmembers():
        target = (staging / member.name).resolve()
        if staging not in target.parents and target != staging:
            raise SystemExit("Unsafe path in release archive.")
    archive.extractall(staging)

assets = list((staging / "assets").glob("*.js"))
if len(assets) != 1:
    raise SystemExit("Unexpected JavaScript release assets.")
bundle_text = assets[0].read_text(encoding="utf-8")
if "Обсудить подключение к ИУ" not in bundle_text:
    raise SystemExit("New CTA is absent from release.")
if "Обсудить индивидуальные условия" in bundle_text:
    raise SystemExit("Old CTA remains in release.")

live = calculator / "dist"
previous = calculator / f"dist.bak.pre-cta-{stamp}"
live.rename(previous)
staging.rename(live)
print(f"PREVIOUS_DIST={previous}")

asset_url = (
    "https://www.m4s.ru/"
    "%D0%9A%D0%B0%D0%BB%D1%8C%D0%BA%D1%83%D0%BB%D1%8F%D1%82%D0%BE%D1%80/assets/"
    + assets[0].name
)
public_bundle = output(["curl", "-fsS", asset_url])
if "Обсудить подключение к ИУ" not in public_bundle:
    raise SystemExit("Production bundle does not contain the new CTA.")
if "Обсудить индивидуальные условия" in public_bundle:
    raise SystemExit("Production bundle still contains the old CTA.")
for service in ("albery", "albery-tg", "hermes-gateway", "nginx"):
    if output(["systemctl", "is-active", service]) != "active":
        raise SystemExit(f"Service is not active after deploy: {service}")

print("SERVER_HEAD_UNCHANGED=" + EXPECTED_SERVER_HEAD)
print("DEPLOY_OK")
