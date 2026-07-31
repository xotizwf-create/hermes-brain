import json
import os
import sys

os.environ["B24_TASK_OFFER"] = "0"
os.environ["B24_TASK_CHECKIN"] = "0"
sys.path.insert(0, "/var/www/albery")

from mcp import context_server

title = "Albery: переработать калькулятор ИУ в светлом стиле формы"
description = """[b]Контекст[/b]
Владелец отклонил тёмно-золотое оформление калькулятора как слишком агрессивное и передал референс светлой формы Битрикс: узкая центрированная колонка, спокойные серые поля и голубая основная кнопка.

[b]Что требуется[/b]
1. Полностью убрать прежнюю тёмную тему, золото, свечения и пошаговый сценарий.
2. Показать все четыре параметра одновременно в удобной светлой форме.
3. Использовать мягкие серые поля, белый фон и единый голубой акцент.
4. Сохранить разделение введённых данных и результата, существующие формулы и Telegram CTA.
5. Проверить desktop/mobile, валидацию, сборку и production.

[b]Критерий результата[/b]
Публичный калькулятор визуально соответствует светлой подаче референса; все поля доступны на одном экране; результат появляется только после успешной валидации; старые маркеры темы отсутствуют; mobile и desktop не имеют наложений; production HTML и JS возвращают 200."""

created = context_server.tool_create_bitrix_task(
    {
        "title": title,
        "description": description,
        "result_criteria": (
            "Калькулятор полностью переведён на светлую форму в стиле референса, "
            "проверен на desktop/mobile и опубликован на production без изменения формул."
        ),
        "responsible_bitrix_user_id": 16,
        "creator_bitrix_user_id": 22,
        "deadline": "2026-07-29T15:15:00+03:00",
        "priority": "high",
        "tags": ["Albery", "калькулятор", "UX", "production"],
        "checklist": [
            {"title": "Полностью убрать тёмно-золотую тему", "complete": True},
            {"title": "Собрать светлую форму со всеми полями", "complete": True},
            {"title": "Переработать спокойный блок результата", "complete": True},
            {"title": "Проверить desktop, mobile и production", "complete": True},
        ],
    }
)
task_id = int(created["task_id"])

result_text = """[b]Реализовано[/b]
• Пошаговый тёмный экран заменён единой светлой формой: все четыре параметра видны одновременно.
• Убраны чёрный фон, золото, свечение и тёмная browser theme; фон и scrollbar переведены в light mode.
• Поля оформлены как в референсе Битрикс: светло-серые поверхности, компактные подписи, значения внутри поля и голубой focus.
• Результат появляется только после нажатия «Рассчитать» и успешной валидации.
• Введённые данные, расчёт, две ключевые суммы и Telegram CTA сохранены в спокойной бело-голубой подаче.
• Формулы не изменялись; после изменения любого поля старый результат скрывается до нового расчёта.

[b]Проверено[/b]
• Calculator unit tests — 2 passed; TypeScript — успешно; production build — успешно.
• Полный Albery predeploy: 1522 passed, 17 skipped.
• Визуально проверены 390×844 и 1440×1000: четыре поля, форма и результат без перекрытий.
• Production HTML — 200; новый JS asset — 200; theme-color #ffffff.
• В production-бандле присутствуют новые light-form маркеры и отсутствуют bg-zinc-950 / прежняя подпись Albery.
• albery, albery-tg, hermes-gateway и nginx — active; tracked worktree чистый; ошибок albery после выкладки нет.

[b]Версия и откат[/b]
Commit: 51a88d99afc9f68c983911aff542f9da2e97cb4a
GitHub: https://github.com/xotizwf-create/Albery/commit/51a88d99afc9f68c983911aff542f9da2e97cb4a
Backup: /var/backups/albery/code/pre-calculator-light-20260729_143102
Быстрый откат: восстановить calculator/dist из backup или вернуть dist.bak.pre-51a88d9-20260729_143102; код откатить через git revert 51a88d9."""

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
