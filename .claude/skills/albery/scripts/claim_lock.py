#!/usr/bin/env python3
"""Общая механика «задача занята» для агентов, работающих с очередью Albery.

Замок живёт в комментариях самой задачи — единственном месте, которое видят ВСЕ агенты
и все люди сразу. Комментарии на этом портале нельзя ни удалить, ни отредактировать через
REST, поэтому замок не снимается стиранием: снятие — это отдельный комментарий-освобождение.
Состояние агента = его последняя метка (взял → занята, освободил → свободна).

Метки (строго эти префиксы, по ним же читают люди):
    🔒 ВЗЯЛ В РАБОТУ: <агент> · <время МСК>
    🔓 ОСВОБОДИЛ ЗАДАЧУ: <агент> · <время МСК> · причина: <...>

Кто такой <агент> — свободная строка вида «Claude Code/7998167a»: имя инструмента и
идентификатор сессии, чтобы два экземпляра одного инструмента не считали себя одним.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

ENV_PATH = "/var/www/albery/.env"
CLAIM_PREFIX = "🔒 ВЗЯЛ В РАБОТУ:"
RELEASE_PREFIX = "🔓 ОСВОБОДИЛ ЗАДАЧУ:"
# Чужие агенты могут писать по-человечески, без наших префиксов — это тоже считаем захватом.
FREEFORM_CLAIM = re.compile(r"(взял|беру|взяла|забрал)\s+(эту\s+)?задачу\s+в\s+работу", re.I)
MSK = timezone(timedelta(hours=3))
STALE_HOURS = 4  # старше — замок подозрительный, но САМ не снимается (см. skill)


def webhook_base() -> str:
    base = ""
    with open(ENV_PATH, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("BITRIX_WEBHOOK_BASE="):
                base = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not base:
        sys.exit("BITRIX_WEBHOOK_BASE не найден в .env")
    return base if base.endswith("/") else base + "/"


def call(method: str, payload: dict) -> dict:
    req = urllib.request.Request(
        webhook_base() + method, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def live_comments(task_id: int) -> list[dict]:
    """Комментарии задачи = сообщения её IM-чата. `task.commentitem.getlist` на этом портале
    отдаёт ложный ноль для только что созданного комментария, поэтому читаем чат напрямую."""
    task = (call("tasks.task.get", {"taskId": int(task_id),
                                    "select": ["ID", "CHAT_ID"]}).get("result") or {}).get("task") or {}
    chat_id = task.get("chatId") or task.get("CHAT_ID")
    if not chat_id:
        return []
    msgs = call("im.dialog.messages.get", {"DIALOG_ID": f"chat{chat_id}", "LIMIT": 100})
    items = (msgs.get("result") or {}).get("messages")
    if not isinstance(items, list):
        return []
    return sorted(items, key=lambda m: int(m.get("id") or 0))


def _agent_of(text: str, prefix: str) -> str:
    tail = text.split(prefix, 1)[1].strip()
    return tail.split("·")[0].strip().strip("[]b/") or "(без имени)"


def parse_locks(comments: list[dict]) -> dict[str, dict]:
    """Последняя метка каждого агента. Ключ — имя агента, значение — событие."""
    state: dict[str, dict] = {}
    for msg in comments:
        text = (msg.get("text") or "").replace("[b]", "").replace("[/b]", "")
        mid, date = int(msg.get("id") or 0), msg.get("date")
        if CLAIM_PREFIX in text:
            agent = _agent_of(text, CLAIM_PREFIX)
            state[agent] = {"agent": agent, "held": True, "id": mid, "date": date}
        elif RELEASE_PREFIX in text:
            agent = _agent_of(text, RELEASE_PREFIX)
            state[agent] = {"agent": agent, "held": False, "id": mid, "date": date}
        elif FREEFORM_CLAIM.search(text):
            # Формат не наш — агента опознаём по автору комментария, замок всё равно уважаем.
            agent = f"пользователь {msg.get('author_id')} (свободная форма)"
            state.setdefault(agent, {"agent": agent, "held": True, "id": mid, "date": date})
    return state


def active_locks(comments: list[dict], me: str | None = None) -> list[dict]:
    """Действующие захваты, кроме моего, — от самого раннего к позднему."""
    return sorted((ev for agent, ev in parse_locks(comments).items()
                   if ev["held"] and agent != me), key=lambda e: e["id"])


def my_lock(comments: list[dict], me: str) -> dict | None:
    ev = parse_locks(comments).get(me)
    return ev if ev and ev["held"] else None


def is_stale(event: dict) -> bool:
    try:
        taken = datetime.fromisoformat(str(event.get("date")))
    except (TypeError, ValueError):
        return False
    return datetime.now(MSK) - taken > timedelta(hours=STALE_HOURS)


def now_msk() -> str:
    return datetime.now(MSK).strftime("%d.%m.%Y %H:%M МСК")


def claim_text(agent: str) -> str:
    return (f"[b]{CLAIM_PREFIX}[/b] {agent} · {now_msk()}\n"
            "Задача занята: другим агентам её не брать, пока не появится метка об освобождении "
            "или результат.")


def release_text(agent: str, reason: str) -> str:
    return f"[b]{RELEASE_PREFIX}[/b] {agent} · {now_msk()} · причина: {reason}"
