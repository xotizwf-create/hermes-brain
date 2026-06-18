---
id: albery-server-mcp-tools
type: project
project: albery
tags: [albery, mcp, bitrix, zoom, fetch-url, webhooks, reference]
updated: 2026-06-18
secret_refs: []
---

# Albery — MCP-инструменты и их особенности (Bitrix, Zoom, fetch_url, фиксы)

> Извлечено из `server-context.md` при разбиении по темам (2026-06-13). Соседние документы: [server-context.md](server-context.md) (хаб), [server-infra.md](server-infra.md), [server-mcp-tools.md](server-mcp-tools.md), [server-integrations-sync.md](server-integrations-sync.md).

## Недавние прод-изменения (вебхуки Bitrix/Zoom, инкрементальная синхронизация)

Recent production changes:

- Bitrix task comments are now exposed through the main MCP connector:
  - new tool `get_task_comments(bitrix_task_id, include_service?, order?, limit?, offset?)` reads `bitrix_tasks.raw_json -> 'comments' -> 'items'`, strips Bitrix BB-codes, resolves author names from `users`, and hides auto-generated notifications (overdue reminders, status cards, completion notices) unless `include_service=true`;
  - `search_tasks` rows now also return `comments_total_count` and `comments_human_count` so the agent knows which tasks have real discussion;
  - no DB migration; lives in `mcp/context_server.py` (MCP server version `0.3.0`); not exposed on the FAQ endpoint.
- Bitrix tasks now support near-realtime sync through outgoing Bitrix webhook:
  - endpoint: `https://mcp.m4s.ru/bitrix/events/tasks/<BITRIX_EVENT_SECRET>`
  - events: `OnTaskAdd`, `OnTaskUpdate`, `OnTaskDelete`
  - queue table: `bitrix_task_events`
  - migration: `database/migrations/018_bitrix_task_events.sql`
  - unsupported Bitrix task comment events are accepted with `200 OK` and ignored.
- Zoom recordings now use incremental sync:
  - existing Zoom calls are skipped if the set of transcript files has not changed;
  - old transcript segments are not deleted/recreated for unchanged recordings;
  - manual/API/cron sync downloads only new or changed transcript files.
- Zoom webhook support was added:
  - endpoint: `https://mcp.m4s.ru/zoom/events/<ZOOM_EVENT_SECRET>`
  - events: `recording.transcript_completed`, `recording.completed`
  - validation event: `endpoint.url_validation`
  - queue table: `zoom_recording_events`
  - migration: `database/migrations/019_zoom_recording_events.sql`
  - `ZOOM_WEBHOOK_SECRET_TOKEN` must be copied from Zoom Marketplace Event Subscriptions Secret Token.
- Big external sync cron is daily at `18:00 Europe/Moscow`, not hourly:
  - file: `/etc/cron.d/albery-daily-sync`
  - logs: `/var/log/albery/daily-sync.log`, `/var/log/albery/daily-sync.cron.log`
- Latest relevant commits:
  - `90833c5 Expose Bitrix task comments via MCP`
  - `096c85f Add Bitrix task event sync`
  - `1f8c45d Add incremental Zoom recording sync`

Important env keys:

```env
BITRIX_EVENT_SECRET=...
BITRIX_TASK_EVENT_PROCESS_INLINE=1
ZOOM_EVENT_SECRET=...
ZOOM_WEBHOOK_SECRET_TOKEN=...
ZOOM_EVENT_PROCESS_INLINE=1
```

Operational checks:

```bash
cd /var/www/albery
git status --short
git rev-parse --short HEAD
systemctl status albery --no-pager
tail -n 120 /var/log/albery/daily-sync.log
tail -n 120 /var/log/albery/daily-sync.cron.log
```

Apply migrations/restart after deploy:

```bash
cd /var/www/albery && .venv/bin/python scripts/ensure_postgres.py && systemctl restart albery
```

Check webhook endpoints without printing secrets:

```bash
cd /var/www/albery
bitrix_secret=$(awk -F= '$1=="BITRIX_EVENT_SECRET"{print $2; exit}' .env)
zoom_secret=$(awk -F= '$1=="ZOOM_EVENT_SECRET"{print $2; exit}' .env)
curl -sS "https://mcp.m4s.ru/bitrix/events/tasks/$bitrix_secret"
curl -sS "https://mcp.m4s.ru/zoom/events/$zoom_secret"
```

Current GitHub branch: `main`. Push code changes to GitHub before or after server deployment so that future `./scripts/update_server.sh` does not overwrite manual server edits.

Этот файл фиксирует рабочий контекст проекта, чтобы в новом чате сразу было понятно, где что лежит и какими командами обслуживать сервер.

## FAQ MCP

Use this URL for the limited FAQ MCP server:

```text
https://mcp.m4s.ru/mcp-faq/<MCP_FAQ_SHARED_SECRET>
```

Set the secret in `/var/www/albery/.env`:

```env
MCP_FAQ_SHARED_SECRET=...
```

Allowed tools: `start_here_always_read_ai_instructions`, `health`, `get_context_guide`, `get_ai_instructions`, `list_available_sources`, `get_company_profile`, `list_company_files`, `get_company_file`, `search_company_knowledge`, `get_org_structure`, `list_zoom_calls`, `get_zoom_call_transcript`, `search_zoom_transcripts`.

Scope: org structure, regulations/company knowledge, AI instructions, and Zoom calls (transcripts + stored Zoom call reports exposed via `get_zoom_call_transcript.analytical_note`).

Unavailable there: Bitrix tasks, chats/messages, OCR processing, chat/owner report reading/generation/saving/deleting, compact export, Bitrix refresh, AI instruction editing, and Zoom report saving/deleting.

### Поиск по знаниям компании — гибридный (FTS + триграммы + ILIKE), с 2026-06-14

`search_company_knowledge` раньше был **чистый `ILIKE '%query%'`** — не понимал русскую морфологию
(«отчётность» ≠ «отчёты») и часто возвращал пусто, хотя документ есть (это была документированная
боль, см. [owner-reports.md](owner-reports.md) правило 3). Переписан на **гибрид** в
[mcp/context_server.py](mcp/context_server.py) `tool_search_company_knowledge`:

- **Русский full-text** (`to_tsvector('russian', name||' '||content)`) — совпадение по корням слов;
- **Триграммы** `pg_trgm` (`similarity(name, query)`) — опечатки/частичные слова (GIN-индексы уже были);
- **ILIKE** — точная подстрока как ещё один сигнал;
- ранжирование `ts_rank_cd + 0.5*similarity + бонус за точное совпадение имени`. Интерфейс инструмента
  не изменился; есть fallback на ILIKE, если колонка `content_tsv` ещё не создана (середина деплоя).

Инфраструктура: миграция `database/migrations/026_company_folders_fts.sql` (stored generated-колонка
`content_tsv` + GIN-индекс `idx_company_folders_content_tsv`), зарегистрирована в
`scripts/ensure_postgres.py` (`ALWAYS_APPLY_MIGRATIONS`, идемпотентна). Коммит `9b56146`.
Проверено на проде: «фиксация результатов» давало 0 по ILIKE → теперь 16 релевантных, топ
`Регламент_фиксации_результата`. **Деплой был backend-only** (git pull + `ensure_postgres.py` +
рестарт `albery`), БЕЗ `update_server.sh` — тот пересобирает фронт (`npm run build`), а это
memory-тяжело на 1 ГБ боксе (правило №7); для чисто бэкендовой правки фронт не трогать.

Возможная **ступень 2** (отложена): pgvector + эмбеддинги для семантики/синонимов («оплаты» ↔
«платёжный календарь»). Локальную модель грузить нельзя (RAM ~1 ГБ) — только API (Google-ключ уже в
`.env`, либо OpenAI). Корпус крошечный (42 дока), отдельная векторная БД не нужна — pgvector в той же
Postgres.

### Bitrix-инструменты в MCP

В MCP Albery доступны инструменты:

- `create_bitrix_task` — создаёт одну задачу в Bitrix (разовую или периодическую,
  с наблюдателями опционально). Агент обязан собрать и показать человеку перед
  созданием: ответственный, дедлайн, проверяемый результат, финальный человеческий
  текст задачи, полный список наблюдателей (если есть), и расписание (если
  периодическая). Если чего-то нет — уточнять до конца, не создавать. **Расширен
  28.05.2026** — три новых параметра:
  - `auditor_names: list[str]` / `auditor_bitrix_user_ids: list[int]` — наблюдатели
    из активной оргструктуры (`users.is_active=TRUE`). Резолвинг через новый хелпер
    `_resolve_active_bitrix_users` ([mcp/context_server.py](mcp/context_server.py)):
    fuzzy-match по `_person_names_match`, неоднозначность → отказ + список кандидатов
    с `bitrix_user_id`/`full_name`/`work_position`. Списки объединяются и
    дедуплицируются. На Bitrix уходит как `fields.AUDITORS = [int]`.
  - `periodic: {type, interval?, weekdays?, day_of_month?, daily_mode?, until?}` —
    расписание. Если присутствует, задача создаётся как `IS_REGULAR=Y` +
    `REGULAR_PARAMETERS` (через `_build_bitrix_regular_parameters`). Поддержка:
    - `type="daily"` + `daily_mode="all"|"workdays"` (default `all`) → `REPEAT_TYPE=daily`, `DAILY_MODE`;
    - `type="weekly"` + `weekdays=["MO","WE","FR"]` + `interval` → `REPEAT_TYPE=weekly`, `REPEAT_WEEKDAYS`, `REPEAT_EVERY`;
    - `type="monthly"` + `day_of_month=1-31` + `interval` → `REPEAT_TYPE=monthlydays`, `REPEAT_MONTHDAY`, `REPEAT_EVERY`;
    - опциональный `until="YYYY-MM-DD"` → `REPEAT_TILL`.
    Невалидные комбинации (нет `type`, weekly без `weekdays`, monthly без
    `day_of_month`, кривой weekday-код, `interval<1`, кривой `until`) → инструмент
    отказывает с понятным сообщением.
  Schema-валидация в `inputSchema` дополнительно ограничивает enum'ы. MCP server
  version поднят до `0.6.0`.
- `delete_bitrix_task` — удаляет одну задачу в Bitrix. Жёсткое правило:
  сначала `search_tasks(bitrix_task_id=...)`, затем показать пользователю точную
  задачу (номер, название, статус, ответственный, дедлайн) и спросить подтверждение.
  Только после явного подтверждения можно вызвать
  `delete_bitrix_task(bitrix_task_id=..., confirm=true)`. Нельзя удалять по названию,
  поисковому тексту или неоднозначной ссылке. В инструменте есть дополнительная
  защита: без `confirm=true` он откажет, а `expected_title` можно использовать как
  safety-check от удаления не той задачи.
- `list_pending_owner_recommendations(report_date)` — возвращает сохранённые
  черновики рекомендаций из `owner_manager_recommendations` за указанный день
  (только текущая версия отчёта, только статусы `new/queued`, только записи с
  `manager_bitrix_user_id IS NOT NULL`). Вместе с черновиками отдаёт поля отчёта:
  `report_summary`, `report_dynamics_summary`, `report_risks_summary`,
  `report_text`. Используется Hermes-агентом в Telegram-сессии после ответа
  владельца «отправляй», чтобы собрать `recipient_recommendations` под отправку.
- `send_owner_recommendations_to_bitrix(report_date, recipient_recommendations, confirm=true)`
  — шлёт каждому получателю один личный текст в Битрикс через `im.message.add`
  с fallback на `im.notify.personal.add`. `confirm=true` обязателен — без него
  инструмент отказывает. Параметр `recipient_recommendations` — это словарь
  `{bitrix_user_id: text}`; текст отправляется как есть, без редактирования. Под
  капотом — `send_owner_report_recommendations_to_bitrix` из `app.py`, который
  пишет каждую отправку в `owner_recommendation_dispatches` (channel `bitrix_im`
  / `bitrix_notification`), переводит соответствующие `owner_manager_recommendations`
  в `status='sent'` и пишет `sent`-событие в `owner_recommendation_events`.
- `cancel_owner_recommendation(recommendation_id, reason?)` — помечает одну
  запись `owner_manager_recommendations` как `cancelled`, фиксирует событие
  `cancelled` в `owner_recommendation_events`. Используется на «не отправляй»
  или «правки по <имя>: …» (старый черновик отменяется, новый формируется).
- `save_owner_daily_report` — **расширен 28.05.2026**: теперь принимает поле
  `manager_messages` (массив объектов со структурой
  `{manager_name, manager_bitrix_user_id, priority, message_type, subject, message_text, due, topics}`),
  и после INSERT в `owner_daily_reports` сразу вызывает
  `save_owner_daily_manager_messages` (в `app.py`) — он наполняет
  `owner_manager_recommendations` строкой на каждый объект из `manager_messages`.
  Без `manager_messages` инструмент работает как раньше (только сам отчёт).
- `list_pending_zoom_operational_dispatches(date_from?, date_to?)` — **добавлен 28.05.2026**:
  возвращает Zoom-созвоны с сохранённым `analytical_note`, по которым ещё не
  созданы агрегированные «Итоги созвона» задачи в Битрикс. **Default период —
  только сегодня (Europe/Moscow)** — это страховка от случайной отправки старых
  непереданных созвонов на ответ «ставь»; за прошлые дни нужно передать
  `date_from` явно. Hermes использует это как первый шаг Phase 2 zoom-to-tasks.
- `preview_zoom_operational_tasks(call_id)` — **добавлен 28.05.2026**: показывает
  что будет создано в Битрикс БЕЗ отправки. Возвращает `title` («Итоги созвона
  ЧЧ:ММ»), per-recipient `task_cards` (одна карточка = одна агрегированная
  задача), `deadline` (дата созвона 19:00 МСК), стандартное `description`.
  Полезен для отладки; в обычном flow Hermes этот инструмент не дёргает —
  идёт сразу к `dispatch_zoom_operational_tasks`.
- `dispatch_zoom_operational_tasks(call_id, confirm=true)` — **добавлен
  28.05.2026**: создаёт агрегированные Bitrix-задачи «Итоги созвона ЧЧ:ММ» —
  одна задача на каждого ответственного из `operational_tasks` сохранённого
  отчёта. Дедлайн = call_date 19:00 МСК. Описание = `ZOOM_OPERATIONAL_TASKS_DISPATCH_INTRO` +
  список задач этого человека. Внутри использует тот же
  `build_zoom_operational_task_cards` + `dispatch_prepared_zoom_operational_tasks`,
  что и Flask endpoint UI-кнопки «Отправка задач», поэтому формат идентичен.
  После успеха записывает `zoom_calls.raw_json.ai_report.bitrix_dispatch` (timestamp
  + созданные task_ids) — `list_pending_zoom_operational_dispatches` больше его
  не вернёт. Требует `confirm=true`. **НЕЛЬЗЯ заменять на серию
  `create_bitrix_task`** — это создаст много мелких задач вместо одной агрегированной.
- `send_bitrix_message(recipient_bitrix_user_id?, recipient_name?, message_text, confirm)` —
  **добавлен 28.05.2026**: отправляет одно личное сообщение в Bitrix любому
  активному сотруднику от моего пользователя (через `BITRIX_WEBHOOK_BASE`,
  отдельного бота пока нет). Под капотом — `send_bitrix_personal_message` в
  [app.py](app.py): `im.message.add` с fallback на `im.notify.personal.add` при
  `ERROR_NO_ACCESS`. Получатель резолвится через `_resolve_message_recipient` в
  [mcp/context_server.py](mcp/context_server.py) — приоритет у
  `recipient_bitrix_user_id` (точный integer); если передано только
  `recipient_name`, делается fuzzy-match по активным `users` (через
  `_person_names_match`), и при неоднозначности инструмент отказывает и возвращает
  кандидатов. `confirm=true` обязателен — Hermes должен сначала показать владельцу
  итоговый `message_text` + `full_name`/`work_position`/`bitrix_user_id` получателя
  и получить явное «отправляй». `message_text` уходит как есть, без редактирования
  и без подписей. Это **общий** инструмент для сценариев «напиши <имя> в Битрикс:
  …» из Telegram-чата с Hermes или любой ИИ через коннектор — НЕ путать с
  `send_owner_recommendations_to_bitrix` (тот строго привязан к
  `owner_daily_reports.manager_messages` и работает только в Phase 2 owner-daily).
  MCP server version поднят до `0.5.0` (`hermes mcp test albery` должен показывать
  45 инструментов).

### MCP-инструмент `fetch_url` (добавлено 28.05.2026)

**Зачем.** В Hermes для Telegram-платформы отключены встроенные `web`/`browser` toolset'ы ([agent.md:1538-1543](agent.md#L1538-L1543)) — после инцидента 28.05 с раздутой сессией на 100k токенов. Поэтому Hermes не мог открывать ссылки из чата (Google Sheets/Docs, статьи, регламенты). Включать `web` обратно опасно — одна большая страница съест полконтекста Codex.

**Решение.** Отдельный MCP-инструмент `fetch_url(url, max_chars?, strip_html?)`:
- **Google Sheets** URL (`docs.google.com/spreadsheets/d/<id>/edit?gid=<n>`) автоматически переписывается в `/export?format=csv&gid=<n>` → возвращается чистый CSV.
- **Google Docs** URL (`docs.google.com/document/d/<id>/...`) → `/export?format=txt`.
- Прочие URL: HTTP GET + `User-Agent: AlberyMCP/0.7`, по умолчанию HTML-теги срезаются до текста, скрипты/стили выкидываются.
- **Size cap:** default `max_chars=50000`, max 200000. Это ~12k токенов на ответ — не съедает контекст.
- На HTTP 401/403 для Google-документов в ответ добавляется `hint`: «Откройте доступ "Любой, у кого есть ссылка — Просмотр" либо положите файл в Drive-папку, которую читает Albery через Apps Script (`list_company_files` / `search_company_knowledge` / `get_company_file`)».

Когда **НЕ** использовать `fetch_url`: для знаний, которые уже синхронизированы в Albery (регламенты, инструкции, Zoom-расшифровки, чаты) — там быстрее и точнее работают `search_company_knowledge`, `list_company_files`, `get_company_file`, `search_messages`, `get_zoom_call_transcript`.

**Проверено на реальном Google Sheet** (28.05.2026, `17NZP5U5YBQPKKQrBUGq05bpTjq2V-KBX98uM1Wa2W_4`): 0.82с, HTTP 200, 6103 символа CSV, не truncated. Распарсилось как 40 строк × 7 колонок.

**Версия MCP** поднята до `0.7.0`, инструментов 46. Коммит `92c7391`.

**Flow в Telegram после /reset:** «Прочитай таблицу <ссылка> и создай задачи в Битриксе» → Hermes сам зовёт `fetch_url(...)` → парсит CSV → резолвит ФИО исполнителей/наблюдателей через `_resolve_active_bitrix_user(s)` → показывает план → ждёт «создавай» → циклом `create_bitrix_task` на каждую строку (с `auditor_names`, `periodic` если есть).

### Google Sheets + Apps Script — полноценные инструменты (2026-06-18, MCP `0.10.0`)

**Проблема.** В Битриксе агент с полным доступом отвечал «красивое оформление, графические дашборды
и перенос в папку Drive недоступны»: единственным гугл-инструментом был `create_google_sheet`
([app.py](app.py) `create_google_sheet`), умевший только задать название, залить строки
(`valueInputOption=USER_ENTERED` — формулы в ячейках работают) и выдать доступ «по ссылке —
редактор». Форматирования, charts, папок и Apps Script в коде не было. При этом **креды и scope уже
полные**: OAuth-токен `a9ent.ai` лежит на 186 в `/root/.hermes/secure/google_oauth_token.json`
(`_google_user_credentials()`), scopes `drive, spreadsheets, script.projects, script.deployments,
documents`. То есть не хватало только кода инструментов. (Скилл `google-sheets-dashboard-automation` —
это скилл *мозга* Hermes, в инструменты задеплоенного агента Albery он не подключён.)

**Что добавлено** (бэкенд-only, без пересборки фронта — правило №7). Функции в [app.py](app.py)
(вызываются через `app_workflow_function` = getattr из `app`):
- `format_google_sheet(spreadsheet_id, requests)` — тонкая обёртка над `spreadsheets.batchUpdate`:
  форматирование, числовые/валютные форматы, условное форматирование, закрепление строк, ширины
  колонок, объединение, **charts (addChart) для дашбордов**. Агент собирает стандартные объекты
  запросов Sheets API.
- `write_google_sheet_values(spreadsheet_id, cell_range, values, value_input_option)` — запись
  значений/формул в A1-диапазон (USER_ENTERED).
- `get_google_sheet_meta(spreadsheet_id)` — вкладки с `sheetId`/названием/размером (нужно, чтобы
  знать `sheetId` для batchUpdate).
- `move_drive_file_to_folder(file_id|item_id, folder)` — перенос файла, таблицы, документа **или папки**
  в другую папку Drive (id или ссылка). Технически папки в Drive тоже являются `files`, поэтому тот же
  parents API работает для вложенных папок.
- `remove_drive_item_from_folder(item_id|file_id, folder, confirm=true)` — убрать файл, таблицу, документ
  **или папку** из конкретной родительской папки Drive без полного удаления объекта из Google Drive.
  Требует предварительно показать человеку точный элемент и папку и получить подтверждение.
- `manage_apps_script(action, ...)` — Apps Script API: `create`/`get`/`update`/`deploy`/`run`/`publish_web_app`
  (см. блок «Веб-приложения» ниже — `publish_web_app` отдаёт готовый `web_app_url`).

6 MCP-инструментов в [mcp/context_server.py](mcp/context_server.py) (описания английские, чтобы не
ловить mojibake при патче). Тиринг: добавлены в `TOOLS` → автоматически в **`/mcp` (Полный)** и
**`/mcp-ops` (Все функции)**; НЕ в `FAQ_TOOL_NAMES`, НЕ в `OWNER_ONLY_TOOL_NAMES`. `manage_apps_script`
требует `confirm=true`. Версия MCP `0.9.0` → `0.10.0` (теперь ~62 инструмента). Возможности агента
обновлены в БД `ai_agent_capabilities` (tier `full`), чтобы он знал о новых умениях и не отвечал
«недоступно». Коммит Albery-репо `9cbc570`.

**Drive-файлы/папки внутри папок (фикс 18.06, MCP `0.10.1`).** После жалобы владельца Bitrix-агент
отказывался «удалить таблицу из указанной папки» и не умел перемещать папки внутри папок. Исправлено
backend-only: `move_drive_file_to_folder` теперь принимает и обычные ссылки/ID папок как `file_id` или
`item_id`, а новый `remove_drive_item_from_folder` снимает конкретного родителя (`removeParents`) без
удаления объекта из Drive. Проверено после рестарта: `/mcp` и `/mcp-ops` отдают оба инструмента через
`tools/list`; FAQ-тир их не видит, как и должно быть.

**Веб-приложения Apps Script — РАБОЧИЕ ссылки + сервисы (фикс 18.06, MCP `0.11.0`).** Симптом: владелец
попросил в Битриксе сделать веб-приложение, агент прислал ссылку, а она открывала Google Drive
«**Не удалось открыть файл**». Причина (две дыры в `manage_apps_script`):
1. **`deploy` вообще не создавал веб-приложение.** Он делал версию + deployment, но в манифесте
   (`appsscript.json`) **не было секции `webapp`**, поэтому web-app entry point не возникал и **рабочий
   `/exec`-URL не возвращался никогда**. У агента на руках был только `create`-URL редактора
   (`script.google.com/d/<id>/edit`) — а он для всех, кто не залогинен в аккаунт `a9ent.ai`, и есть тот
   самый Drive «Не удалось открыть файл». Он его и отправлял.
2. **`update` слал файлы кода без манифеста**, хотя Apps Script API требует манифест в `updateContent` —
   латентно ломалось.

**Фикс (backend-only, `app.py` + `mcp/context_server.py`, Albery `6eb699e`):**
- Новый одношаговый `action=publish_web_app`: create (или reuse `script_id`) → запись `files`
  `[{name,type:HTML|SERVER_JS,source}]` (код с `doGet`/`doPost`) → манифест с `webapp` →
  version+deploy → share → **возвращает живой `web_app_url`**
  (`https://script.google.com/macros/s/<id>/exec`). Доступ по умолчанию `ANYONE_ANONYMOUS` +
  `executeAs: USER_DEPLOYING` = **открыт по ссылке всем, без логина**.
- `deploy` теперь тоже инжектит `webapp`-манифест и отдаёт `web_app_url` (по умолчанию `web_app=true`).
- `create`/`update`/`publish_web_app` шарят сам проект **редактируемым по ссылке** (Drive `anyone:writer`,
  поле `shared`), чтобы и editor-ссылка открывалась у всех.
- **Подключение сервисов по проекту:** `advanced_services=['drive','sheets','calendar','gmail','docs',
  'slides','tasks','people','youtube','bigquery',...]` → пишутся в манифест
  `dependencies.enabledAdvancedServices` (правильные `serviceId`/`version`). `oauth_scopes=[...]` →
  `oauthScopes`. Для встроенных сервисов (`DriveApp`/`SpreadsheetApp`/`UrlFetchApp`) ничего включать не
  надо. Для **advanced**-сервисов на дефолтном GCP-проекте скрипта манифеста обычно достаточно; если
  advanced-вызов всё же даёт ошибку — владелец включает нужный API в Cloud-проекте `a9ent.ai`.
- **Правило агенту (в описании инструмента):** всегда давать владельцу **`web_app_url`, а не
  `editor_url`**.
- **Нюанс runtime-авторизации:** для `ANYONE_ANONYMOUS`+`executeAs USER_DEPLOYING` веб-приложение,
  которое реально дёргает Drive/Sheets/Gmail, при первом запуске может потребовать **разовой
  авторизации владельцем `a9ent.ai` в редакторе** (один клик). HTML-приложения без чувствительных
  scope работают сразу.

Проверено вживую сквозь весь путь (на 186, токен `a9ent.ai`): `publish_web_app` (с/без
`advanced_services`) и `deploy` → `web_app_url` отвечает **анонимным GET 200 + HTML**; манифест
содержит `enabledAdvancedServices`; `confirm`-гейт срабатывает; вызов через MCP-обёртку
`tool_manage_apps_script` тоже отдаёт рабочий URL. Тестовые проекты удалены. MCP `0.10.1` → `0.11.0`.
Деплой: коммит на 186 → push с 217 → reconcile 186 (процедура [deploy.md](deploy.md)). Связано:
[[albery-google-account-a9ent]].

**Доступ «для всех по ссылке» — гарантия (фикс 18.06, MCP `0.12.0`).** Жалоба владельца: открывает
присланную агентом ссылку (таблица/папка) и видит **«Нет доступа»**. Причины: `create_drive_folder`
вообще НЕ шарил папку; таблицы, которые **само Apps Script-приложение создаёт в рантайме**
(`SpreadsheetApp.create`), не шарятся; иногда агент давал ссылку на закрытый объект. Фиксы:
- `create_drive_folder` теперь авто-шарит папку `anyone:writer` (и на создании, и на reuse);
  `create_google_sheet` шарил и раньше (`share_anyone_writer=True`); `manage_apps_script` шарит скрипт.
- **Новый инструмент `share_drive_item_for_everyone(item)`** (`app.py` + MCP, тиры ops/admin): открывает
  ЛЮБОЙ Drive-объект (таблица/документ/папка/файл/Apps Script) по id или URL для всех по ссылке
  (редактор, fallback reader). Им агент гарантирует доступ к чему угодно — в т.ч. к таблице, которую
  создало само приложение.
- **Железное правило в системном промпте (admin/ops):** любой Google-объект, который агент создаёт ИЛИ
  на который даёт ссылку, ОБЯЗАН быть открыт «для всех по ссылке»; перед отправкой ссылки —
  проверить/открыть через `share_drive_item_for_everyone`; в генерируемом Apps Script, создающем файлы,
  добавлять `DriveApp.getFileById(id).setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT)`.
- Разовая зачистка: все a9ent-owned таблицы/папки/доки переоткрыты на anyone-with-link.
Проверено: инструмент открыл приватную таблицу → `anyone_with_link_editor`. Коммит Albery `a098532`.
Помощник `_share_drive_anyone(drive, file_id, role)` — общий шарер. MCP `0.11.0` → `0.12.0`.

**Веб-приложения на таблицах — открываются у ВСЕХ без входа (applet API, фикс 19.06, MCP `0.13.0`).**
Доказано тестом: Apps Script web app, чей код обращается к `SpreadsheetApp`/`DriveApp`, **отдаёт
анонимам 403** — Google требует, чтобы деплоящий аккаунт `a9ent.ai` авторизовал скрипт, а headless на
дефолтном GCP-проекте это сделать нельзя (scripts.run тоже не годится — нужен совпадающий GCP-проект,
а его через API не выставить). Чисто-HTML web app работает анонимно (200). Поэтому data-приложения
раньше не открывались «для всех», а агент усугублял, переключая публикацию на `ANYONE` (требует вход).
**Решение — applet API:** Apps Script отдаёт ТОЛЬКО HTML/JS (открывается анонимно), а данные
читает/пишет через публичный Albery-эндпоинт, который сам ходит в таблицу токеном `a9ent.ai` (всегда
авторизован):
- `GET/POST /applet/<token>` (`app.py`, в `AUTH_EXEMPT_PREFIXES`, CORS `*`): GET → `{values:[[...]]}`,
  POST `{values:[...]}` → добавляет строку (`values().append`). Token = HMAC(spreadsheet_id[+sheet]) на
  `FLASK_SECRET_KEY` — доступ только к ОДНОЙ таблице, не угадывается.
- MCP-инструмент **`make_sheet_applet(spreadsheet_id[, sheet])`** → `applet_url` + готовый `html_snippet`
  (`appletRows()` читает, `appletAdd([...])` добавляет). Агент встраивает его в HTML приложения.
- Публикация принудительно `ANYONE_ANONYMOUS` (любой `ANYONE`/пусто коэрсится и в манифесте, и в
  ответе; login-wall больше невозможен).
- Системный промпт научен строить data-app именно так (doGet=HTML-only, данные через applet).
Проверено сквозь: анонимные GET/POST через applet реально читают/пишут таблицу, анонимный `/exec`
отдаёт 200 (приложение открывается без входа). Коммит Albery `2e77924`. MCP `0.12.0` → `0.13.0`.
Связано: [[albery-google-account-a9ent]].

**Два «человеческих» нюанса (headless-ограничения a9ent.ai), которые агент сообщает сам:**
1. **Папка Drive.** Чтобы класть таблицу в конкретную папку, её надо **один раз** расшарить на
   `a9ent.ai@gmail.com` (редактор) — иначе `move_drive_file_to_folder` отдаёт `404 File not found`.
   Без этого таблица создаётся в Drive аккаунта агента и доступна по ссылке (anyone-editor).
2. **Apps Script API** должен быть включён в Google Cloud проекте `a9ent.ai` — иначе
   `manage_apps_script(create)` вернёт 403 «Apps Script API … is disabled». Создание/оформление
   таблиц и charts от этого НЕ зависят (это Sheets/Drive API).

Проверено сквозным тестом в venv (create + формулы + 8 запросов форматирования + chart) и живым
MCP-вызовом `tools/call get_google_sheet_meta` через `/mcp`. Демо-таблица:
`docs.google.com/spreadsheets/d/1XsacfTQdgPeV3BO62XFeLmbqR8mq3C11WxCnanGihF0/edit`. Связано:
[[albery-google-account-a9ent]].

**Читаемый дизайн таблиц (фикс 18.06).** После жалобы владельца на финансовый дашборд из Bitrix
агента: значения и заголовки резались, блоки съезжали, цветов было слишком много и непонятно, куда
смотреть. В `app.py` усилены `create_google_sheet`/`format_google_sheet`:
- ширины колонок считаются от реального содержимого (длинный русский текст, рубли/проценты/числа) с
  безопасными минимумами и максимумами, а не одним размером «на всех»;
- включён перенос текста и вертикальное выравнивание, строки авто-ресайзятся, шапки получают
  адекватную высоту;
- `format_google_sheet` после любых ручных `batchUpdate`-запросов агента запускает post-polish
  читаемости, чтобы даже случайно сжатые колонки снова раскрывались;
- инструкции MCP для Sheets переписаны: спокойная палитра, максимум 1–2 акцентных цвета, без
  красно-зелёной раскраски больших блоков, цвет только как смысловой акцент.
Проверено на проде через реальный Google OAuth агента: тестовая таблица с длинными заголовками дала
ширины 199–340 px; специально сломанная таблица с колонками 45 px после `format_google_sheet` была
автоматически раскрыта до 150/340/135 px, сервис `albery` остался активен без ошибок.

**Таймаут тяжёлой сборки (фикс 18.06).** Симптом: на «Создавай» бот в Битриксе через ~3 мин отвечал
**«Долго думаю — попробуй короче или переформулируй вопрос»**. Это НЕ Telegram-гейтвей (его журнал
пуст) — Bitrix-бот живёт в `albery.service` (`hermes_brain_answer` в [app.py](app.py)) и запускает
**`hermes` CLI как подпроцесс** с `subprocess.run(timeout=B24_TESTBOT_HERMES_TIMEOUT)` (дефолт
**170с**); по таймауту → `TimeoutExpired` → эта фраза (источник app.py:~21504; родственное «Не
уложился в лимит шагов» — app.py:~20770 у старого `b24_testbot_run_agent`). Инструменты быстрые
(<3с по `mcp_tool_call duration_ms`), но gpt-5.5 (один codex-аккаунт) думает ~15–60с между шагами,
а полноценная сборка (создать + 3 листа + форматирование + графики + перенос) — это ~10 шагов >170с.
Фикс: `B24_TESTBOT_HERMES_TIMEOUT=600` в `/var/www/albery/.env` (изначально подняли 170→300, затем
→600 под итеративные задачи; есть typing-keepalive + фоновый поток, длинный ход безопасен) +
`format_google_sheet` возвращает лёгкий `replies_count` вместо большого `replies` (меньше рост
контекста → быстрее каждый шаг). Коммит `a928f10`.

**Почему 600, а не больше/меньше.** Для итеративной работы (особенно кодинг в Apps Script:
написал → задеплоил → запустил → увидел ошибку → поправил) каждый цикл это 2–3 хода модели по
30–60с, и 300с мало. Внутренние лимиты самого `hermes` щедрые и НЕ режут (Albery
`/root/.hermes/config.yaml`: `max_iterations: 50`, `max_tool_calls: 50`, `max_turns: 60`) — связывает
именно подпроцессный таймаут бота. 600с = безопасный потолок (≈до 50 вызовов инструментов на ход);
это и максимум на ОДИН ход. Для задач длиннее: у бота есть непрерывность сессии (`hermes --continue`
+ инъекция истории), так что «продолжай» следующим сообщением расширяет работу через несколько ходов.
Возможный следующий рычаг, если сложная генерация упрётся в один долгий шаг — `inactivity_timeout: 120`
в hermes-config (пока не трогали). Радикальный вариант для тяжёлых сборок — композитный инструмент
(вся таблица за ОДИН MCP-вызов, чтобы убрать межшаговую латентность модели).

### Известный баг: 120s таймаут `create_bitrix_task` / `delete_bitrix_task` (исправлено 28.05.2026)

**Симптом.** Hermes в Telegram отвечал: «Не удалось создать задачу» или «MCP call timed out after 120.0s». В журнале `journalctl -u hermes-gateway`:

```
ERROR tools.mcp_tool: MCP tool albery/create_bitrix_task call failed:
MCP call timed out after 120.0s (configured timeout: 120.0s)
```

**Корневая причина.** В Albery жили **две разные реализации Bitrix-клиента**:
- `BitrixClient` в [app.py:14246](app.py#L14246) — на `requests.Session`, кэш, retry. **Быстрый**, < 2s. Используют `send_bitrix_message`, `dispatch_zoom_operational_tasks`, `send_owner_recommendations_to_bitrix`.
- `_bitrix_call_with_fallback` в [mcp/context_server.py](mcp/context_server.py) — на голом `urllib.request.urlopen(timeout=60)`. **Зависал ровно 120с** (30 минут, `delete_bitrix_task`.

Hermes-side MCP-клиент имеет свой ceiling 120s → urllib доходил до 120s раньше, чем что-либо ответил → Hermes ловил `MCP call timed out`, а никакая задача в Bitrix не создавалась.

Дополнительно у `delete_bitrix_task` был **SQL-баг**: JOIN на несуществующую колонку `bitrix_tasks.responsible_user_id` (на самом деле колонка зовётся `responsible_id`) → каждый вызов падал с `psycopg.errors.UndefinedColumn` ещё до обращения в Bitrix.

**Фикс.**
1. В [app.py](app.py) добавлен workflow `bitrix_method_call(method, payload, prefer_api=True)` — тонкая обёртка над `BitrixClient.call_with_fallback`. Доступен через `app_workflow_function("bitrix_method_call")`.
2. `_bitrix_call_with_fallback` в [mcp/context_server.py](mcp/context_server.py) свёрнут до 8 строк — делегирует в `bitrix_method_call`. Голый urllib выпилен.
3. SQL в `tool_delete_bitrix_task` поправлен: `responsible_user_id` → `responsible_id`.

После фикса замеры на проде (с реальным Bitrix через VPN-Эстонию):
- Разовая задача: **1.02s**
- Задача с наблюдателями (1 человек): **0.67s**
- Периодическая weekly с `IS_REGULAR=Y`: **0.72s** (Bitrix-портал принимает `REGULAR_PARAMETERS` ровно в нашем формате)

Версия MCP поднята до `0.6.1`. Коммиты: `db0c4e0` (urllib → BitrixClient), `90109e1` (SQL fix).

**Правило на будущее.** Любой новый MCP-инструмент, дёргающий Bitrix API, обязан идти через `app_workflow_function("bitrix_method_call")` (или прямо `BitrixClient` в самом app.py). Не делать собственные urllib-обёртки — это уже один раз привело к 120с таймауту в проде.

### Известная гран. ситуация: time-зоны в title «Итоги созвона ЧЧ:ММ»

В Postgres колонка `zoom_calls.start_time_msk` фактически хранится как UTC
(`timestamptz`), несмотря на название с `_msk`. Конверсия в МСК делается на
runtime через `astimezone(MSK_TZ)`. Это работает корректно в happy-path
(`zoom_call_row_payload` precomputed-ит `time_text` как `"09:28 - 10:26"` уже
в МСК). Но **fallback-пути** (когда `time_text` пустой) когда-то брали `str(start_time_msk)` напрямую — выдавали
ISO с `+00:00` и в title вылезало UTC время (например `"Итоги созвона 06:28"`
вместо МСК `09:28`).

Зафиксировано 28.05.2026:
- backend `build_zoom_operational_tasks_dispatch` ([app.py:3601-3611](app.py#L3601-L3611)) теперь конвертит fallback через `parse_datetime(...).astimezone(MSK_TZ).strftime('%H:%M')`;
- frontend `buildLocalZoomOperationalPreview` ([Интерфейс/src/App.tsx:4110-4124](Интерфейс/src/App.tsx#L4110-L4124)) использует `Date.toLocaleTimeString({timeZone: 'Europe/Moscow'})`.

Если в будущем появится новый код, формирующий «Итоги созвона …» из ISO-строки — обязательно конвертировать в МСК. Прямой использовать `str(call.start_time_msk)` нельзя.
