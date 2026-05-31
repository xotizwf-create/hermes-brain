---
id: gov-exams-app-overview
type: project
project: gov-exams-app
tags: [overview]
updated: 2026-05-31
secret_refs: []
---

# Лёгкие экзамены / LiteExams — overview

## What it is
«Лёгкие экзамены» / LiteExams — критически важный платный сервис подготовки к госэкзаменам КФУ. В сервисе есть база вопросов, пользователи, подписки и токены устройств; эти данные нельзя ломать, терять или массово менять без явного плана и резервной копии.

## Core capabilities
- Подготовка студентов к госэкзаменам КФУ.
- Платная подписка.
- База вопросов и пользовательские данные.
- Механизм токенов/привязок устройств для мобильного и ПК-доступа.
- Подключён MCP-сервер `gov_exams_tokens` для безопасной ротации токенов без раскрытия значений.

## Stack
- Frontend/backend: уточнить по репозиторию; известно, что для проекта применяются Node/Vite-сборки.
- Database: production database with sensitive user/subscription/token data.
- Infra: production host/domain `liteexams.ru`.

## Key URLs (non-secret)
- Web/domain: https://liteexams.ru
- Repo: https://github.com/xotizwf-create/gov-exams-app
- MCP: current Hermes has local/stdio `gov_exams_tokens`; HTTP URL `https://liteexams.ru/mcp` is not confirmed.

## Current state
Активный критически важный проект. Серверные секреты добавлены в secure-зону. Production host is memory-constrained; build and full checks should be done off-server, with only lightweight smoke checks on production.
