---
id: prostye-postavki-incidents
type: project
project: prostye-postavki
tags: [incidents]
updated: 2026-06-15
secret_refs: []
---

# Простые поставки — incidents

## 2026-06-15 — импортированные входящие контракты показывали нулевую цену

Симптом: после обработки входящих документов MCP/экран карточки контракта показывал корректное количество, но `items[].price = 0`, потому что `form_snapshot.items` у импортера мог хранить `price` как цену за единицу, а `_assemble_contract_out` ожидал UI-формат: `price` = количество, `total` = цена за единицу.

Что сделано на production `miramed32`, checkout `/var/www/prostye-postavki/app`:
- точечно нормализованы две карточки: `Контракт №424` и `Контракт №0363300044326000058`;
- backend `backend/app/main.py` научен принимать оба формата snapshot и брать цену из `price`, если `total` пустой, но в строке есть отдельное количество;
- коммит в canonical repo: `93fd160 Handle imported contract item price fallback`.

Проверка: `get_contracts`/`fetch` по обоим контрактам возвращают ненулевые цены в `items[].price`; очередь необработанных входящих документов пустая.
