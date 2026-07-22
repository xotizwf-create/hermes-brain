#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hermes_compaction_watchdog.py — ловит ЗАВИСАНИЕ агента, которое systemd не видит.

Инцидент 2026-07-22: gateway был `active (running)`, процесс жив, `Restart=always`
не срабатывал — но владелец не получал ответов ~35 минут. В журнале: `Session
compressed 32 times` подряд и `Compression summary failed: 413 ... Limit 12000 TPM`.
Причина: auxiliary.compression указывал на Groq (llama-3.3-70b-versatile, лимит
12k токенов/мин), а сжимать надо было ~93k токенов -> 413 на каждой попытке;
запасной codex не укладывался в 45 c. Сжатие не завершалось никогда, контекст не
уменьшался, каждый ход снова уходил в компакцию вместо ответа.

Почему отдельный сторож, а не hermes cron: задания hermes cron исполняет САМ
gateway — если он в петле, его собственные проверки висят вместе с ним. Этот
скрипт живёт в системном cron и шлёт сообщение напрямую через Bot API.

Проверки:
  1. сервис не active                 -> рестарт + алерт
  2. падения сжатия >= FAIL_LIMIT     -> алерт; при повторе подряд — рестарт
  3. компакций >= COMPACT_LIMIT       -> то же (петля без явных ошибок)
  4. auxiliary.compression снова смотрит на модель с малым лимитом токенов
                                      -> алерт (защита от возврата причины)

Тихий по умолчанию: если всё в порядке, не печатает и не шлёт ничего.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SERVICE = "hermes-gateway"
STATE_PATH = "/root/.hermes/state/compaction_watchdog.json"
TOKEN_PATH = "/root/.hermes/secure/claude_code/bot_token"
CONFIG_PATH = "/root/.hermes/config.yaml"
OWNER_CHAT = "1451982360"

FAIL_LIMIT = 3        # падений сжатия в окне -> тревога
COMPACT_LIMIT = 12    # компакций в окне -> тревога (петля без явных ошибок)
RESTART_COOLDOWN = 3600   # не перезапускать чаще раза в час
ALERT_COOLDOWN = 7200     # не повторять один и тот же алерт чаще раза в 2 часа

RE_FAIL = re.compile(
    r"Compression summary failed|Failed to generate context summary|"
    r"compression.*(413|too large|exceeded .*timeout)",
    re.I,
)
RE_COMPACT = re.compile(r"Compacting context|Session compressed \d+ times", re.I)
# провайдеры сжатия с лимитом токенов/мин, которых не хватает на реальный контекст
RE_SMALL_TPM = re.compile(r"api\.groq\.com|llama-3\.\d+-\d+b|gpt-oss-\d+b", re.I)


def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def service_started_at():
    """Момент последнего старта службы — строки до него уже не про текущий процесс."""
    try:
        out = subprocess.run(
            ["systemctl", "show", "-p", "ActiveEnterTimestampMonotonic", "--value", SERVICE],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        monotonic_us = int(out or 0)
        if monotonic_us <= 0:
            return 0
        with open("/proc/uptime", encoding="utf-8") as fh:
            uptime = float(fh.read().split()[0])
        return time.time() - uptime + monotonic_us / 1_000_000
    except Exception:
        return 0


def journal(minutes, journal_file=None):
    if journal_file:
        with open(journal_file, encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    # Окно начинается не раньше последнего старта службы: после перезапуска
    # старые строки петли не должны выглядеть как новая петля.
    since = max(time.time() - minutes * 60, service_started_at())
    try:
        out = subprocess.run(
            ["journalctl", "-u", SERVICE, "--since", "@" + str(int(since)), "--no-pager"],
            capture_output=True, text=True, timeout=60,
        ).stdout
        return out.splitlines()
    except Exception as exc:
        print(f"watchdog: журнал недоступен: {exc}", file=sys.stderr)
        return []


def service_active():
    try:
        out = subprocess.run(
            ["systemctl", "is-active", SERVICE], capture_output=True, text=True, timeout=30
        ).stdout.strip()
        return out == "active"
    except Exception:
        return True  # не смогли проверить — не паникуем


def compression_provider_line():
    """Вернуть строку с провайдером сжатия из конфига (для проверки регрессии)."""
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return ""
    try:
        aux = lines.index("auxiliary:")
        comp = next(i for i in range(aux + 1, len(lines)) if lines[i] == "  compression:")
    except (ValueError, StopIteration):
        return ""
    block = []
    for line in lines[comp + 1:]:
        if line.strip() and not line.startswith("    "):
            break
        block.append(line)
    return "\n".join(block)


def telegram(text, dry_run=False):
    if dry_run:
        print("[dry-run] в Telegram ушло бы:\n" + text)
        return True
    try:
        with open(TOKEN_PATH, encoding="utf-8") as fh:
            token = fh.read().strip()
    except OSError as exc:
        print(f"watchdog: нет токена бота: {exc}", file=sys.stderr)
        return False
    data = json.dumps({"chat_id": OWNER_CHAT, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data, headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 200
    except Exception as exc:
        print(f"watchdog: Telegram не принял сообщение: {exc}", file=sys.stderr)
        return False


def restart(dry_run=False):
    if dry_run:
        print("[dry-run] перезапустил бы hermes-gateway")
        return True
    try:
        subprocess.run(["systemctl", "restart", SERVICE], timeout=240, check=True)
        return True
    except Exception as exc:
        print(f"watchdog: рестарт не удался: {exc}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=15, help="окно журнала")
    ap.add_argument("--journal-file", help="читать журнал из файла (для тестов)")
    ap.add_argument("--dry-run", action="store_true", help="ничего не менять и не слать")
    ap.add_argument("--state", help="путь к файлу состояния (для тестов)")
    args = ap.parse_args()

    global STATE_PATH
    if args.state:
        STATE_PATH = args.state

    now = time.time()
    state = load_state()
    lines = journal(args.minutes, args.journal_file)

    fails = [l for l in lines if RE_FAIL.search(l)]
    compacts = [l for l in lines if RE_COMPACT.search(l)]
    dead = not service_active() if not args.journal_file else False

    storm = len(fails) >= FAIL_LIMIT or len(compacts) >= COMPACT_LIMIT
    prev_storm = bool(state.get("storm_seen"))
    problems, actions = [], []

    if dead:
        problems.append("Агент не запущен (служба не в состоянии active).")
        if now - state.get("last_restart", 0) > RESTART_COOLDOWN and restart(args.dry_run):
            state["last_restart"] = now
            actions.append("Перезапустил агента.")

    if storm:
        problems.append(
            f"Агент застрял в петле сжатия контекста: за {args.minutes} мин "
            f"{len(compacts)} компакций и {len(fails)} падений сжатия. "
            "В таком состоянии он не отвечает на сообщения, хотя формально «работает»."
        )
        if prev_storm and now - state.get("last_restart", 0) > RESTART_COOLDOWN:
            if restart(args.dry_run):
                state["last_restart"] = now
                actions.append("Перезапустил агента, чтобы разорвать петлю.")
        elif not prev_storm:
            actions.append("Слежу: если повторится на следующей проверке — перезапущу сам.")
    state["storm_seen"] = storm

    provider = compression_provider_line()
    if provider and RE_SMALL_TPM.search(provider):
        problems.append(
            "Сжатие контекста снова настроено на модель с маленьким лимитом "
            "токенов в минуту — именно это уронило агента 22.07.2026. "
            "Нужен провайдер основной модели (auxiliary.compression.provider: auto)."
        )

    if not problems:
        save_state(state)
        return 0

    key = "|".join(problems)[:200]
    if state.get("last_alert_key") == key and now - state.get("last_alert", 0) < ALERT_COOLDOWN:
        save_state(state)
        return 0

    text = "🔴 Сторож агента\n\n" + "\n\n".join(f"• {p}" for p in problems)
    if actions:
        text += "\n\nЧто сделано:\n" + "\n".join(f"— {a}" for a in actions)
    print(text)
    telegram(text, args.dry_run)
    state["last_alert"] = now
    state["last_alert_key"] = key
    save_state(state)
    return 1


if __name__ == "__main__":
    sys.exit(main())
