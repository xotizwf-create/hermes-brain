#!/usr/bin/env python3
"""Очередь задач для Claude: задачи Битрикса с тегом Claude, ещё не закрытые.

Только чтение — ничего не меняет на портале. Запускать НА 186 (`/var/www/albery/.venv/bin/python`),
webhook берётся из `/var/www/albery/.env`.

По каждой задаче печатается номер, автор, ответственный, дедлайн, полное описание, лента
комментариев и — главное для командной работы — СОСТОЯНИЕ ЗАМКА: свободна, занята другим
агентом или уже моя.

Тег сверяется по содержанию: «Claude», «#Claude», «claude-code» — всё это очередь.

Usage: list_claude_tasks.py [--tag claude] [--all] [--agent "Claude Code/<сессия>"]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claim_lock as lock  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    tag = args[args.index("--tag") + 1] if "--tag" in args else lock.QUEUE_TAG_WORD
    me = args[args.index("--agent") + 1] if "--agent" in args else None
    include_closed = "--all" in args

    tasks = lock.find_queue_tasks(tag, include_closed=include_closed)

    print(f"ЗАДАЧИ С ТЕГОМ «{tag}» (любое написание): {len(tasks)}"
          f"{'' if include_closed else ' (открытых)'}\n")
    free = []
    for t in tasks:
        tid = int(t["id"])
        comments = lock.live_comments(tid)
        taken = lock.active_locks(comments, me=me)
        mine = lock.my_lock(comments, me) if me else None

        if taken:
            holder = taken[0]
            stale = " · ЗАМОК СТАРШЕ 4 Ч — не перехватывать, сообщить владельцу" if lock.is_stale(holder) else ""
            state = f"ЗАНЯТА — держит {holder['agent']} с {holder['date']}{stale}"
        elif mine:
            state = f"МОЯ — замок стоит с {mine['date']}"
            free.append(tid)
        else:
            state = "СВОБОДНА — можно брать"
            free.append(tid)

        print("=" * 78)
        print(f"ЗАДАЧА #{tid}: {t.get('title')}")
        print(f"СОСТОЯНИЕ: {state} · теги: {lock.tag_titles(t)}")
        print(f"постановщик={t.get('createdBy')} ответственный={t.get('responsibleId')} "
              f"статус={t.get('status')} дедлайн={t.get('deadline')} создана={t.get('createdDate')}")
        print(f"ссылка: https://albery.bitrix24.ru/company/personal/user/"
              f"{t.get('responsibleId')}/tasks/task/view/{tid}/")
        print("--- описание ---")
        print((t.get("description") or "").strip() or "(пусто)")
        if comments:
            print(f"--- комментарии ({len(comments)}) ---")
            for c in comments[-20:]:
                text = (c.get("text") or "").replace("\n", " ")[:300]
                print(f"  [{c.get('author_id')}] {c.get('date')}: {text}")
        print()

    print(f"СВОБОДНЫ ДЛЯ РАБОТЫ: {', '.join('#' + str(i) for i in free) if free else '(нет)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
