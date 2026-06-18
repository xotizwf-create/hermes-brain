---
name: albery-webapp-design
description: Use when building any Apps Script web app for Albery (mini-CRM, form, dashboard, calculator) so it always matches the Albery prod-site look AND opens for everyone with no Google login. Covers the brand design system + the anonymous data architecture (applet API) + the build flow.
---

# Skill: albery-webapp-design

## Goal
Every web app the Albery agent makes must (1) **look like the prod React site** (Albery brand, not random)
and (2) **open for everyone by link without a Google login** and read/write data. Two hard rules make
this work — never deviate.

## Rule 1 — анонимность: Apps Script doGet отдаёт ТОЛЬКО HTML/JS
A web app whose Apps Script code touches `SpreadsheetApp`/`DriveApp` returns **403 to anonymous users**
(Google requires the deploying account `a9ent.ai` to authorize the script — impossible headless on a
default GCP project; proven by test). Pure-HTML apps open anonymously (200). So:
- `doGet` returns only static HTML/JS — **никогда** не вызывай `SpreadsheetApp`/`DriveApp` в коде скрипта.
- Read/write the sheet from the page's JS via the **Albery applet API** (it uses a9ent.ai's authorized
  token server-side, so the browser needs no auth): `make_sheet_applet(spreadsheet_id)` → `applet_url` +
  `html_snippet` with `appletRows()` (read) and `appletAdd([...])` (append).
- Publish **only** `ANYONE_ANONYMOUS` (the tools coerce `ANYONE`→anonymous; `ANYONE` = login wall = bad).

## Rule 2 — фирменный дизайн: всегда через get_webapp_template
Call `get_webapp_template(title)` and build on its CSS — never hand-roll random styles. It is distilled
from the prod app (`/var/www/albery/Интерфейс/src`):

| Токен | Значение |
|---|---|
| Фон страницы | `#f6f8fb` |
| Карточки | белые `#fff`, border `#eef0f4`, радиус **18px**, мягкая тень |
| Primary (акцент) | **`#5440F6`** (фиолетовый), hover `#4532db`, focus-glow `rgba(84,64,246,.x)` |
| Текст | `#0f172a`, приглушённый `#64748b` |
| Радиусы | 12–18px (кнопки/инпуты 12px, карточки 18px) |
| Шрифт | **Inter** (Google Fonts) + system-sans fallback |
| Успех/ошибка/варн | `#16a34a`/`#e7f8ed`, `#ef4444`, `#fef3c7` |

CSS-классы из шаблона: `.app .topbar .brand .card .btn .btn-primary .field .input .row table .badge
.badge-success .stat .grid .toast .muted .right`. Собирай UI только из них → единый аккуратный вид.

## Build flow (для data-приложения)
1. `create_google_sheet(title, [headers])` — таблица-БД (создаётся уже открытой по ссылке).
2. `make_sheet_applet(spreadsheet_id)` → `applet_url` + `html_snippet`.
3. `get_webapp_template(title)` → `html_skeleton` (плейсхолдеры `{{TITLE}}` `{{CONTENT}}` `{{APPLET}}`) +
   `content_example`.
4. Собери HTML: подставь заголовок; в `{{CONTENT}}` — свои `.card` с таблицей/формой/статами (ориентир —
   `content_example`); в `{{APPLET}}` — `html_snippet`; данные читай `appletRows()` / пиши `appletAdd([...])`.
5. `manage_apps_script(action="publish_web_app", files=[{name:"Code", type:"SERVER_JS",
   source:"function doGet(){return HtmlService.createHtmlOutput(<HTML>).addMetaTag('viewport',
   'width=device-width, initial-scale=1');}"}])` → вернёт рабочий `web_app_url` (анонимный).
6. Дай владельцу `web_app_url` (всегда указывай также `script_id`+`editor_url` для будущих правок —
   см. [[albery-bitrix-bot]] про память/recall).

Для дашборда/калькулятора без записи — шаги те же, но только чтение (`appletRows()`), или вообще без
таблицы (чистый расчёт).

## Why this exists / pitfalls
- `ANYONE` (не ANONYMOUS) требует вход Google → «не заходит с любого аккаунта». Только `ANYONE_ANONYMOUS`.
- `SpreadsheetApp` в `doGet` → 403 анонимам. Данные — только через applet.
- Любой созданный Google-объект (таблица/папка/скрипт) должен быть открыт по ссылке —
  `create_google_sheet`/`create_drive_folder` делают это сами; для прочего — `share_drive_item_for_everyone`.
- Канонический источник дизайна — прод-фронт `Интерфейс/src` (Vite+React, Tailwind v4). Инструмент
  `get_webapp_template` держит ту же палитру; реализация — `webapp_design_template()` в `app.py`,
  MCP-тиры ops/full. См. [[albery-server-mcp-tools]].

## Реализация (где живёт)
- Albery-репо `app.py`: `webapp_design_template()`, `make_sheet_applet()`, applet-маршрут `/applet/<token>`,
  `manage_apps_script` (publish_web_app, force-anonymous). MCP-инструменты: `get_webapp_template`,
  `make_sheet_applet`, `manage_apps_script`, `share_drive_item_for_everyone`. MCP `0.14.0`.
- Документация: `projects/albery/server-mcp-tools.md`, `projects/albery/bitrix-bot.md`.
