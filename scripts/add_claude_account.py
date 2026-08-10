#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add_claude_account.py — подключить ещё один аккаунт Claude Code к обновлению окна лимитов на 217.

Токен добывает владелец у себя на ПК:

    claude setup-token        # откроется браузер; войти НУЖНЫМ аккаунтом

Затем:

    python scripts/add_claude_account.py <имя-аккаунта>

Токен вводится в скрытом приглашении (не печатается, не попадает в историю шелла,
не передаётся аргументом). Скрипт кладёт его на 217 в защищённую зону
/root/.hermes/secure/claude_code/accounts/<имя>/oauth_token (600) и сразу проверяет
живым минимальным запросом. Дальше аккаунт подхватывает claude_limit_refresh.sh
(06:00/11:00/16:00 МСК) — правки в cron не нужны.

Реквизиты сервера читаются из некоммитимого .env репозитория (IP/USER/PASSWORD),
как в run_on_217.py. Значений здесь нет — только ссылка на файл.
"""
import io
import json
import os
import posixpath
import re
import sys
from getpass import getpass

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ENV = os.path.join(REPO, ".env")
ACCOUNTS_DIR = "/root/.hermes/secure/claude_code/accounts"


def creds(path):
    host = user = pwd = None
    with io.open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("IP="):
                host = line.split("=", 1)[1].strip()
            elif line.startswith("USER="):
                user = line.split("=", 1)[1].strip()
            elif line.startswith("PASSWORD="):
                pwd = line.split("=", 1)[1].strip()
    if not (host and user and pwd):
        sys.exit(f"add_claude_account: в {path} нет IP/USER/PASSWORD")
    return host, user, pwd


def run(client, cmd, timeout=180):
    _, out, err = client.exec_command(cmd, timeout=timeout)
    stdout = out.read().decode("utf-8", "replace")
    stderr = err.read().decode("utf-8", "replace")
    return out.channel.recv_exit_status(), stdout, stderr


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug = sys.argv[1].strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,40}", slug):
        sys.exit("Имя аккаунта: латиница/цифры/._- , до 41 символа (например: xotizwf).")

    token = getpass(f"Long-lived токен Claude Code для «{slug}» (ввод скрыт): ").strip()
    if not token:
        sys.exit("Пустой ввод — ничего не делаю.")
    if any(c.isspace() for c in token):
        sys.exit("В токене пробелы/переводы строк — скопирован лишний текст. Повтори.")
    if len(token) < 20:
        sys.exit("Слишком короткая строка для токена — похоже, скопировалось не то.")

    host, user, pwd = creds(os.environ.get("HERMES_SSH_ENV", DEFAULT_ENV))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=pwd, timeout=30)

    try:
        acc_dir = posixpath.join(ACCOUNTS_DIR, slug)
        target = posixpath.join(acc_dir, "oauth_token")

        rc, _, err = run(client, f"install -d -m 700 {acc_dir}")
        if rc != 0:
            sys.exit(f"Не создалась папка аккаунта: {err.strip()}")

        # Токен пишем через SFTP: так он не попадает ни в командную строку, ни в логи sshd.
        sftp = client.open_sftp()
        with sftp.open(target, "wb") as fh:
            fh.write((token + "\n").encode("utf-8"))
        sftp.chmod(target, 0o600)
        sftp.close()
        print(f"Токен записан: {target} (600)")

        print("Проверяю живым запросом…")
        rc, out, err = run(
            client,
            "export HOME=/root/claude-accounts/{slug}; install -d -m 700 $HOME; "
            "CLAUDE_CODE_OAUTH_TOKEN=$(cat {target}) "
            "timeout 90s claude -p --model claude-haiku-4-5 --output-format json 'OK' "
            "< /dev/null".format(slug=slug, target=target),
            timeout=200,
        )
        verdict = {}
        try:
            data = json.loads(out.strip().splitlines()[-1])
            verdict = {k: data.get(k) for k in ("is_error", "api_error_status", "result")}
        except Exception:
            verdict = {"raw": (out or err).strip()[:300]}

        if rc == 0 and verdict.get("is_error") is False:
            print("OK — аккаунт отвечает, окно лимитов будет обновляться в 06:00/11:00/16:00 МСК.")
        else:
            print(f"НЕ ПРОШЛО (код {rc}): {verdict}")
            print("Токен оставлен на месте — при желании удалить: "
                  f"ssh → rm -rf {acc_dir}")
            sys.exit(1)

        print("\nКонтрольный прогон всего задания (как его зовёт cron):")
        rc, out, err = run(client, "/root/.hermes/scripts/claude_limit_refresh.sh", timeout=300)
        print(out.strip() or "(тишина — все аккаунты обновились)")
        if err.strip():
            print("--- stderr ---\n" + err.strip())
        print(f"код возврата: {rc} (0 = все аккаунты живы; N = столько аккаунтов не обновилось)")
    finally:
        client.close()


if __name__ == "__main__":
    main()
