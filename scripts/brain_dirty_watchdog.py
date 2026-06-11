#!/usr/bin/env python3
"""Autonomous housekeeper for the Hermes Brain git clone on the server.

Behaviour (owner's standing approval, 2026-06-11 — «чтобы всё всегда было
закоммичено, добавлять агенту автономности»):

- clean tree → silently sync (ff-pull, push unpushed commits), no output;
- dirty tree → wait until the dirty state is STABLE for two consecutive runs
  (>= GRACE), so mid-work edits are never committed under someone's hands;
- stable + `scripts/validate.py` passes (frontmatter + secret scan) →
  auto-commit, rebase-pull, push, short Russian success note;
- validator FAILS (possible secret / broken doc) or push/rebase conflict →
  loud alert (throttled) — the only case that still needs a human.

Deployed at /root/.hermes/scripts/brain_dirty_watchdog.py, run by hermes cron
job `brain-dirty-watchdog` (no_agent, every 30m, delivery to Telegram; clean
runs print nothing so nothing is delivered).

Source of truth in git: hermes-brain scripts/brain_dirty_watchdog.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/root/.hermes/agent-knowledge")
STATE = Path("/root/.hermes/state/brain_dirty_watchdog.json")
THROTTLE_SECONDS = 6 * 60 * 60
GRACE_SECONDS = 25 * 60  # dirty state must survive ~one cron interval
DRY_RUN = os.environ.get("WATCHDOG_DRY_RUN") == "1"


def run_git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO), *args], text=True, stderr=subprocess.STDOUT
    )


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE)


def dirty_files(status: str) -> list[str]:
    files = []
    for line in status.splitlines():
        files.append(line[2:].strip() if len(line) >= 3 else line.strip())
    return files


def quiet_sync() -> None:
    """On a clean tree: pull fast-forward and push any unpushed commits."""
    try:
        run_git("fetch", "--quiet", "origin")
        run_git("pull", "--ff-only", "--quiet")
        ahead = run_git("rev-list", "--count", "@{u}..HEAD").strip()
        if ahead != "0":
            if DRY_RUN:
                print(f"[dry-run] would push {ahead} commit(s)")
            else:
                run_git("push", "--quiet")
    except Exception:
        pass  # network blips are not worth an owner notification


def validate() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "validate.py")],
        capture_output=True, text=True, cwd=str(REPO),
    )
    out = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, out


def alert(state: dict, digest: str, lines: list[str]) -> None:
    now = int(time.time())
    if state.get("alert_digest") == digest and now - int(state.get("last_alert_at", 0)) < THROTTLE_SECONDS:
        return
    state.update({"alert_digest": digest, "last_alert_at": now})
    save_state(state)
    print("\n".join(lines))


def main() -> int:
    try:
        status = run_git("status", "--porcelain").strip()
    except Exception as exc:
        print(f"⚠️ Не смог проверить базу знаний Hermes: {exc}")
        return 0

    state = load_state()
    now = int(time.time())

    if not status:
        quiet_sync()
        if state.get("digest"):
            save_state({"last_clean_at": now})
        return 0

    digest = hashlib.sha256(status.encode("utf-8")).hexdigest()
    files = dirty_files(status)

    # New / changed dirty state: start the grace clock, stay silent.
    if state.get("digest") != digest:
        state.update({"digest": digest, "first_seen_at": now})
        save_state(state)
        return 0

    if now - int(state.get("first_seen_at", now)) < GRACE_SECONDS:
        return 0

    # Stable dirty state → try to reconcile autonomously.
    ok, vout = validate()
    if not ok:
        alert(state, digest, [
            "⚠️ В базе знаний Hermes зависли изменения, и я НЕ могу закоммитить их сам:",
            "",
            *[f"— {f}" for f in files[:8]],
            *([f"— ещё {len(files) - 8} файл(ов)"] if len(files) > 8 else []),
            "",
            f"Валидатор не пропустил (возможен секрет или сломанный фронтматтер): {vout[-300:]}",
            "Посмотри глазами или скажи мне «разбери мозг» — починю под присмотром.",
        ])
        return 0

    if DRY_RUN:
        print(f"[dry-run] would auto-commit {len(files)} file(s): {', '.join(files[:8])}")
        return 0

    try:
        run_git("add", "-A")
        listing = ", ".join(files[:6]) + (f" и ещё {len(files) - 6}" if len(files) > 6 else "")
        run_git("commit", "-q", "-m",
                f"brain: автокоммит вотчдога — рабочие хвосты ({listing})")
        run_git("pull", "--rebase", "--quiet")
        run_git("push", "--quiet")
    except Exception as exc:
        alert(state, digest, [
            "⚠️ Автокоммит мозга не прошёл (конфликт или сеть):",
            f"{str(exc)[-300:]}",
            "Скажи «разбери мозг» — починю под присмотром.",
        ])
        return 0

    save_state({"last_autocommit_at": now})
    print("🧹 Навёл порядок в базе знаний: закоммитил и запушил "
          f"{len(files)} файл(ов) — {listing}. Валидатор и секрет-скан пройдены.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
