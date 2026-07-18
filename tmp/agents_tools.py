"""Inspect agents + their enabled tools on prod (read-only)."""
import sys

sys.path.insert(0, "/var/www/albery")
from shared.db import connect  # noqa: E402

with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT id, slug, name, is_active, tools FROM agents ORDER BY id")
    for r in cur.fetchall():
        tools = r["tools"] or []
        crm = [t for t in tools if "crm" in str(t)]
        task = [t for t in tools if "bitrix_task" in str(t)]
        print(f"id={r['id']} slug={r['slug']!r} name={r['name']!r} active={r['is_active']} "
              f"tools={len(tools)} task_tools={len(task)} crm_tools={crm}")
