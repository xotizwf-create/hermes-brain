---
id: albery-hermes-automations
type: project
project: albery
tags: [albery, hermes, cron, zoom, owner-report, bitrix, reference]
updated: 2026-06-13
secret_refs: []
---

# Hermes — cron-автоматизации (zoom-to-tasks, owner-daily)

> Извлечено из `hermes.md` при разбиении монолита по темам (2026-06-13). Сосед­ние документы: [hermes.md](hermes.md) (хаб), [hermes-setup.md](hermes-setup.md), [hermes-automations.md](hermes-automations.md), [hermes-operations.md](hermes-operations.md).

Две cron-задачи Hermes на проде формируют отчёты/задачи. Управление и логи — в [hermes-operations.md](hermes-operations.md); где править поведение — раздел «Обучение Hermes» ниже.

Две автоматизации (`hermes cron list`):

- `zoom-to-tasks` — `*/5 * * * *`: находит Zoom-созвоны без отчёта
  **без расхода Codex на пустых проверках**. Реализовано как `no-agent` cron
  со скриптом `/root/.hermes/scripts/zoom_watchdog.sh`: скрипт напрямую и быстро
  проверяет PostgreSQL (`zoom_calls` за последние 2 дня, `analytical_note=''`,
  транскрипт есть). Если новых Zoom нет — stdout пустой, Telegram молчит, LLM не
  вызывается. Если есть новый Zoom — скрипт быстро запускает отдельный защищённый
  worker и сам сразу завершается, чтобы короткий timeout `no-agent` cron не мог
  оборвать качественное формирование отчёта. Worker уже запускает `hermes -z` с
  промптом из `/root/.hermes/scripts/hermes_zoom_to_tasks_prompt.txt`
  (источник правды в git: [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt)).
  Промпт подставляет `$DATE_FROM`, `$DATE_TO`, `$MISSING` через awk-substitution
  (без проблем со sed-escaping для многострочных значений).
  В скрипте есть `flock`, отдельный lock на worker и короткий cooldown 900 сек
  на тот же набор missing-call id; состояние «обработано» записывается только
  после успешного завершения `hermes -z`, чтобы не глушить повтор после ошибки.

  **Что делает агент.** По промпту строго:
  1. `start_here_always_read_ai_instructions` → `get_context_guide`;
  2. для каждого созвона: `get_report_contract(zoom_processing)` (контракт — 13 KB, 12 разделов в `report_text` + JSON-схема с обязательным `operational_tasks`), `get_zoom_call_transcript(include_full_text=true)`, `get_org_structure`;
  3. формирует отчёт **строго по контракту** (12 разделов + полный JSON) и сохраняет через `save_zoom_call_report` — это кладёт `analytical_note` и `raw_json.ai_report.analysis.operational_tasks`;
  4. в Битрикс задачи НЕ создаёт (verification mode).

  **Что приходит в Telegram (формат принципиально короткий).** Никакого пересказа отчёта, никаких разделов «Краткая суть» / «Риски» / «Выводы»:
  ```
  Созвон: <ДД.ММ.ГГГГ> — <тема>

  Предлагаю поставить задачи в Битрикс:
  1. <ФИО> — <task_text>. Срок: <deadline_text>. Критерий: <result_criteria>.
  2. …

  Создаём задачи в Битрикс? Ответь «ставь» — я по каждому ответственному создам одну агрегированную задачу «Итоги созвона <ЧЧ:ММ>» с дедлайном <дата созвона> 19:00 МСК и описанием со списком всех его задач из созвона (формат как в Albery UI). «Не ставь» — пропускаю. «Правки по №<n>: <текст>» — пересоберу конкретную.
  ```
  Если задач 0 — строка «Задач не выделено.» и финальный вопрос не задаётся. Если обработано несколько созвонов — каждый отдельным блоком через разделитель «———».

  Полный отчёт по контракту (краткая суть, риски, поведенческие факторы, диагностика и т.д.) живёт **только в БД** (`analytical_note` + `raw_json.ai_report.analysis`) и доступен через UI Albery / MCP `get_zoom_call_transcript`. В Telegram он не дублируется.

  **На ответ «ставь» (Phase 2 — отправка в Битрикс).** Hermes в Telegram-сессии **НЕ создаёт по одной мелкой задаче через `create_bitrix_task`** — он использует existing UI dispatcher (тот же код, что и кнопка «Отправка задач» в Albery UI):
  1. `list_pending_zoom_operational_dispatches()` без аргументов — возвращает массив `pending` ТОЛЬКО за сегодня (Europe/Moscow). Это именно те созвоны, которые владелец видел в недавней сводке.
  2. Для каждого `pending` → `dispatch_zoom_operational_tasks(call_id, confirm=true)`. Этот инструмент сам сгруппирует `operational_tasks` по ответственному, создаст **одну агрегированную Bitrix-задачу** «Итоги созвона ЧЧ:ММ» на каждого человека с описанием через стандартный intro `Ознакомьтесь со списком выделенных из созвона задач и поставьте себе самые важные в Битрикс…` + нумерованный список этого человека.
  3. После успешной отправки бэкенд помечает `zoom_calls.raw_json.ai_report.bitrix_dispatch` (timestamp + task_ids) → следующий `list_pending` для того же дня уже не вернёт этот созвон.
  4. Hermes отвечает владельцу короткой человеческой сводкой («Создано M задач в Битрикс по созвону <тема>: — ФИО (N задач)»), без техн id, MCP, прочей кухни.

  Правило поведения на «ставь» зафиксировано отдельной AI-инструкцией в Albery («Cron автоматизации/Zoom задачи — ответ ставь», источник в git: [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md)). Hermes читает её через `start_here_always_read_ai_instructions` в начале Telegram-сессии. Деплой инструкции — `python scripts/upsert_albery_ai_instruction.py "<path>" scripts/ai_instruction_zoom_approval.md`.

  Жёсткие правила в этой AI-инструкции (важны чтобы Hermes не сжигал токены и не делал лишнего):
  - НЕ переспрашивай «3 обязательных поля» — у `dispatch_zoom_operational_tasks` все поля собираются из БД автоматически.
  - НЕ вызывай `create_bitrix_task` для отдельных задач — это создаёт много мелких задач вместо одной агрегированной.
  - НЕ ищи `call_id` вручную через `list_zoom_calls`/`get_zoom_call_transcript` — `list_pending_zoom_operational_dispatches` уже отфильтровал нужное.
  - НЕ читай `get_org_structure`, `get_zoom_call_transcript`, `get_report_contract` — dispatch сам всё подтянет из БД.
  - На «не ставь» — ничего не создавай, отвечай «Понял, задачи не ставлю.».
  - На «правки по №N: …» — `dispatch_zoom_operational_tasks` не вызывай; режим редактирования отдельной задачи пока не автоматизирован, обсуди с владельцем устно.

  **Деплой обновлённого промпта/watchdog'а**:
  ```powershell
  python scripts/update_hermes_zoom_to_tasks.py
  # Опции:
  #   --reset-and-run <zoom_call_uuid>
  #     дополнительно: удалит сохранённый отчёт за этот созвон через MCP
  #     delete_zoom_call_report, сбросит cooldown, и запустит watchdog один раз
  #     через bash (для разработки; в проде используйте `hermes cron run f217482a8618`
  #     если нужна реальная cron-delivery в Telegram).
  ```
  Источники правды в git:
  - [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt) — текст промпта (на проде: `/root/.hermes/scripts/hermes_zoom_to_tasks_prompt.txt`);
  - [scripts/hermes_zoom_watchdog.sh](scripts/hermes_zoom_watchdog.sh) — wrapper (на проде: `/root/.hermes/scripts/zoom_watchdog.sh`, права 0700);
  - [scripts/update_hermes_zoom_to_tasks.py](scripts/update_hermes_zoom_to_tasks.py) — патчер.
  - [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md) — AI-инструкция Albery для Telegram-сессии.
  - [scripts/upsert_albery_ai_instruction.py](scripts/upsert_albery_ai_instruction.py) — общий патчер AI-инструкций через MCP `upsert_ai_instruction`.
  Бэкап предыдущего watchdog'a: `/root/.hermes/scripts/zoom_watchdog.sh.bak`.
- `owner-daily` — `0 18 * * *`: формирует и сохраняет ежедневный отчёт собственнику
  по контракту `get_report_contract(owner_daily)`. **На уровне prompt самого Hermes**
  (не MCP-инструкций — контракт `owner_daily` НЕ трогали) включён двухфазный
  режим согласования рекомендаций → отправка в Битрикс.

  **Фаза 1 — формирование (cron в 18:00 МСК).** Hermes:
  1. читает живые AI-инструкции, контракт `owner_daily`, источники за день (чаты с OCR, Zoom-отчёты, Bitrix-задачи, оргструктуру, регламенты, предыдущий owner-отчёт);
  2. вызывает `save_owner_daily_report` и **дополнительно передаёт** аргумент `manager_messages` — массив адресных сообщений ТОЛЬКО для пятёрки (Сергей Виноградов, Наталья Горюнова, Артур Степанян, Евгений Палей, Александр Никитенко). В каждом `message_text` уже лежит ПОЛНЫЙ финальный текст в формате «<Имя>, приветствую! Рекомендации: 1) … 2) …», который пойдёт в Битрикс одной репликой;
  3. для Евгения Палея (собственник) в начало `message_text` добавляется блок «Главный вывод дня — <2-3 строки executive summary>»;
  4. на стороне MCP `tool_save_owner_daily_report` после INSERT в `owner_daily_reports` вызывает `save_owner_daily_manager_messages` (в `app.py`), который парсит `manager_messages` и пишет каждое сообщение строкой в `owner_manager_recommendations` со `status='new'`;
  5. для **НЕ-разрешённых** сотрудников рекомендации в `manager_messages` НЕ передаются вообще — наблюдения по ним остаются только в `report_text/recommendations` отчёта;
  6. **если для пятёрки за день нет фактов-оснований** (нет созвонов/чатов/ответов/просрочек) — `manager_messages` пустой, в БД ничего не записывается, и Hermes возвращает **пустой stdout** → Telegram молчит вообще (правило тишины, как у `zoom-to-tasks` при отсутствии новых созвонов);
  7. если хоть один блок есть — Hermes собирает единое сообщение и присылает мне в Telegram:
     ```
     Согласуйте что мы отправляем:

     Евгений, приветствую!
     Главный вывод дня — …
     Рекомендации: 1) … 2) …

     ———

     Сергей, приветствую!
     Рекомендации: 1) …

     Отправляю в Битрикс? Ответь: отправляй / не отправляй / правки по <имя>: <текст>.
     ```

  **Фаза 2 — отправка в Битрикс (ответ владельца в Telegram).** На «отправляй»
  Hermes в новой Telegram-сессии:
  1. `list_pending_owner_recommendations(report_date=today)` — читает сохранённые черновики из `owner_manager_recommendations` (статус `new`);
  2. собирает `recipient_recommendations = {manager_bitrix_user_id: recommendation_text}` строго как есть (тексты уже финальные и одобренные);
  3. `send_owner_recommendations_to_bitrix(report_date, recipient_recommendations, confirm=true)` → backend (`send_owner_report_recommendations_to_bitrix` в `app.py`) шлёт каждому через **`im.message.add` от моего имени** (через существующий `BITRIX_WEBHOOK_BASE`, отдельного бота пока не делаем) с fallback на `im.notify.personal.add` при `ERROR_NO_ACCESS`;
  4. факт отправки пишется в `owner_recommendation_dispatches` (channel `bitrix_im` или `bitrix_notification`), статус соответствующих `owner_manager_recommendations` обновляется на `sent`, в `owner_recommendation_events` фиксируется событие `sent`;
  5. на «правки по <имя>: …» — Hermes пересобирает текст для этого человека и снова показывает на согласование (старый черновик можно пометить `cancel_owner_recommendation(recommendation_id, reason)`);
  6. на «не отправляй» — отметка статусов `cancelled`, ничего в Битрикс не уходит.

  Сценарий полностью автоматизированный — отдельного «Альбери Бота» в Bitrix пока нет, сообщения идут от моего пользователя через тот же webhook, что и `create_bitrix_task`. Когда добавим отдельного бота (Phase 2), достаточно будет переключить `send_owner_report_recommendations_to_bitrix` на новый webhook.

### Обучение Hermes (где править поведение, по убыванию силы)

| Уровень | Источник правды | Кто читает | Деплой |
|---|---|---|---|
| Контракт отчёта (структура секций + JSON-схема) | Albery UI → `Сводная аналитика → Настройка промтов` (`zoom_processing`, `owner_daily`) | Все — Hermes, внешние ассистенты | Сохранение в UI = live |
| AI-инструкции (правила поведения) | Albery UI → `Настройки → Инструкции для ИИ` + git: [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md) | Hermes через `start_here_always_read_ai_instructions` в начале сессии | `python scripts/upsert_albery_ai_instruction.py <path> <file>` |
| Cron-промпт (что делает одна джоба) | git: [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt), [scripts/hermes_owner_daily_prompt.txt](scripts/hermes_owner_daily_prompt.txt) | Только эта cron-джоба | `python scripts/update_hermes_*_prompt.py` → restart gateway |
| Память Hermes (личные предпочтения) | `/root/.hermes/state.db` через `hermes memory` или «запомни: …» в Telegram | Hermes везде, в рамках инстанса | Live |

**Правило большого пальца:** что должно быть у всех (формат отчёта, состав пятёрки, что считать срочным) → **контракт/AI-инструкции в Albery**. Что специфично для одной cron-джобы (cooldown, формат Telegram-сводки) → **cron-промпт в git**. Личные предпочтения владельца → **`hermes memory`**.

**Болевая точка** из ретро [agent.md:1545-1549](agent.md#L1545-L1549): обучать **жёсткими запретами** в AI-инструкции, а не уговорами. Пример из [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md): «НЕ вызывай `create_bitrix_task` / НЕ читай `get_org_structure`» — это спасло Codex-лимит. Без таких запретов Hermes идёт в `search_files` и сжигает 100k токенов.
