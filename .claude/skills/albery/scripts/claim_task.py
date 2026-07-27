#!/usr/bin/env python3
"""Взять задачу в работу (или освободить её). Запускать НА 186.

    claim_task.py <task_id> "<точное название>" --agent "Claude Code/7998167a"
    claim_task.py <task_id> "<точное название>" --agent "..." --release "причина"

Коды возврата: 0 — задача моя, работать можно; 2 — задача занята другим агентом, взять
следующую свободную; 1 — ошибка.

Защита от гонки (два агента нажали одновременно): после записи метки скрипт перечитывает
ленту и сравнивает все действующие захваты. Побеждает самый ранний комментарий — id
сообщений в чате задачи монотонно растут. Проигравший сам пишет освобождение и уходит.
Это дешевле и надёжнее любых внешних локов: замок виден людям в той же ленте.
"""
from __future__ import annotations

import os
import sys
import time

os.environ["B24_TASK_OFFER"] = "0"
os.environ["B24_TASK_CHECKIN"] = "0"
sys.path.insert(0, "/var/www/albery")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claim_lock as lock  # noqa: E402

AGENT_USER_ID = 22  # «ИИ Агент» — от его имени пишут все наши агенты
STATUS_IN_PROGRESS = 3
SETTLE_SECONDS = 6  # пауза перед перечитыванием ленты — переживает гонку двух агентов


def post(task_id: int, expected_title: str, text: str) -> int:
    from mcp import context_server as cs  # noqa: PLC0415 — только после кил-свитчей выше

    out = cs.tool_add_bitrix_task_comment({
        "bitrix_task_id": task_id,
        "comment_text": text,
        "author_bitrix_user_id": AGENT_USER_ID,
        "expected_title": expected_title,
    })
    comment_id = out.get("comment_id")
    if not comment_id:
        sys.exit("портал не подтвердил комментарий (нет comment_id)")
    return comment_id


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) < 2 or "--agent" not in argv:
        sys.exit('usage: claim_task.py <task_id> "<название>" --agent "<имя/сессия>" [--release "причина"]')
    task_id, expected_title = int(argv[0]), argv[1]
    me = argv[argv.index("--agent") + 1]
    reason = argv[argv.index("--release") + 1] if "--release" in argv else None

    comments = lock.live_comments(task_id)

    if reason is not None:
        post(task_id, expected_title, lock.release_text(me, reason))
        print(f"ОСВОБОЖДЕНА #{task_id} · {me} · причина: {reason}")
        return 0

    # 1. Уже занята кем-то другим — не трогаем, идём к следующей.
    taken = lock.active_locks(comments, me=me)
    if taken:
        holder = taken[0]
        stale = " (замок старше 4 ч — сообщить владельцу, самому НЕ перехватывать)" if lock.is_stale(holder) else ""
        print(f"ЗАНЯТА #{task_id} · держит: {holder['agent']} · с {holder['date']}{stale}")
        return 2

    # 2. Уже моя с прошлого захода — просто продолжаем.
    if lock.my_lock(comments, me):
        print(f"МОЯ #{task_id} · {me} · замок уже стоял, продолжаю работу")
        return 0

    # 3. Ставим замок и проверяем, что гонку выиграли мы.
    post(task_id, expected_title, lock.claim_text(me))
    time.sleep(SETTLE_SECONDS)
    fresh = lock.live_comments(task_id)
    holders = sorted((ev for ev in lock.parse_locks(fresh).values() if ev["held"]),
                     key=lambda e: e["id"])
    if not holders:
        sys.exit("метку записали, но в ленте её нет — разобраться вручную, задачу не начинать")
    winner = holders[0]
    if winner["agent"] != me:
        post(task_id, expected_title,
             lock.release_text(me, f"уступаю, задачу раньше взял {winner['agent']}"))
        print(f"ЗАНЯТА #{task_id} · гонку выиграл {winner['agent']} · я уступил")
        return 2

    lock.call("tasks.task.update", {"taskId": task_id,
                                    "fields": {"STATUS": STATUS_IN_PROGRESS,
                                               "STATUS_CHANGED_BY": AGENT_USER_ID}})
    print(f"ВЗЯТА #{task_id} · {me} · статус переведён в «выполняется»")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
