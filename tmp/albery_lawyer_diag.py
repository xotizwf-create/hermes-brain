# Diagnose the lawyer agent's recent failed task: last turns + errors (run with PYTHONPATH=/var/www/albery).
import app  # noqa: F401
from app import pg_connect

with pg_connect() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, dialog_id, created_at, status, error, latency_ms, "
            "       left(question, 160) AS q, left(answer, 220) AS a "
            "FROM bitrix_bot_interactions WHERE agent_slug = 'agent-sklad' "
            "ORDER BY id DESC LIMIT 12"
        )
        for r in cur.fetchall():
            print("—", r["id"], str(r["created_at"])[:19], r["status"],
                  f"{(r['latency_ms'] or 0)//1000}s",
                  ("ERR: " + (r["error"] or "")[:200]) if r["error"] else "")
            print("  Q:", (r["q"] or "").replace("\n", " ")[:150])
            print("  A:", (r["a"] or "").replace("\n", " ")[:200])
