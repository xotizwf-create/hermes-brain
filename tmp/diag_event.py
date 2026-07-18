#!/usr/bin/env python3
"""Diagnose why the bound OnTaskCommentAdd didn't produce a reply: check the seen table and
replay the extraction on a freshly-created comment via a synthetic-but-realistic payload."""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, "/var/www/albery")
from dotenv import load_dotenv  # noqa: E402
load_dotenv("/var/www/albery/.env")
import app  # noqa: F401  (import app first — circular-import rule)
import bitrix
import b24bot
from shared.db import connect

WH = os.environ["BITRIX_WEBHOOK_BASE"].rstrip("/")


def wh(method, payload):
    req = urllib.request.Request(f"{WH}/{method}.json", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


with connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT comment_id, task_id, agent_slug, author_id, handled, created_at "
                    "FROM bitrix_task_comment_seen ORDER BY created_at DESC LIMIT 5")
        print("seen rows:", [dict(r) for r in cur.fetchall()])

# Create a task+comment and test the extraction + fetch directly
r = wh("tasks.task.add", {"fields": {"TITLE": "[diag] event extract", "RESPONSIBLE_ID": 16, "CREATED_BY": 16}})
tid = ((r.get("result") or {}).get("task") or {}).get("id")
c = wh("task.commentitem.add", {"TASKID": tid, "FIELDS": {"POST_MESSAGE": "Албери, тест", "AUTHOR_ID": 16}})
cid = c.get("result")
print("task", tid, "comment", cid)
time.sleep(2)
try:
    # simulate the two flattened event shapes Bitrix sends
    for shape in (
        {"event": "ONTASKCOMMENTADD", "data[FIELDS_AFTER][ID]": str(cid), "data[FIELDS_AFTER][TASK_ID]": str(tid)},
        {"event": "ONTASKCOMMENTADD", "data[FIELDS_BEFORE][ID]": str(cid), "data[FIELDS_AFTER][TASK_ID]": str(tid)},
    ):
        etid = bitrix.extract_bitrix_comment_event_task_id(shape)
        ecid = bitrix._extract_bitrix_event_comment_id(shape)
        print("extract:", {"task": etid, "comment": ecid})

    fetched = b24bot._b24_fetch_task_comment(int(tid), int(cid))
    print("fetch_task_comment:", fetched)
    if fetched:
        print("pick_agent:", (b24bot._b24_task_pick_agent(fetched["text"]) or {}).get("name"))
        print("main_allows(16):", b24bot._b24_main_allows(16))
finally:
    wh("tasks.task.delete", {"taskId": tid})
    print("deleted")
