---
id: prostye-postavki-overview
type: project
project: prostye-postavki
tags: [overview]
updated: 2026-07-09
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
- Договоры по шаблону (2026-07-09): выгрузка существующего DOCX-договора как шаблона и быстрая
  генерация нового (№ = дата создания, преамбула без ФЗ, спецификация/приложения по данным
  пользователя) — см. `mcp.md`, prompt `contract_from_template_workflow`.
- MCP-сервер содержит инструкции и инструменты для работы в приложении.

## Stack (confirmed 2026-06-11 from the repo)
- **Backend: FastAPI** (single `backend/app/main.py`, ~12.6k lines), `uvicorn`, `psycopg` (Postgres),
  `python-docx`, `Pillow`. Entry `backend/app/main.py:app`. ⚠ Earlier docs/`registry.yaml` said
  "Flask" — that was wrong, it's FastAPI. Module import runs `ensure_*_schema()` against the DB at
  load time (needs a live `DATABASE_URL`), so the app cannot be imported without Postgres.
- **Frontend: React + Vite** (TypeScript), build → `dist/`, tests via `vitest`.
- **Database: PostgreSQL** (`psycopg[binary]`, pooled via a custom `get_conn()` context manager).
- **CI (added 2026-06-11):** `.github/workflows/ci.yml` — backend smoke (Postgres service) +
  frontend build + non-blocking legacy vitest. See `engineering/testing.md` for the pattern. Two
  legacy frontend parsing tests (`contractParsing`/`specPipeline`) are pre-existing failures awaiting triage.
- MCP: подключен в Hermes как `prostye_postavki`.
- Infra: публичная точка `miramed32.ru`; серверные секреты будут дозаполнены отдельно.

## Key URLs (non-secret)
- Repo: https://github.com/xotizwf-create/prostavki
- MCP endpoint without secret segment: https://miramed32.ru/mcp

## Current state
Активный критически важный проект. MCP доступен из текущего Hermes-профиля. Живой production-код находится в `/var/www/prostye-postavki/app` и связан с GitHub-репозиторием `xotizwf-create/prostavki`; пустой репозиторий `xotizwf-create/prostye-postavki` не является источником production-кода. Перед любыми серверными действиями сначала проверить доступы в secure-зоне и выполнить обязательный server preflight.
