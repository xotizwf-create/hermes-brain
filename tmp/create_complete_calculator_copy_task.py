import json
import os
import sys

os.environ["B24_TASK_OFFER"] = "0"
os.environ["B24_TASK_CHECKIN"] = "0"
sys.path.insert(0, "/var/www/albery")

from mcp import context_server

title = "Albery: усилить акцент результата публичного калькулятора ИУ"
description = """[b]Контекст[/b]
По обратной связи владельца итоговая страница калькулятора визуально смешивала введённые пользователем значения и рассчитанный результат. Верхняя подпись «Albery · Индивидуальные условия» также не соответствовала требуемому названию страницы.

[b]Что требуется[/b]
1. Вверху оставить название «Калькулятор расчёта ИУ».
2. Введённые значения обозначить заголовком «Введённые вами данные:».
3. Настоящий расчёт вынести ниже в отдельную выразительную продающую секцию.
4. Использовать заголовок «Расчёт готов!» и текст «При работе на ИУ вы получите…».
5. Проверить мобильную адаптацию, сборку и production.

[b]Критерий результата[/b]
На публичной странице введённые данные и расчёт визуально разделены; result-секция заметно выделена, новые тексты отображаются без наложений на мобильном экране; старой подписи Albery нет; production отдаёт новый HTML и JS с кодом 200."""

created = context_server.tool_create_bitrix_task(
    {
        "title": title,
        "description": description,
        "result_criteria": (
            "Новая продающая result-секция доступна на production, введённые данные "
            "отделены от рассчитанных значений, мобильная версия и тесты проверены."
        ),
        "responsible_bitrix_user_id": 16,
        "creator_bitrix_user_id": 22,
        "deadline": "2026-07-29T15:00:00+03:00",
        "priority": "high",
        "tags": ["Albery", "калькулятор", "UX", "production"],
        "checklist": [
            {"title": "Разделить введённые данные и результат", "complete": True},
            {"title": "Оформить продающую result-секцию", "complete": True},
            {"title": "Проверить mobile и production", "complete": True},
        ],
    }
)
task_id = int(created["task_id"])

result_text = """[b]Реализовано[/b]
• Верхняя подпись заменена на «Калькулятор расчёта ИУ».
• Над карточками исходных значений добавлен заголовок «Введённые вами данные:».
• Расчёт вынесен в отдельную контрастную секцию с золотым акцентом, знаком результата и текстами «Расчёт готов!» / «При работе на ИУ вы получите…».
• Акцентированы сумма к переводу и маржинальный доход; добавлен поясняющий продающий текст без изменения формул.

[b]Проверено[/b]
• Calculator: unit tests — 2 passed; TypeScript — успешно; Vite production build — успешно.
• Полный Albery predeploy: 1522 passed, 17 skipped.
• Мобильный экран 390 px проверен визуально: тексты и карточки не перекрываются.
• Production HTML — 200, новый JS asset — 200; новые тексты присутствуют, прежняя подпись удалена.
• albery, albery-tg, hermes-gateway и nginx — active; tracked worktree чистый; ошибок albery после выкладки нет.

[b]Версия и откат[/b]
Commit: 6eded8eef965e0f209ecf7b9f6825b6553e5e583
GitHub: https://github.com/xotizwf-create/Albery/commit/6eded8eef965e0f209ecf7b9f6825b6553e5e583
Backup: /var/backups/albery/code/pre-calculator-copy-20260729_141515
Быстрый откат: восстановить calculator/dist из backup или переименовать сохранённый dist.bak.pre-6eded8e-20260729_141515 обратно в dist; код откатить через git revert 6eded8e."""

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
