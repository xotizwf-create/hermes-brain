#!/usr/bin/env python3
"""WORKSTATION tool — push a project's .env straight into the server secure zone over SSH.

Run this on YOUR PC. It reads a local secrets file and uploads it directly to
/root/.hermes/secure/projects/<slug>/.env on the Hermes server over the encrypted SSH channel,
then asks the server helper to confirm by variable NAMES only. The secret NEVER goes through
Telegram and NEVER enters any LLM context — that is the whole point.

The local file stays where it is (your copy). Nothing secret is printed.

SSH connection facts (host/user/password or key) are read from a local env file — by default
c:\\hermes-brain\\.env (override with HERMES_SSH_ENV). That file is gitignored and never leaves the PC.

Usage:
  python secret_push.py <slug> <path-to-.env>
  python secret_push.py <slug> <path> --as-file <name>     # store under a custom filename
Examples:
  python secret_push.py myshop .\\.env
  python secret_push.py myshop C:\\proj\\.env.production
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import secrets as _secrets
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import paramiko
except ImportError:
    print("Нужен пакет paramiko: pip install paramiko")
    raise SystemExit(2)

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,48}[a-z0-9]$")
SERVER_HELPER = "/root/.hermes/agent-knowledge/skills/secure-access/scripts/save_project_secrets.py"


def load_ssh_env() -> dict:
    path = Path(os.environ.get("HERMES_SSH_ENV", r"c:\hermes-brain\.env"))
    if not path.exists():
        print(f"Не найден файл с доступом к серверу: {path}")
        raise SystemExit(2)
    cfg = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip()
    return cfg


def connect(cfg: dict) -> "paramiko.SSHClient":
    host = cfg.get("IP сервера агента") or cfg.get("HOST")
    user = cfg.get("Пользователь") or cfg.get("USER") or "root"
    pwd = cfg.get("Пароль") or cfg.get("PASSWORD")
    key = cfg.get("KEYFILE")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key:
        c.connect(host, username=user, key_filename=key, timeout=30)
    else:
        c.connect(host, username=user, password=pwd, timeout=30)
    return c


def main() -> int:
    p = argparse.ArgumentParser(prog="secret_push")
    p.add_argument("slug")
    p.add_argument("file")
    p.add_argument("--as-file", dest="as_file", default=".env",
                   help="filename inside the project secure dir (default .env)")
    a = p.parse_args()

    if not SLUG_RE.match(a.slug):
        print(f"Имя проекта «{a.slug}» не годится. Только латиница в нижнем регистре, цифры и дефис.")
        return 2
    local = Path(a.file)
    if not local.exists():
        print(f"Локальный файл не найден: {local}")
        return 2
    payload = local.read_bytes()
    if not payload.strip():
        print("Файл пустой — нечего отправлять.")
        return 2

    cfg = load_ssh_env()
    print(f"Подключаюсь к серверу и загружаю «{local.name}» в сейф проекта «{a.slug}»…")
    c = connect(cfg)
    sftp = c.open_sftp()
    # land in a transient file inside the secure store, then let the server helper move+lock+confirm
    staging = f"/root/.hermes/secure/.incoming_{a.slug}_{_secrets.token_hex(4)}"
    with sftp.open(staging, "wb") as fh:
        fh.write(payload)
    sftp.chmod(staging, 0o600)

    cmd = f"HERMES_SECURE_DIR=/root/.hermes/secure python3 {SERVER_HELPER} save-env {a.slug} --from {staging}"
    if a.as_file != ".env":
        # generic file: write directly to the project dir under the chosen name, 600
        target = f"/root/.hermes/secure/projects/{a.slug}/{a.as_file}"
        cmd = (f"mkdir -p -m700 /root/.hermes/secure/projects/{a.slug} && "
               f"mv {staging} {target} && chmod 600 {target} && "
               f"echo '✅ Файл «{a.as_file}» сохранён в сейф проекта «{a.slug}» (600). Значение не показываю.'")
    _i, o, e = c.exec_command(cmd, timeout=60)
    out = o.read().decode("utf-8", "replace"); err = e.read().decode("utf-8", "replace")
    rc = o.channel.recv_exit_status()
    # make sure no staging file is left behind on any path
    c.exec_command(f"rm -f {staging}")
    c.close()

    print(out.strip() or err.strip())
    if rc != 0:
        print("⚠️ Что-то пошло не так при сохранении на сервере.")
        return 1
    print("Готово. Секрет лежит только в сейфе на сервере — в чат и в ИИ он не попадал.")
    print(f"Дальше скажи Гермесу: «запиши память по проекту {a.slug}» — он заведёт карточку (без значений).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
