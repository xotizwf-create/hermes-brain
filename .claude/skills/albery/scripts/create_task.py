#!/usr/bin/env python3
"""Поставить задачу в очередь Claude (тег #Claude). Запускать НА 186.

    create_task.py <файл_с_задачей>

Файл: первая строка — название, дальше пустая строка и описание. Последняя строка описания
может быть «Критерий результата: …» — портал показывает его как критерий.

Задача создаётся на владельца (ответственный 16) от имени «ИИ Агент» (22) с тегом #Claude,
то есть сразу попадает в очередь `/албери`. Так оформляются задачи, о которых владелец
попросил в переписке: они живут в Битриксе, а не в чате.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claim_lock as lock  # noqa: E402

OWNER_ID = 16
AGENT_ID = 22
QUEUE_TAG = "#Claude"
PORTAL_TZ = timezone(timedelta(hours=4))  # портал отдаёт и принимает сроки в +04:00


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: create_task.py <файл_с_задачей>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        text = fh.read().strip()
    title, _, description = text.partition("\n")
    title, description = title.strip(), description.strip()
    if not title or not description:
        sys.exit("нужны название (первая строка) и описание (остальное)")

    deadline = datetime.now(PORTAL_TZ).replace(hour=19, minute=0, second=0, microsecond=0)
    if deadline < datetime.now(PORTAL_TZ):
        deadline += timedelta(days=1)

    created = lock.call("tasks.task.add", {"fields": {
        "TITLE": title,
        "DESCRIPTION": description,
        "RESPONSIBLE_ID": OWNER_ID,
        "CREATED_BY": AGENT_ID,
        "TAGS": [QUEUE_TAG],
        "DEADLINE": deadline.isoformat(),
    }})
    task = (created.get("result") or {}).get("task") or {}
    task_id = task.get("id")
    if not task_id:
        sys.exit(f"портал не создал задачу: {str(created)[:300]}")
    print(f"создана задача #{task_id}: {title}")
    print(f"https://albery.bitrix24.ru/company/personal/user/{OWNER_ID}/tasks/task/view/{task_id}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
