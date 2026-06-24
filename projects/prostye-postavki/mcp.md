# MCP-инструкции и навигация

## Где живёт канон

Канонический источник встроенных MCP-инструкций проекта «Простые поставки» находится в production-репозитории:

- `backend/app/mcp_prompts.py` — тексты prompt’ов и их метаданные;
- `backend/app/main.py` — регистрация MCP-инструментов и обработчиков;
- `agent.md` в репозитории проекта — краткая инструкция для оператора/агента.

Не дублируй полный текст prompt’ов в Hermes brain: сначала смотри этот файл, затем читай актуальный prompt через MCP.

## Инструменты навигации

Для быстрого выбора инструкции используй read-only MCP-инструменты:

| Инструмент | Когда использовать |
|---|---|
| `list_mcp_prompt_topics` | Показать карту доступных MCP-инструкций: название, категория, ключевые слова, когда читать |
| `search_mcp_prompts` | Найти нужную инструкцию по словам вроде «КП», «Интеко», «входящий договор», «ИНН», «остатки» |
| `get_mcp_prompt` | Прочитать полный текст выбранной инструкции перед выполнением профильной задачи |

Общий порядок:

1. Если задача новая или неочевидная — вызвать `list_mcp_prompt_topics` или `search_mcp_prompts`.
2. Перед выполнением профильной операции прочитать полный prompt через `get_mcp_prompt`.
3. Для коммерческих предложений обязательно читать `commercial_offer_workflow`.
4. Для входящих договоров/контрактов обязательно читать `incoming_contract_processing`.
5. Для общих вопросов по остаткам, контрактам, поставкам, организациям и инструментам начинать с `prostavki_operator_guide`.

## Как добавлять новую инструкцию

1. В `backend/app/mcp_prompts.py` добавить текст prompt’а и запись в `MCP_PROMPTS`.
2. В записи заполнить:
   - `name` — стабильный машинный id;
   - `title` — короткое человеческое название;
   - `category` — группа сценариев;
   - `description` — что это за инструкция;
   - `keywords` — слова для поиска;
   - `use_when` — когда читать;
   - `read_first` — `true` только для стартового общего гайда;
   - `text` — полный текст prompt’а.
3. Не хардкодить список prompt’ов в schema `get_mcp_prompt`: enum должен строиться из `list(MCP_PROMPTS.keys())`.
4. Если появляется новый сценарий, добавить ключевые слова так, чтобы `search_mcp_prompts` находил его по обычному языку владельца.
5. Проверить:
   - синтаксис Python;
   - `list_mcp_prompt_topics()` возвращает новый prompt;
   - `search_mcp_prompts(<живой запрос>)` ставит нужный prompt в верх выдачи;
   - live MCP `tools/list` видит новые/изменённые инструменты после перезапуска backend.

## Текущая реализация

Добавлена в коммите проекта `cfb40e2 Add MCP prompt navigation tools` на ветке `fix/incoming-paste-single-cell`.

Проверено на production backend:

- Python-синтаксис `backend/app/mcp_prompts.py` и `backend/app/main.py` проходит;
- поиск по «КП Грин Интеко медицинские товары» возвращает `commercial_offer_workflow` первым;
- поиск по «ИНН входящий договор OCR» возвращает `incoming_contract_processing` первым;
- live MCP `tools/list` содержит `list_mcp_prompt_topics`, `search_mcp_prompts`, `get_mcp_prompt`;
- live MCP-вызов `search_mcp_prompts` работает через HTTP endpoint backend.
