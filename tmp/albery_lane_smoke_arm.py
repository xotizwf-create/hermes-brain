# Arm a live-lane smoke: schedule a SILENT automation ~2 minutes from now for the MAIN
# agent; the RUNNING SERVICE (scheduler -> queue -> worker) must pick it up on its own.
from datetime import timedelta

import app  # noqa: F401
from app import msk_now, pg_connect

t = msk_now() + timedelta(minutes=2)
sched = f"{t.minute} {t.hour} * * *"
with pg_connect() as conn:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("DELETE FROM agent_automations WHERE name = '__lane_smoke__'")
            cur.execute(
                "INSERT INTO agent_automations (agent_slug, name, schedule, prompt, kind, created_by, creator_label) "
                "VALUES ('main', '__lane_smoke__', %s, "
                "'Это тестовый запуск конвейера. Никаких инструментов не вызывай. Ответь ровно одним словом SILENT.', "
                "'agent', 'owner', 'smoke') RETURNING id",
                (sched,),
            )
            print("armed id", cur.fetchone()["id"], "schedule", sched, "now", msk_now().strftime("%H:%M:%S"))
