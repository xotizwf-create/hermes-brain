#!/usr/bin/env python3
"""Run a command on one of the owner's servers.

Two targets:

    main   -> 217.198.12.236 (andigital / Hermes Brain). Direct SSH; credentials come from
              the Albery repo's gitignored `.env` (IP / USER / PASSWORD).

    albery -> 186.246.7.32 (Albery production). Reached **through** 217, exactly as
              `projects/albery/servers.md` prescribes: the password is read from the secure
              vault on 217 (`/opt/hermes/secure/projects/albery/.env`) into a mode-600 temp
              file, used via `sshpass -f`, then shredded. It never reaches this machine and
              never appears in argv or `ps`.

The command is base64-encoded and fed to the remote `bash -s` over stdin, so quoting never
mangles it.

Usage:
    python tmp/server.py main   "uptime; free -m"
    python tmp/server.py albery "systemctl is-active albery"

NOTE: local stand-in for `_deploy_helper.py` from the "Сайт мой" repo, which is not checked
out here. Lives in tmp/ (gitignored) per the repo-hygiene rule; promote it to scripts/ only
with the owner's approval.
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

import paramiko

ENV_FILE = Path(__file__).resolve().parents[2] / "Albery" / ".env"

ALBERY_HOST = "186.246.7.32"
VAULT_ENV = "/opt/hermes/secure/projects/albery/.env"


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        sys.exit(f"missing {ENV_FILE}")
    env: dict[str, str] = {}
    for raw in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def wrap_for_albery(command: str) -> str:
    """Wrap a command so 217 runs it on 186 without the password touching argv."""
    payload = base64.b64encode(command.encode("utf-8")).decode("ascii")
    return (
        'PW=$(mktemp); chmod 600 "$PW"; '
        f'grep "^PASSWORD=" {VAULT_ENV} | cut -d= -f2- > "$PW"; '
        f"echo {payload} | base64 -d | "
        f'sshpass -f "$PW" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 '
        f"root@{ALBERY_HOST} bash -s; "
        'rc=$?; shred -u "$PW" 2>/dev/null || rm -f "$PW"; exit $rc'
    )


def main() -> int:
    if len(sys.argv) < 3:
        sys.exit('usage: python tmp/server.py <main|albery> "<command>"')

    target, command = sys.argv[1], sys.argv[2]
    if target not in ("main", "albery"):
        sys.exit(f"unknown target {target!r} — known: main, albery")

    env = load_env()
    host, user, password = env.get("IP"), env.get("USER", "root"), env.get("PASSWORD")
    if not host or not password:
        sys.exit(f"IP / PASSWORD not set in {ENV_FILE.name}")

    remote = wrap_for_albery(command) if target == "albery" else command

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password, timeout=30)
        _, stdout, stderr = client.exec_command(remote, timeout=600)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
    except Exception as exc:  # noqa: BLE001 - surface the failure without leaking creds
        sys.exit(f"failed on {target}: {type(exc).__name__}: {exc}")
    finally:
        client.close()

    if out:
        print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
