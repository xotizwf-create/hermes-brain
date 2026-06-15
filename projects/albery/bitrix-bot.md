---
id: albery-bitrix-bot
type: project
project: albery
tags: [albery, bitrix, imbot, chatbot, hermes, mcp]
updated: 2026-06-15
secret_refs: []
---

# Albery — ИИ-ассистент внутри Bitrix24 (чат-бот на Мозге Гермеса)

Бот в чате Bitrix24, мозг которого — **Albery-Гермес** (агент на 186), с доступом по
уровню личности: обычные сотрудники → read-only знания компании (FAQ-MCP), Евгений/Александр →
полный MCP (планируется). Канал = ещё один вход к тому же агенту (как Telegram), не отдельный агент
(см. урок про дробление: [[hermes-multi-agent-design]]).

## Текущее состояние (2026-06-15)
- **Стадия 2 (read-only) работает в проде**: сотрудник пишет боту → бот показывает «печатает…» →
  Мозг Гермеса отвечает по знаниям компании (FAQ-MCP) → 👍 на сообщении.
- Развёрнуто на **тестовом портале** `b24-0xrp3s.bitrix24.ru` (НЕ боевой damaska). Это песочница;
  боевой портал/миграция — отдельно.
- **Готово**: реакции 👀→👍, tiered-доступ (Евгений/Александр → full MCP), жизненный цикл сессий
  (idle 8ч + ротация со сводкой), лог взаимодействий + еженедельный дайджест Александру в Telegram.

## Архитектура
`Bitrix-чат (локальное приложение, imbot) → обработчик в Albery (app.py, на 186) → Мозг Гермеса
(hermes CLI на 186) → текст → обработчик постит ответ в чат`.

Петлю в Bitrix замыкает **обработчик** (Гермес умеет доставлять ответ только в встроенные платформы
telegram/slack/…, Bitrix среди них нет).

## Почему локальное приложение, а не вебхук
Bitrix **запрещает регистрировать чат-бота из входящего вебхука** (`imbot.register` →
`403 ACCESS_DENIED: "Client ID not specified"`). Бот = только из приложения (локального/маркет).
Вебхук умеет дёргать `imbot.*` лишь для уже существующего бота.

## Эндпоинты (Albery, через mcp.m4s.ru)
- `POST /bitrix/imbot/app` — обработчик **локального приложения** (боевой путь бота). Принимает
  события приложения с блоком `auth` (`access_token`/`application_token`/`client_endpoint`).
  Добавлен в `AUTH_EXEMPT_PREFIXES` и в редирект-исключения `canonical_web_redirect`.
- `POST /bitrix/imbot/<secret>` — старый sandbox-путь по вебхук-секрету (`B24_TESTBOT_SECRET`),
  оставлен, но через него бота зарегистрировать нельзя.

## Модель авторизации и состояние
- На `ONAPPINSTALL`/`ONAPPUPDATE` бот регистрируется (`imbot.register` через app `access_token` —
  тут CLIENT_ID есть, проходит), сохраняются `application_token` + `client_endpoint` + `bot_id`.
- Последующие события валидируются по `application_token` (`hmac.compare_digest`).
- Ответы/typing/like — через **per-event `access_token`** против `client_endpoint`
  (`{endpoint}/{method}.json?auth=<token>`). Токен живёт ~1ч — хватает на ответ из фонового потока.
- Состояние (application_token, bot_id, endpoint) в JSON-файле `/var/www/albery/.b24_testbot_state.json`
  (путь из `B24_TESTBOT_STATE`) — обработчику не нужен рестарт после установки.
- Бот зарегистрирован: `bot_id=24`, CODE `hermes_agent`, имя «Гермес-ассистент (тест)».

## Мост к Мозгу Гермеса
`_b24_app_process` зовёт `hermes_brain_answer()`:
```
hermes -z "<подсказка>+<сообщение>" --continue "bitrix-<dialog_id>" -t albery-faq --yolo
```
- `cwd=/root`, `HOME=/root` (albery-сервис крутится под **root**, поэтому видит `/root/.hermes`).
- Ответ берётся со stdout, таймаут `B24_TESTBOT_HERMES_TIMEOUT` (170с), сессия на диалог.
- Замер: ответ ~8–30с, пик памяти hermes-процесса ~160МБ (бокс 2ГБ + 2ГБ swap — тянет).

## Безопасность (важно)
- **Toolset жёстко ограничен** `-t albery-faq` — только read-only FAQ-MCP, БЕЗ `terminal/web/code`.
  Иначе сотрудник через чат мог бы выполнять команды на проде от root.
- Полный MCP (`albery` → `mcp.m4s.ru/mcp/...`) ходит в **боевой damaska** (создание/удаление задач,
  сообщения людям). Его даём только Евгению/Александру и отдельно/аккуратно — не для всех.

## MCP-коннекторы Гермеса (на 186, `/root/.hermes/config.yaml` → `mcp_servers`)
- `albery` — полный MCP (`mcp.m4s.ru/mcp/<secret>`), был.
- `albery-faq` — добавлен 2026-06-15, read-only (`mcp.m4s.ru/mcp-faq/<secret>`). Бэкап конфига
  `config.yaml.bak-faq`. Требует рестарта `hermes-gateway`.
- Мозг: `gpt-5.5` через `openai-codex`/OpenRouter (НЕ Gemini — ключ `GOOGLE_API_KEY` у Albery с
  квотой ~0, отсюда был 429 у интерим-цикла).

## Реакции
Старый `im.message.reaction` = `METHOD_NOT_FOUND`, НО богатые реакции идут через **IM v2**:
`im.v2.Chat.Message.Reaction.add` / `.delete` (принимает коды `eyes`, `like`, …). Логика:
- «прочитал» → 👀 (`eyes`, add) + индикатор `imbot.chat.sendTyping` («печатает…»);
- «выполнено» → снять 👀 (`delete`) и поставить 👍 (`like`, add) на сообщении пользователя.

## Tiered-доступ (по личности)
`B24_TESTBOT_FULL_USER_IDS` (default `14,16` = Евгений Палей / Александр Никитенко) → полный MCP
(`-t albery`, может действовать в боевой damaska, изменения подтверждает). Все остальные → `albery-faq`
(read-only). Системный промпт и tier пишутся в лог. На тест-портале id: Евгений=14, Александр=16,
владелец-бота «ИИ Агент»=22, админ katestone=1.

## Сессии (жизненный цикл) — `bitrix_bot_sessions` (миграция 028)
Автосжатие у Albery-Гермеса ОТКЛЮЧЕНО → контекст ограничиваем сами:
- сессия на диалог с эпохой: `bitrix-<dialog>-e<epoch>`;
- **простой >8ч** (`B24_TESTBOT_IDLE_RESET_SECONDS=28800`) → новая эпоха (свежий контекст);
- **лимит реплик** (`B24_TESTBOT_TURN_CAP=16`) → ротация эпохи с переносом КРАТКОЙ сводки
  (паттерн conversation-summary-buffer): сводку строит быстрый `hermes -z` по логу диалога.

## Аналитика
- `bitrix_bot_interactions` (миграция 027): строка на запрос (диалог, user, tier, вопрос, ответ,
  латентность, статус). Запись best-effort, не ломает ответ.
- **Еженедельный дайджест** владельцу: `scripts/bitrix_bot_weekly_digest.py` → `hermes send --to
  "telegram:Александр Никитенко"` (цель в `B24_DIGEST_TARGET`), cron `/etc/cron.d/albery-bitrix-bot-digest`
  (Пн 10:00 МСК, `CRON_TZ=Europe/Moscow`), лог `/var/log/albery/bitrix-bot-digest.log`. Доставка проверена.

## Env (на 186, `/var/www/albery/.env`)
`B24_TESTBOT_WEBHOOK_BASE` (вебхук тест-портала, scope task/im/user/department/**imbot**),
`B24_TESTBOT_SECRET` (sandbox-путь), `B24_TESTBOT_MODEL` (gemini-2.0-flash, старый интерим-цикл),
`B24_TESTBOT_HERMES_TIMEOUT` (170с), `B24_TESTBOT_STATE`, `B24_TESTBOT_FULL_USER_IDS` (default `14,16`),
`B24_TESTBOT_IDLE_RESET_SECONDS` (28800), `B24_TESTBOT_TURN_CAP` (16), `B24_DIGEST_TARGET`.

## Ключевые коммиты (репо Albery, ветка main)
- `819c2a7` sandbox imbot (Gemini+тулы) · `3e43ded` app-flow (регистрация на install, app-token) ·
  `f44e351` мост к Мозгу Гермеса (faq read-only) · `daa48b6` typing + 👍.
- `8db738d` — реконсиляция прод-онли правок (промпт недельного отчёта + метка канала), которые жили
  только на диске прода; теперь в git (источник истины восстановлен).

## Деплой (бэкенд-only, правило #7)
Правка локально → commit/push → на 186 `cd /var/www/albery && git pull --ff-only && systemctl restart albery`.
БЕЗ `update_server.sh` (он пересобирает фронт = тяжело для памяти). Доступ к 186: креды в секрет-зоне
217 `/opt/hermes/secure/projects/albery/.env`; ходим local→217(paramiko)→186(sshpass).

## Реализовано 2026-06-15 (коммиты Albery)
`0d4a6a5` лог взаимодействий · `da62889` реакции 👀→👍 + tiered + сессии (миграции 027/028) ·
`03abf7e` еженедельный дайджест. Деплой бэкенд-only (`git pull` + `ensure_postgres.py` + рестарт albery).

## Open tasks
1. **Боевая миграция портала** (когда компания переедет на новый Bitrix): полный MCP бота сейчас
   ходит в damaska — full-tier (Евгений/Александр) реально действует в боевой системе, помнить про это.
2. Опционально: кластеризация тем вопросов в дайджесте (сейчас просто последние вопросы), typing
   повторять каждые ~25с для длинных ответов, 👀-как-сообщение если v2-реакция где-то недоступна.
3. На тест-портале лог пустой до первых реальных чатов — дайджест наполнится после использования.
