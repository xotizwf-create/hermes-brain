#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_on_217.py — запустить команду на сервере 217.198.12.236 с ПК владельца.

На ПК нет SSH-ключа, поэтому идём по паролю через paramiko. Реквизиты берутся из
локального, НЕ коммитимого .env (по умолчанию — .env репозитория Albery: IP/USER/PASSWORD)
и никогда не печатаются. Здесь лежит только ССЫЛКА на файл, значений нет.

    python scripts/run_on_217.py "hermes cron list" [timeout_sec]

Переопределение источника реквизитов: HERMES_SSH_ENV=<путь к .env>.
"""
import io
import os
import sys

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_ENV = os.path.expanduser(r"~\Новая папка\Albery\.env")


def creds(path):
    host = user = pwd = None
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            for key, name in (("IP=", "host"), ("USER=", "user"), ("PASSWORD=", "pwd")):
                if line.startswith(key):
                    value = line.split("=", 1)[1].strip()
                    if name == "host":
                        host = value
                    elif name == "user":
                        user = value
                    else:
                        pwd = value
    if not (host and user and pwd):
        sys.exit(f"run_on_217: в {path} нет IP/USER/PASSWORD")
    return host, user, pwd


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    env_path = os.environ.get("HERMES_SSH_ENV", DEFAULT_ENV)
    host, user, pwd = creds(env_path)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=pwd, timeout=30)
    try:
        _, out, err = client.exec_command(cmd, timeout=timeout)
        stdout = out.read().decode("utf-8", "replace")
        stderr = err.read().decode("utf-8", "replace")
        rc = out.channel.recv_exit_status()
        print(stdout)
        if stderr.strip():
            print("--- stderr ---")
            print(stderr)
        print(f"--- exit {rc} ---")
    finally:
        client.close()
    sys.exit(rc)


if __name__ == "__main__":
    main()
