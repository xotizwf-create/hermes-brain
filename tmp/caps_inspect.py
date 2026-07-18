"""Inspect ai_agent_capabilities structure + tail of the full-tier content (read-only)."""
import sys

sys.path.insert(0, "/var/www/albery")
from shared.db import connect  # noqa: E402

with connect() as conn, conn.cursor() as cur:
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns
                   WHERE table_name = 'ai_agent_capabilities' ORDER BY ordinal_position""")
    print([f"{r['column_name']}:{r['data_type']}" for r in cur.fetchall()])
    cur.execute("SELECT * FROM ai_agent_capabilities")
    for r in cur.fetchall():
        body = str(r.get("content") or r.get("capabilities") or "")
        print("---", {k: v for k, v in r.items() if k not in ("content", "capabilities")},
              "len:", len(body))
        print("TAIL:", body[-700:])
