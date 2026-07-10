---
id: learning-log
type: log
tags: [learning]
updated: 2026-05-30
secret_refs: []
---

# Learning log

Append-only, newest on top. Durable lessons that improve future work (patterns that worked,
gotchas, preferences confirmed in practice). Link to the file they refine.

## 2026-05-30 — two-way git brain sync is live (verified from the server)
- The prod brain `/root/.hermes/agent-knowledge` is now a git clone of `hermes-brain` (deploy key
  `hermes_brain_deploy`, read-write). This entry was authored and pushed **from the server** to
  verify the self-scaling pipeline end-to-end. Hermes can now edit → validate → (Telegram approval)
  → commit → push; the local copy pulls. See `skills/update-knowledge`.


## 2026-07-11 — Марафон «Простые поставки»: MCP-инструменты как рычаг эффективности ИИ

**Главный урок: агент становится супер-эффективным не от «умного промпта», а от ИНСТРУМЕНТОВ.**
Под каждую боль владельца — MCP-инструмент: сервер делает механику детерминированно (валидация
обязательных ячеек, вычисление дедлайнов из фраз, привязка организаций по ИНН через DaData,
клонирование файлов, суммы прописью, cp1251-санитизация для легаси), агент делает только своё —
читает документ, извлекает, решает, спрашивает. Итог трёх дней: ~15 инструментов, 4 конвейера
(интейк, договор по шаблону, графики поставок, сводка), обработка договора сократилась с 10+ минут
и ~20 вызовов до 2–4 вызовов. Полный дизайн-гайд: `engineering/mcp-tool-design.md`; проектные
детали: `projects/prostye-postavki/mcp.md`.

Ключевые под-уроки:
- Ответ инструмента = самодостаточная вериф-проверка (снапшот) → без контрольных чтений.
- Легаси-схему объявлять в ответе («это НЕ баг») — иначе агент чинит норму и дебажит прод по SSH.
- Антивыдумывание: не видишь страницы — стоп и доклад; vision у Hermes режется `-t`-ограничением.
- Тестировать ЖИВЫМ агентом на реальных данных (dry-run для рискованного) + сверять с
  первоисточником своими глазами; бэкенд-тесты не ловят потерю полей и конфабуляцию.
- Жизненный цикл данных = часть контракта инструмента (документ израсходуется → призраков не
  создавать, перезапись по contractId).
- Деплой: import-check ДО рестарта (декоратор/def — упали дважды), рестарт hermes-gateway после
  каждого деплоя бэкенда (MCP-коннект умирает навсегда за ~30с недоступности).
