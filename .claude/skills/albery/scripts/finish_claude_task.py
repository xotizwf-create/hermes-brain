#!/usr/bin/env python3
"""Написать результат в задачу Битрикса и закрыть её. Запускать НА 186.

    finish_claude_task.py <task_id> "<точное название задачи>" <файл_с_текстом> \
        --agent "Claude Code/<сессия>" [--comment-only]

`--comment-only` — только комментарий, без закрытия (промежуточный статус, уточняющий вопрос).

Перед записью проверяется замок из `claim_lock`: если задачу держит ДРУГОЙ агент, скрипт
отказывается писать. Так результат одного агента не затирает работу другого.

Почему так, а не «сырым» REST:
* инструменты MCP проверяют, что портал реально принял комментарий (вернул `comment_id`), —
  читатели комментариев на этом портале врут и показывают ноль для только что созданного;
* название сверяется с ожидаемым (`expected_title`) — защита от записи не в ту задачу;
* комментарии на портале НЕ удаляются и НЕ редактируются через REST. Текст пишем начисто,
  один раз, без «тестовых» прогонов на живой задаче.

Импорт `mcp.context_server` тянет за собой живые планировщики Albery, поэтому до импорта
выключаем оффер («могу помочь») и обход по чек-ину — иначе фоновый скрипт начнёт писать
живым сотрудникам.
"""
from __future__ import annotations

import os
import sys

os.environ["B24_TASK_OFFER"] = "0"
os.environ["B24_TASK_CHECKIN"] = "0"
sys.path.insert(0, "/var/www/albery")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claim_lock as lock  # noqa: E402

AGENT_USER_ID = 22  # «ИИ Агент» — от его имени пишутся инженерные результаты


def main() -> int:
    argv = sys.argv[1:]
    comment_only = "--comment-only" in argv
    me = argv[argv.index("--agent") + 1] if "--agent" in argv else None
    args = [a for a in argv if a != "--comment-only"]
    if "--agent" in args:
        i = args.index("--agent")
        del args[i:i + 2]
    if len(args) < 3:
        sys.exit('usage: finish_claude_task.py <task_id> "<название>" <файл> --agent "<имя/сессия>" [--comment-only]')

    task_id, expected_title, text_path = int(args[0]), args[1], args[2]
    with open(text_path, encoding="utf-8") as fh:
        result_text = fh.read().strip()
    if not result_text:
        sys.exit("текст результата пуст")

    taken = lock.active_locks(lock.live_comments(task_id), me=me)
    if taken:
        sys.exit(f"задачу держит другой агент: {taken[0]['agent']} с {taken[0]['date']} — не пишу")

    from mcp import context_server as cs  # noqa: PLC0415 — только после кил-свитчей выше

    if comment_only:
        out = cs.tool_add_bitrix_task_comment({
            "bitrix_task_id": task_id,
            "comment_text": result_text,
            "author_bitrix_user_id": AGENT_USER_ID,
            "expected_title": expected_title,
        })
        print(f"комментарий добавлен, comment_id={out.get('comment_id')}")
        return 0

    out = cs.tool_complete_bitrix_task({
        "bitrix_task_id": task_id,
        "on_behalf_bitrix_user_id": AGENT_USER_ID,
        "expected_title": expected_title,
        "result_text": result_text,
    })
    result = out.get("result") or {}
    comment_id = result.get("comment_id")
    print(f"закрыта={out.get('completed')} метод={out.get('method')} comment_id={comment_id}")
    if not comment_id:
        sys.exit("НЕТ comment_id — портал не подтвердил результат, задачу считать незакрытой")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
