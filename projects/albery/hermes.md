---
id: albery-hermes
type: project
project: albery
tags: [albery, hermes, agent, codex, cron, telegram, mcp, reference]
updated: 2026-06-18
secret_refs: [proj/albery/ssh/root]
---

# Albery — Hermes agent (autonomous AI employee)

> ⚠ Hosts: the **dedicated Albery Hermes + its Codex run on `186.246.7.32`** (Timeweb; m4s.ru/mcp.m4s.ru
> → 186 by DNS; verified 2026-06-11). `217.198.12.236` is a *separate* box — the general Hermes Brain +
> andigital + Vault — and in this doc family it appears only where a note is explicitly about that box
> (its own Codex install, the `--target new` account manager, the brain/Vault store). Authoritative
> topology & access: [servers.md](servers.md).
> Credentials by NAME only — never print or commit secrets.

> Extracted from `server-context.md`. Hermes (Nous Research) is the autonomous agent that
> runs 24/7 on prod as a systemd service, lives in Telegram, with persistent memory, skills,
> a cron scheduler and an MCP client. Brain = ChatGPT (`gpt-5.5`) via the `openai-codex` provider.

## Hermes Agent (автономный ИИ-агент, мозг = ChatGPT Plus)

Настроено 2026-05-27. Поставлен локально на ПК в WSL2 для теста; следующий шаг —
перенос на прод-сервер.

### Что это и зачем

`Hermes Agent` (Nous Research, open-source) — автономный агент с **постоянной
памятью, навыками, cron-планировщиком и MCP-клиентом**. Он **model-agnostic**:
своего «мозга» у него нет, модель подключается по OAuth/API. Это **обвязка-агент**
(как Codex/Cline), а НЕ модель.

Наша задача: «цифровой сотрудник» по отчётам/действиям (а не правка кода). Albery
уже отдаёт инструменты для этого через MCP — Hermes выступает автономным
исполнителем поверх них. «Мозг» сейчас — **ChatGPT Plus (модель `gpt-5.5`)**.

### Ключевые пути и факты

```text
версия:        v0.14.0
бинарь:        ~/.local/bin/hermes
установка:     ~/.hermes/hermes-agent
конфиг:        ~/.hermes/config.yaml
токены аккаунтов: ~/.hermes/auth.json   ← для смены аккаунта и переноса на сервер
провайдер:     openai-codex   (= аккаунт ChatGPT через OAuth)
модель:        gpt-5.5        (доступна и gpt-5.4)
дашборд:       http://127.0.0.1:9119   (hermes dashboard --tui)
```

### Важные понятия (чтобы не путать)

- Провайдер **`openai-codex`** — это НЕ отдельный урезанный продукт, а технический
  **OAuth-канал к твоему аккаунту ChatGPT**. Модель `gpt-5.5` — обычная ChatGPT.
- Подписку ChatGPT в Hermes можно подключить **только** через `openai-codex`.
  Провайдер `openai` использует **API-ключ**, а не подписку.
- **Лимиты**: на подписке Plus они есть всегда, как ни подключайся. «Без потолка» —
  только **API-ключ** (платишь по токенам). Для автономного агента 24/7 на сервере
  правильнее API-ключ; подписка Plus периодически будет упираться в `usage limit`.

## Подробности (разбито по темам, 2026-06-13)

Этот файл — хаб. Грузи только нужную часть, а не весь дослер:

| Документ | Что внутри |
|---|---|
| [hermes-setup.md](hermes-setup.md) | Codex-auth на сервере, WSL2/VPN, установка, подключение/смена аккаунта ChatGPT, провайдер/модель, запуск, перенос на прод, чек-лист, прод-развёртывание, RBAC-роадмап |
| [hermes-automations.md](hermes-automations.md) | cron `zoom-to-tasks` и `owner-daily` (обе фазы), где править поведение отчётов |
| [hermes-operations.md](hermes-operations.md) | cron/Telegram/сессии, STT (Groq), таймауты, деплой промптов, правило рестарта gateway, approval=off, фикс `NameError` + `/accounts`/`/limits` + авто-переприменение, веб-UI знаний |

### Google Sheets через битрикс-агента

Фикс 2026-06-18: инструменты `create_google_sheet` и `write_google_sheet_values` в live-коде Альбери (`/var/www/albery/app.py`, плюс MCP-описание в `mcp/context_server.py`) нормализуют формулы под локаль Google Sheets. Для `ru_RU` сервер автоматически заменяет разделители аргументов формул с запятых на точки с запятой вне строковых литералов и после записи проверяет диапазон на ошибки формул. Если ошибки остаются, инструмент падает, чтобы агент не мог сказать «готово» про битую таблицу. Проверка: временная таблица с `=SUM(A2,B2)` в `ru_RU` дала рабочий результат без ошибок; созданная пользователем таблица `Калькулятор доходов и расходов` была исправлена — 20 формул конвертировано, ошибок формул не осталось.

Фикс 2026-06-18: таблицы от Bitrix-агента Альбери больше не должны выходить «голой сеткой». `create_google_sheet` автоматически применяет базовое читаемое оформление, когда переданы `rows`: закреплённая контрастная шапка, жирный белый текст, переносы, вертикальное выравнивание, границы, чередование строк, стартовые ширины колонок и авторазмер. `format_google_sheet` в MCP-описании усилен правилом: Google-таблица или таблица заданий не считается готовой без красивого читаемого оформления; для дашбордов/сложных таблиц агент обязан дополнительно использовать форматирование, графики, условные цвета, merged title blocks и смысловые числовые форматы. Проверка: временная таблица `Albery style smoke test 2026-06-18` через серверный `create_google_sheet` вернула `style_applied=true`; API-проверка подтвердила frozen header, banded ranges, bold header, тёмный фон, wrap и vertical middle.

См. также [overview.md](overview.md), [server-context.md](server-context.md), [vpn-gateway.md](vpn-gateway.md).
