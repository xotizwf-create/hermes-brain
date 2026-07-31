import json
import os
import sys
from urllib.parse import urlsplit

os.environ["B24_TASK_OFFER"] = "0"
os.environ["B24_TASK_CHECKIN"] = "0"
sys.path.insert(0, "/var/www/albery")

from mcp import context_server

title = "Albery: публичный калькулятор ИУ и усиление защиты веб-контура"
description = """[b]Контекст[/b]
Подготовить и опубликовать отдельную страницу из переданного шаблона «Страница с калькулятором» по адресу /Калькулятор, доступную без пароля с любого устройства. Связать с ней кнопку калькулятора в Telegram-боте и проверить безопасность проекта.

[b]Проблема и последствия[/b]
Калькулятор не был встроен в приложение, весь веб-контур закрывался общей авторизацией, а кнопка бота передавала диалог человеку. При аудите также обнаружены риски SSRF во внешнем чтении URL, небезопасный XML fallback, слишком широкие auth-prefix исключения, доверие неизвестным SSH host keys, слабый fallback Flask secret и неполные browser security headers.

[b]Что требуется[/b]
1. Опубликовать адаптивный калькулятор по /Калькулятор/ без авторизации и без раскрытия других маршрутов.
2. Реализовать и протестировать расчёты ИУ; обновить кнопку Telegram.
3. Закрыть обнаруженные exploitable security findings и проверить зависимости/код сканерами.
4. Собрать фронтенд, выложить на production server 186, проверить HTTPS, сервисы и rollback.

[b]Критерий результата[/b]
Страница https://www.m4s.ru/Калькулятор/ возвращает 200 без сессии, ассеты загружаются, похожие URL требуют вход; расчёты покрыты тестами; кнопка Telegram ведёт на страницу; security-аудит зависимостей не находит известных уязвимостей, Bandit не находит high severity; production работает на зафиксированном коммите, сервисы активны, есть backup и описан откат."""

criteria = (
    "Публичный HTTPS-калькулятор доступен без авторизации; соседние маршруты защищены; "
    "формулы и Telegram-ссылка протестированы; security gates пройдены; production commit, "
    "сервисы, backup и rollback подтверждены."
)

created = context_server.tool_create_bitrix_task(
    {
        "title": title,
        "description": description,
        "result_criteria": criteria,
        "responsible_bitrix_user_id": 16,
        "creator_bitrix_user_id": 22,
        "deadline": "2026-07-29T14:30:00+03:00",
        "priority": "high",
        "tags": ["Albery", "калькулятор", "security", "production"],
        "checklist": [
            {"title": "Опубликовать /Калькулятор/ без авторизации", "complete": True},
            {"title": "Обновить кнопку Telegram-бота", "complete": True},
            {"title": "Закрыть findings security-аудита", "complete": True},
            {"title": "Пройти локальные и production-проверки", "complete": True},
        ],
    }
)
task_id = int(created["task_id"])

result_text = """[b]Реализовано[/b]
• Добавлена отдельная адаптивная React/Vite-страница /Калькулятор/ и точное публичное исключение из auth middleware.
• Формулы ИУ вынесены в тестируемый модуль; добавлена валидация сумм и процентов.
• Кнопка «Калькулятор расчёта ИУ» в Telegram ведёт на production URL.
• Усилены Flask session fallback, точность auth-prefix, CSP/Permissions-Policy, SSRF-защита с проверкой DNS и каждого redirect, XML fallback через defusedxml, SSH host-key policy и безопасная передача Zoom payload.

[b]Проверено[/b]
• Полный predeploy gate: 1522 passed, 17 skipped.
• Calculator unit tests, TypeScript check и production build — успешно.
• pip-audit — известных уязвимостей нет.
• npm audit для calculator, Интерфейс и wb-cabinet — 0 vulnerabilities.
• Bandit по всему Python-коду — 0 high severity.
• Production: /Калькулятор/ и asset — 200 без сессии; near-match — redirect на /login; HTTP→HTTPS; HSTS, CSP, nosniff, frame, referrer и permissions headers присутствуют.
• SSRF loopback и cloud metadata адреса блокируются.
• albery, albery-tg, hermes-gateway и nginx active; ошибок уровня error после деплоя нет; tracked worktree чистый.

[b]Версия[/b]
Commit: df4d4cd4dc55360ff3bbc36dcac765cd22af3fff
GitHub: https://github.com/xotizwf-create/Albery/commit/df4d4cd4dc55360ff3bbc36dcac765cd22af3fff

[b]Backup и откат[/b]
Code backup: /var/backups/albery/code/pre-calculator-20260729_132946
Nginx backup: /etc/nginx/sites-available/albery.bak-calculator-20260729_133411
Откат: git revert df4d4cd4dc55360ff3bbc36dcac765cd22af3fff, восстановить Nginx backup и calculator/dist из code backup, nginx -t, затем перезапустить только затронутые сервисы в пустое окно.

[b]Отдельное внешнее состояние[/b]
Общий deploy_smoke дополнительно сообщает, что Telegram Business can_reply недоступен. Диагностика Bot API подтвердила: оба подключения были отключены владельцем/Telegram до релиза (последнее изменение до деплоя); это не регрессия коммита и требует ручного переподключения в Telegram Business."""

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

webhook = os.getenv("BITRIX_WEBHOOK") or os.getenv("BITRIX_WEBHOOK_URL") or ""
parts = urlsplit(webhook)
base_url = f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else ""
task_url = (
    f"{base_url}/company/personal/user/16/tasks/task/view/{task_id}/"
    if base_url
    else ""
)
print(
    json.dumps(
        {
            "task_id": task_id,
            "completed": completed.get("completed") is True,
            "comment_id": comment_id,
            "task_url": task_url,
        },
        ensure_ascii=False,
    )
)
