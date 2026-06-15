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
- **Open**: tiered full-доступ для Евгения/Александра (боевой MCP, реальные действия в damaska);
  жизненный цикл сессий; лог взаимодействий + аналитика.

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

## Реакции (ограничение портала)
Портал по REST НЕ умеет произвольные эмодзи-реакции (`im.message.reaction` = `METHOD_NOT_FOUND`).
Доступно только: `imbot.chat.sendTyping` («печатает…») и `imbot.message.like` (👍). Поэтому:
- «прочитал/в работе» → typing-индикатор (не 👀-реакция, её нет);
- «выполнено» → 👍 (`imbot.message.like` на сообщении пользователя).

## Env (на 186, `/var/www/albery/.env`)
`B24_TESTBOT_WEBHOOK_BASE` (вебхук тест-портала, scope task/im/user/department/**imbot**),
`B24_TESTBOT_SECRET` (sandbox-путь), `B24_TESTBOT_MODEL` (gemini-2.0-flash, для старого интерим-цикла),
`B24_TESTBOT_TOOLSET` (default `albery-faq`), `B24_TESTBOT_HERMES_TIMEOUT`, `B24_TESTBOT_STATE`.

## Ключевые коммиты (репо Albery, ветка main)
- `819c2a7` sandbox imbot (Gemini+тулы) · `3e43ded` app-flow (регистрация на install, app-token) ·
  `f44e351` мост к Мозгу Гермеса (faq read-only) · `daa48b6` typing + 👍.
- `8db738d` — реконсиляция прод-онли правок (промпт недельного отчёта + метка канала), которые жили
  только на диске прода; теперь в git (источник истины восстановлен).

## Деплой (бэкенд-only, правило #7)
Правка локально → commit/push → на 186 `cd /var/www/albery && git pull --ff-only && systemctl restart albery`.
БЕЗ `update_server.sh` (он пересобирает фронт = тяжело для памяти). Доступ к 186: креды в секрет-зоне
217 `/opt/hermes/secure/projects/albery/.env`; ходим local→217(paramiko)→186(sshpass).

## Open tasks
1. **Лог взаимодействий** (фундамент аналитики): таблица `bitrix_bot_interactions` + запись на запрос.
2. **Жизненный цикл сессий**: автосжатие у Albery-Гермеса ОТКЛЮЧЕНО (падало на codex) → нельзя
   полагаться на бесконечный `--continue`; ограничивать сессию по простою/N-репликам или вести свою сводку.
3. **Tiered full-доступ** для Евгения/Александра по `bitrix_user_id` → toolset полного MCP.
4. **Анализ**: еженедельный дайджест использования владельцу (по образцу `self-review`).
5. Опционально: 👀 как сообщение-плейсхолдер с последующим редактированием в ответ (если нужен буквально глазок).
