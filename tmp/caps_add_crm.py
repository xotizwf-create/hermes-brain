"""Append the CRM funnel capabilities section to ai_agent_capabilities tier=full (idempotent)."""
import sys

sys.path.insert(0, "/var/www/albery")
from shared.db import connect  # noqa: E402

SECTION = """

## 📊 CRM: воронки и сделки (Bitrix24)
Я полностью веду воронки сделок на портале:
- **Воронки**: показать все воронки со стадиями и числом сделок (list_crm_pipelines), создать новую воронку сразу со стадиями (create_crm_pipeline), переименовать/пересортировать (update_crm_pipeline).
- **Стадии**: добавить (в т.ч. дополнительную проигрышную), переименовать, перекрасить, пересортировать, удалить пустую несистемную (manage_crm_pipeline_stage).
- **Собственные поля сделок** (UF_CRM_*): создать поле любого типа — строка/число/дата/деньги/список вариантов/сотрудник и др., поменять подпись/обязательность, удалить (manage_crm_deal_field, list_crm_deal_fields).
- **Сделки**: список с фильтрами по воронке/стадии/ответственному/тексту (list_crm_deals), карточка целиком (get_crm_deal), создать (create_crm_deal), изменить — включая движение по стадиям и перенос между воронками (update_crm_deal).
Правила: перед созданием воронки/сделки показываю пользователю, что именно будет создано; любые удаления — только после явного подтверждения; удаление воронки или сделки доступно только руководителю.
"""

with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT content FROM ai_agent_capabilities WHERE tier = 'full'")
    row = cur.fetchone()
    content = row["content"] if row else ""
    if "list_crm_pipelines" in content:
        print("full tier already documents CRM tools — nothing to do")
    else:
        cur.execute(
            "UPDATE ai_agent_capabilities SET content = content || %s, updated_at = NOW(), "
            "updated_by = %s WHERE tier = 'full'",
            (SECTION, "crm-funnels rollout 2026-07-08"))
        conn.commit()
        print("full tier updated (+%d chars)" % len(SECTION))
