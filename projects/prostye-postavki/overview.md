---
id: prostye-postavki-overview
type: project
project: prostye-postavki
tags: [overview]
updated: 2026-05-31
secret_refs: []
---

# Простые поставки — overview

## What it is
«Простые поставки» — критически важный рабочий проект для учета контрактов, товаров и коммерческих предложений в сфере госзакупок. В проекте хранится значимая информация по одной из работ Александра, поэтому любые операции с данными, сервером, БД, КП и документами должны выполняться особенно аккуратно.

## Core capabilities
- Учет контрактов и позиций.
- Учет товаров, остатков, поставок и этапов исполнения.
- Генерация коммерческих предложений.
- Работа с входящими договорами/контрактами через OCR и ручное извлечение полей.
- MCP-сервер содержит инструкции и инструменты для работы в приложении.

## Stack
- Backend/frontend/database: уточнить по репозиторию и серверу при следующем техническом заходе.
- MCP: подключен в Hermes как `prostye_postavki`.
- Infra: публичная точка `miramed32.ru`; серверные секреты будут дозаполнены отдельно.

## Key URLs (non-secret)
- Repo: https://github.com/xotizwf-create/prostavki
- MCP endpoint without secret segment: https://miramed32.ru/mcp

## Current state
Активный критически важный проект. MCP доступен из текущего Hermes-профиля. Живой production-код находится в `/var/www/prostye-postavki/app` и связан с GitHub-репозиторием `xotizwf-create/prostavki`; пустой репозиторий `xotizwf-create/prostye-postavki` не является источником production-кода. Перед любыми серверными действиями сначала проверить доступы в secure-зоне и выполнить обязательный server preflight.
