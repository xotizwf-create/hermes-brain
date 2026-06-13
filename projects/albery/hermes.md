---
id: albery-hermes
type: project
project: albery
tags: [albery, hermes, agent, codex, cron, telegram, mcp, reference]
updated: 2026-06-13
secret_refs: [proj/albery/ssh/root]
---

# Albery — Hermes agent (autonomous AI employee)

> ⚠ Server IP — CORRECTED 2026-06-11: the **dedicated Albery Hermes runs on `186.246.7.32`**
> (Timeweb; m4s.ru/mcp.m4s.ru → 186 by DNS). The `217.198.12.236` references scattered below were
> WRONG — 217 is the *separate* general Hermes Brain box. `186.246.7.32` is correct (it was the
> original 2026-05-27 host all along). Access + topology: `servers.md`. Codex was also set up here.
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

См. также [overview.md](overview.md), [server-context.md](server-context.md), [vpn-gateway.md](vpn-gateway.md).
