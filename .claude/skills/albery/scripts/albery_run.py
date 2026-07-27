#!/usr/bin/env python3
"""Запуск команд и скриптов на серверах владельца — единая точка входа для скилла `albery`.

Маршрут до Albery ровно такой, как предписывает `projects/albery/servers.md`:
ПК → 217.198.12.236 (пароль из gitignored `Albery/.env`) → пароль Albery из сейфа на 217
(`/opt/hermes/secure/projects/albery/.env`) во временный файл 600 → `sshpass -f` → 186.246.7.32.
Пароль Albery не попадает ни на этот компьютер, ни в argv, ни в `ps`, и стирается после запуска.

    python albery_run.py exec   albery "systemctl is-active albery"
    python albery_run.py exec   main   "uptime"
    python albery_run.py script albery ./list_claude_tasks.py --tag Claude
    python albery_run.py put    albery ./result_2204.txt

`script` заливает в `/root/claude_tasks/` на цели ВСЕ `.py` из папки запускаемого скрипта
(скрипты делят общий модуль `claim_lock.py`) и выполняет указанный питоном проекта
(`/var/www/albery/.venv/bin/python` на 186, системным `python3` на 217).
`put` только заливает файл туда же — так текст результата попадает на сервер без мучений
с кавычками и без потери переносов строк.
"""
from __future__ import annotations

import base64
import shlex
import sys
from pathlib import Path

import paramiko

# .env самого Albery-репозитория: IP/USER/PASSWORD от 217 (шлюз).
ENV_FILE = Path(__file__).resolve().parents[5] / "Albery" / ".env"

ALBERY_HOST = "186.246.7.32"
VAULT_ENV = "/opt/hermes/secure/projects/albery/.env"
REMOTE_DIR = "/root/claude_tasks"
PY = {"albery": "/var/www/albery/.venv/bin/python", "main": "python3"}


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        sys.exit(f"нет файла с доступом к шлюзу: {ENV_FILE}")
    env: dict[str, str] = {}
    for raw in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def wrap_for_albery(command: str) -> str:
    """Обёртка: 217 выполняет команду на 186, пароль живёт только в mode-600 temp-файле."""
    payload = base64.b64encode(command.encode("utf-8")).decode("ascii")
    return (
        'PW=$(mktemp); chmod 600 "$PW"; '
        f'grep "^PASSWORD=" {VAULT_ENV} | cut -d= -f2- > "$PW"; '
        f"echo {payload} | base64 -d | "
        f'sshpass -f "$PW" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 '
        f"root@{ALBERY_HOST} bash -s; "
        'rc=$?; shred -u "$PW" 2>/dev/null || rm -f "$PW"; exit $rc'
    )


def run(target: str, command: str) -> int:
    env = load_env()
    host, user, password = env.get("IP"), env.get("USER", "root"), env.get("PASSWORD")
    if not host or not password:
        sys.exit(f"IP / PASSWORD не заданы в {ENV_FILE.name}")

    remote = wrap_for_albery(command) if target == "albery" else command
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password, timeout=30)
        _, stdout, stderr = client.exec_command(remote, timeout=900)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
    except Exception as exc:  # noqa: BLE001 — показать сбой, не раскрывая доступы
        sys.exit(f"не выполнилось на {target}: {type(exc).__name__}: {exc}")
    finally:
        client.close()
    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return code


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) < 3 or argv[0] not in ("exec", "script", "put") or argv[1] not in ("albery", "main"):
        sys.exit('usage: albery_run.py exec|script|put <albery|main> "<команда>" | <файл> [аргументы]')

    mode, target = argv[0], argv[1]
    if mode == "exec":
        return run(target, argv[2])

    local = Path(argv[2])
    if not local.is_file():
        sys.exit(f"нет такого файла: {local}")

    def upload_cmd(path: Path) -> str:
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"echo {payload} | base64 -d > {REMOTE_DIR}/{path.name}"

    remote_path = f"{REMOTE_DIR}/{local.name}"
    if mode == "put":
        return run(target, f"mkdir -p {REMOTE_DIR} && {upload_cmd(local)} && "
                           f"echo uploaded: {remote_path}")

    # Скрипты очереди делят общий модуль, поэтому едет вся папка целиком.
    steps = [f"mkdir -p {REMOTE_DIR}"] + [upload_cmd(p) for p in sorted(local.parent.glob("*.py"))]
    extra = " ".join(shlex.quote(a) for a in argv[3:])
    command = " && ".join(steps) + f" && cd /var/www/albery 2>/dev/null; {PY[target]} {remote_path} {extra}"
    return run(target, command)


if __name__ == "__main__":
    raise SystemExit(main())
