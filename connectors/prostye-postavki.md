---
id: prostye-postavki
type: connector
tags: [mcp, prostye-postavki, miramed32, commerce, supplies]
updated: 2026-05-30
secret_refs: [proj/<slug>/prostye_postavki/secret]
---

# Connector: Простые поставки (MCP)

MCP-сервер `miramed32`, подключён как `prostye_postavki` (HTTP, auth none, секрет в URL).
Человеческое имя для владельца — **«Простые поставки»**; в командах вкл/выкл/удаления это
маппится на id `prostye_postavki`.

## Назначение
Коммерческие предложения, складские остатки, договоры, поставки и работа с входящими
документами/организациями — 19 инструментов (`mcp_prostye_postavki_*`).

## Инструменты (19)
- Поиск/чтение: `search`, `fetch`, `list_database_tables`, `read_table_rows`,
  `get_contracts`, `get_inventory_balances`, `get_deliveries`, `list_commercial_templates`.
- Действия: `create_commercial_offer_archive`, `send_commercial_offer_email`,
  плюс инструменты для входящих контрактных документов и организаций.

## Без подтверждения
- Чтение/поиск: остатки, договоры, поставки, таблицы, шаблоны, входящие документы.

## Только с подтверждением
- Отправка наружу и создание артефактов: `send_commercial_offer_email`,
  `create_commercial_offer_archive`, сохранение/изменение контрактов и организаций.

## Подключение и управление
Через скилл `connect-mcp` (`hermes_mcp.py`). Секрет — только в `~/.hermes/config.yaml` (600);
в этом репозитории секрета нет (ссылка по имени). Реестр: `connectors/registry.yaml`.
