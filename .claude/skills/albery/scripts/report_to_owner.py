#!/usr/bin/env python3
"""Мини-отчёт владельцу в Telegram (чат Hermes Brain). Запускать НА 217.

    report_to_owner.py <файл_с_текстом>

Токен бота Hermes берётся из `/root/.hermes/.env`, чат — из `telegram.allowed_chats`
в `/root/.hermes/config.yaml`. Ни то, ни другое не печатается. Длинный текст режется
на куски по 3500 символов — Telegram отвергает сообщения длиннее 4096.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request

ENV_PATH = "/root/.hermes/.env"
CONFIG_PATH = "/root/.hermes/config.yaml"
CHUNK = 3500


def token() -> str:
    with open(ENV_PATH, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"(?:export\s+)?TELEGRAM[A-Z_]*TOKEN\s*=\s*(.+)", line.strip())
            if m:
                return m.group(1).strip().strip('"').strip("'")
    sys.exit("токен Telegram не найден")


def chat() -> str:
    import yaml  # noqa: PLC0415 — есть только в окружении Hermes на 217

    with open(CONFIG_PATH, encoding="utf-8") as fh:
        allowed = yaml.safe_load(fh)["telegram"]["allowed_chats"]
    if isinstance(allowed, (list, tuple)):
        allowed = allowed[0]
    return str(allowed)


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: report_to_owner.py <файл_с_текстом>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read().strip()
    if not text:
        sys.exit("текст отчёта пуст")

    tok, chat_id = token(), chat()
    for start in range(0, len(text), CHUNK):
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text[start:start + CHUNK],
            "disable_web_page_preview": "true",
        }).encode()
        resp = json.load(urllib.request.urlopen(
            f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=30))
        if not resp.get("ok"):
            sys.exit(f"Telegram отказал: {str(resp)[:200]}")
    print("отчёт отправлен")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
