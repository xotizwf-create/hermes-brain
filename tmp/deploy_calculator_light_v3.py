from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import tarfile
from datetime import datetime


ROOT = pathlib.Path("/var/www/albery").resolve()
EXPECTED_COMMIT = "51a88d99afc9f68c983911aff542f9da2e97cb4a"
ARCHIVE = pathlib.Path("/root/claude_tasks/calculator-dist-51a88d9.tar.gz")
EXPECTED_SHA256 = "216e3b969c37bf4f2bb9bb859c64cf3df32c5636369be7aeb762fe8223c578b9"
PUBLIC_URL = (
    "https://www.m4s.ru/"
    "%D0%9A%D0%B0%D0%BB%D1%8C%D0%BA%D1%83%D0%BB%D1%8F%D1%82%D0%BE%D1%80/"
)


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
backup = pathlib.Path(f"/var/backups/albery/code/pre-calculator-light-{stamp}")
backup.mkdir(mode=0o700, parents=True)
(backup / "git-head.txt").write_text(
    output(["git", "rev-parse", "HEAD"], cwd=ROOT) + "\n",
    encoding="utf-8",
)
for relative in (
    "calculator/index.html",
    "calculator/src/App.tsx",
    "calculator/src/index.css",
):
    source = ROOT / relative
    target = backup / source.name
    shutil.copy2(source, target)
    os.chmod(target, 0o600)
with tarfile.open(backup / "calculator-dist.tar.gz", "w:gz") as archive:
    archive.add(ROOT / "calculator/dist", arcname="dist")
os.chmod(backup / "git-head.txt", 0o600)
os.chmod(backup / "calculator-dist.tar.gz", 0o600)
print(f"BACKUP={backup}")

run(["git", "fetch", "origin", "main"], cwd=ROOT)
origin_commit = output(["git", "rev-parse", "origin/main"], cwd=ROOT)
if origin_commit != EXPECTED_COMMIT:
    raise SystemExit(f"origin/main moved unexpectedly: {origin_commit[:12]}")
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
assets = list((staging / "assets").glob("*.js"))
if len(assets) != 1:
    raise SystemExit("Unexpected JavaScript release assets.")
bundle_text = assets[0].read_text(encoding="utf-8")
for marker in (
    "Укажите параметры товара",
    "Расчёт готов!",
    "Обсудить индивидуальные условия",
):
    if marker not in bundle_text:
        raise SystemExit(f"Release marker is absent: {marker}")
for removed_marker in ("bg-zinc-950", "Albery · Индивидуальные условия"):
    if removed_marker in bundle_text:
        raise SystemExit(f"Removed theme marker remains: {removed_marker}")

live = calculator / "dist"
previous = calculator / f"dist.bak.pre-51a88d9-{stamp}"
live.rename(previous)
staging.rename(live)
print(f"PREVIOUS_DIST={previous}")

html = output(["curl", "-fsS", PUBLIC_URL])
if "Калькулятор расчёта ИУ" not in html:
    raise SystemExit("Public page did not return the new release.")
asset_url = (
    "https://www.m4s.ru/"
    "%D0%9A%D0%B0%D0%BB%D1%8C%D0%BA%D1%83%D0%BB%D1%8F%D1%82%D0%BE%D1%80/assets/"
    + assets[0].name
)
run(["curl", "-fsS", "-o", "/dev/null", asset_url])
if output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT):
    raise SystemExit("Tracked production worktree became dirty.")
for service in ("albery", "albery-tg", "hermes-gateway", "nginx"):
    if output(["systemctl", "is-active", service]) != "active":
        raise SystemExit(f"Service is not active after deploy: {service}")

print("DEPLOYED_COMMIT=" + output(["git", "rev-parse", "HEAD"], cwd=ROOT))
print("DEPLOY_OK")
