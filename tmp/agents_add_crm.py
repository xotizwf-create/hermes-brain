"""Additively enable the CRM funnel tools for the prod agents (idempotent).
main -> all 12 (incl. the two owner-class deletes, it already carries delete_bitrix_task);
финансист/юрист -> the 10 non-destructive ones. dev agent is not touched."""
import json
import sys

sys.path.insert(0, "/var/www/albery")
from shared.db import connect  # noqa: E402

SAFE = [
    "list_crm_pipelines", "create_crm_pipeline", "update_crm_pipeline",
    "manage_crm_pipeline_stage", "list_crm_deal_fields", "manage_crm_deal_field",
    "list_crm_deals", "get_crm_deal", "create_crm_deal", "update_crm_deal",
]
DESTRUCTIVE = ["delete_crm_pipeline", "delete_crm_deal"]
PLAN = {
    "main": SAFE + DESTRUCTIVE,
    "agent-finansist": SAFE,
    "agent-sklad": SAFE,
}

with connect() as conn, conn.cursor() as cur:
    for slug, add in PLAN.items():
        cur.execute("SELECT tools FROM agents WHERE slug = %s", (slug,))
        row = cur.fetchone()
        if not row:
            print(f"{slug}: NOT FOUND, skipped")
            continue
        tools = list(row["tools"] or [])
        new = [t for t in add if t not in tools]
        if not new:
            print(f"{slug}: already has all ({len(tools)} tools)")
            continue
        tools.extend(new)
        cur.execute("UPDATE agents SET tools = %s::text[] WHERE slug = %s", (tools, slug))
        print(f"{slug}: +{len(new)} -> {len(tools)} tools ({', '.join(new)})")
    conn.commit()
print("done")
