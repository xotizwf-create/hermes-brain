"""Verify loop safety after the replay: both agent-created comments are claimed in dedupe."""
import sys

sys.path.insert(0, "/var/www/albery")
from shared.db import connect  # noqa: E402

with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT comment_id, task_id, agent_slug, handled FROM bitrix_task_comment_seen "
                "WHERE task_id = 1254 ORDER BY comment_id")
    for r in cur.fetchall():
        print(dict(r))
