import json
import os
import sys

os.environ["B24_TASK_OFFER"] = "0"
os.environ["B24_TASK_CHECKIN"] = "0"
sys.path.insert(0, "/var/www/albery")

from mcp import context_server

title = "Albery: уточнить CTA подключения к ИУ в калькуляторе"
description = """[b]Контекст[/b]
По обратной связи владельца требуется заменить подпись итоговой Telegram-кнопки «Обсудить индивидуальные условия» на более точную «Обсудить подключение к ИУ».

[b]Что требуется[/b]
Изменить только видимый текст кнопки. Telegram URL, предзаполненное сообщение, дизайн, формулы и остальную логику не менять.

[b]Критерий результата[/b]
В production-бандле и на публичном калькуляторе присутствует новая подпись; старая отсутствует; HTML и JS возвращают 200; сервисы активны."""

created = context_server.tool_create_bitrix_task(
    {
        "title": title,
        "description": description,
        "result_criteria": (
            "Кнопка результата подписана «Обсудить подключение к ИУ», "
            "остальные параметры калькулятора не изменены."
        ),
        "responsible_bitrix_user_id": 16,
        "creator_bitrix_user_id": 22,
        "deadline": "2026-07-29T16:15:00+03:00",
        "priority": "normal",
        "tags": ["Albery", "калькулятор", "copy", "production"],
        "checklist": [
            {"title": "Заменить подпись CTA", "complete": True},
            {"title": "Проверить production bundle", "complete": True},
        ],
    }
)
task_id = int(created["task_id"])

result_text = """[b]Реализовано[/b]
• Подпись Telegram CTA заменена на «Обсудить подключение к ИУ».
• URL, предзаполненное сообщение, дизайн и формулы не менялись.

[b]Проверено[/b]
• Calculator unit tests, TypeScript и production build — успешно.
• Полный Albery predeploy: 1551 passed, 17 skipped.
• Production page — 200; JS asset — 200.
• Новая подпись присутствует в production-бандле; старая отсутствует.
• albery, albery-tg, hermes-gateway и nginx — active.

[b]Версия и откат[/b]
Source commit: a88fce9a6f4b8d2359777f31b4170de3ff7b3e23
Backup статического бандла: /var/backups/albery/code/pre-calculator-cta-20260729_154504
Быстрый откат: восстановить calculator/dist из указанного backup или вернуть dist.bak.pre-cta-20260729_154504."""

completed = context_server.tool_complete_bitrix_task(
    {
        "bitrix_task_id": task_id,
        "expected_title": title,
        "on_behalf_bitrix_user_id": 16,
        "result_text": result_text,
    }
)

comment_id = None
if isinstance(completed.get("result"), dict):
    comment_id = completed["result"].get("comment_id")
print(
    json.dumps(
        {
            "task_id": task_id,
            "completed": completed.get("completed") is True,
            "comment_id": comment_id,
        },
        ensure_ascii=False,
    )
)
