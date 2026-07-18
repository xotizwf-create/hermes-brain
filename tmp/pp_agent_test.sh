#!/usr/bin/env bash
# Live agent test: process the real incoming contract via the prostye MCP toolset only.
set -uo pipefail
timeout 540 hermes -z 'Обработай входящий документ «9538 садовый инвентарь.pdf» и занеси контракт в базу. Действуй строго по MCP prompt incoming_contract_processing: прочитай его через get_mcp_prompt, посмотри документ сам (view_incoming_contract_document, точечные страницы), заполни ВСЕ обязательные ячейки сам из документа (не из автораспознавания) и создай контракт одним вызовом save_contract_from_incoming_document с полным extracted. Используй ТОЛЬКО инструменты prostye_postavki. В конце кратко перечисли: номер, дату, дедлайн, заказчика и поставщика с ИНН, позиции с количеством и ценой, итоговую сумму.' -t prostye_postavki 2>&1 | tail -60
