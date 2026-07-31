# -*- coding: utf-8 -*-
import os, sys
os.environ["B24_TASK_OFFER"] = "0"
os.environ["B24_TASK_CHECKIN"] = "0"
sys.path.insert(0, "/var/www/albery")
from mcp import context_server as cs

title = "Albery: замороженный набор инструментов агента не может уметь «создать», но не «изменить»"
description = (
    "[b]Контекст[/b]\n"
    "У агента есть три слоя, отделяющих инструмент от модели: реестр TOOLS, компактный CORE "
    "(подаётся каждый ход) и БЕЛЫЙ СПИСОК самого агента в таблице agents. Третий слой — жёсткие "
    "ворота: `_agent_tool_names` в agent_center.py, и tools/list по коннектору агента отдаёт ровно "
    "этот список. Если набор агента когда-то настраивали в карточке (tools_customized=true), список "
    "заморожен на момент настройки и новые инструменты в него не попадают.\n\n"
    "[b]Следствия[/b]\n"
    "После задач 2376 и 2378 инструменты read_google_doc / edit_google_doc были в реестре, в CORE и "
    "в OPS, живая служба отдавала их на всех четырёх общих коннекторах (/mcp 155, /mcp-ops 133, "
    "/mcp-core 58, /mcp-ops-core 57). Владелец 30.07 в диалоге 16 всё равно получил отказ (ход 1325): "
    "«Напрямую редактировать существующий Google Документ по ссылке я сейчас не умею: в текущем "
    "наборе нет действия для записи изменений в него».\n"
    "Проверка белых списков показала асимметрию у ПЯТИ агентов: main (115 имён), agent-finansist "
    "(102), agent-po-rabote-s-iu (129), agent-sklad (101), albery-ai-bot (119) — во всех есть "
    "create_google_doc и ни в одном нет read_google_doc / edit_google_doc.\n"
    "Дальше агент пошёл в обход через Apps Script (ход 1326): применил Roboto 14 pt и жирный на "
    "первых трёх вопросах, получил блокировку Google и написал «Продолжаю правки напрямую в "
    "документе вручную» — действие, которого он выполнить не может. То есть асимметрия набора "
    "порождает и брошенную на середине работу, и ложное обещание.\n\n"
    "[b]Требование[/b]\n"
    "Набор, в котором есть «создать», обязан содержать «прочитать» и «изменить». Точечная дописка "
    "имён в БД не годится: она чинит сегодня и снова ломается на следующем новом инструменте."
)
result_criteria = (
    "Коннектор агента main отдаёт read_google_doc и edit_google_doc; асимметрия «создать без "
    "изменить» невозможна для любого агента и любого будущего инструмента; кап манифеста строгих "
    "клиентских агентов не расширяется; поведение закреплено тестом."
)
result_text = (
    "[b]Реализовано[/b]\n"
    "1. В agent_center.py введён инвариант `_TOOL_COMPANIONS` + `_with_companion_tools`: набор, "
    "содержащий create_google_doc, замыкается на read_google_doc и edit_google_doc; содержащий "
    "create_google_sheet — на get_google_sheet_meta, read_google_sheet_values, "
    "write_google_sheet_values.\n"
    "2. Замыкание применяется в `_agent_tool_names` к белому списку ДО пересечения с разрешённым "
    "пулом, поэтому кап манифеста строгих клиентских агентов оно не обходит, а агенту без "
    "create_google_doc ничего не добавляется.\n"
    "3. То же замыкание применяется при сохранении набора в карточке агента, чтобы галочки в "
    "интерфейсе совпадали с тем, что реально отдаёт коннектор.\n\n"
    "[b]Проверка[/b]\n"
    "Тест tests/unit/test_agent_tool_symmetry.py — 6 проверок, включая реальный белый список main и "
    "защиту капа; на старом коде падал ровно на случае владельца. Ворота "
    "scripts/predeploy_check.py: 1674 passed, 27 skipped.\n"
    "На проде после деплоя и рестарта в пустое окно (bitrix_inflight_turns=0):\n"
    "  main                 117 инстр. create_doc=True read_doc=True edit_doc=True\n"
    "  agent-finansist      104        True/True/True\n"
    "  agent-sklad          103        True/True/True\n"
    "  agent-po-rabote-s-iu 131        True/True/True\n"
    "  iu-customer-runtime    0        не расширился (кап манифеста = 0)\n"
    "Сквозная проверка через РЕАЛЬНЫЙ коннектор модели /mcp-agent/main/<token>: tools/list = 123 "
    "инструмента, edit_google_doc присутствует; живой вызов read_google_doc на том самом документе "
    "из жалобы («Ответы на частые вопросы») вернул OK.\n"
    "Заодно подтверждено, что поведенческое правило доезжает: инжект 17 193 символа, блок «Вопросы "
    "о возможностях и доступе» в списке, формулировки «у вас не тот уровень прав» в инжекте больше "
    "нет.\n\n"
    "[b]Коммит[/b]\n"
    "f1bf95f — https://github.com/xotizwf-create/Albery/commit/f1bf95f\n"
    "Третий случай одного класса за сутки (после 2378 и 2380): возможность есть, но модель её не "
    "видит. Продолжение задач 2376 и 2378.\n\n"
    "[b]Откат[/b]\n"
    "git revert f1bf95f; бэкап /var/backups/albery/code/pre-toolsymmetry-*.tar.gz\n\n"
    "[b]Обнаружено попутно, НЕ входит в эту правку[/b]\n"
    "У агентов albery-ai-bot и iu-customer-runtime манифест задаёт tools: [] → кап 0, коннектор "
    "отдаёт ноль инструментов. В журнале hermes-gateway при этом каждые 2 минуты: «MCP server "
    "'agent-albery-ai-bot' still down», то же для 'agent-albery-ai-manager'. Требует отдельного "
    "разбора."
)

created = cs.tool_create_bitrix_task({
    "title": title, "description": description,
    "responsible_bitrix_user_id": 16, "creator_bitrix_user_id": 22,
    "deadline": "2026-07-30T11:35:00+03:00",
    "result_criteria": result_criteria,
    "confirm_past_deadline": True,
})
tid = created.get("task_id")
done = cs.tool_complete_bitrix_task({
    "bitrix_task_id": tid, "on_behalf_bitrix_user_id": 22,
    "expected_title": title, "result_text": result_text,
})
info = (done or {}).get("result") or {}
print("задача", tid, "закрыта; comment_id =", info.get("comment_id"))
print("https://albery.bitrix24.ru/company/personal/user/16/tasks/task/view/%s/" % tid)
