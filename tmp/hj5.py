import sqlite3, json, time, datetime
conn = sqlite3.connect("file:/root/.hermes/state.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
since = time.time() - 2 * 3600
rows = conn.execute(
    "SELECT id, session_id, role, tool_name, timestamp, tool_calls, "
    "substr(COALESCE(content,''),1,200) AS c FROM messages WHERE timestamp > ? ORDER BY id",
    (since,),
).fetchall()
sess = {}
for r in rows:
    sess.setdefault(r["session_id"], []).append(r)
for sid, msgs in sess.items():
    print(f"\n===== {sid} ({len(msgs)} msgs) =====")
    for r in msgs:
        tools = ""
        if r["tool_calls"]:
            try:
                calls = json.loads(r["tool_calls"])
                tools = ",".join(c.get("function", {}).get("name", "?")[:45] for c in calls)
            except Exception:
                tools = "?"
        ts = datetime.datetime.utcfromtimestamp(r["timestamp"]).strftime("%H:%M:%S")
        print(f"{ts} | {r['role']:9} | {(r['tool_name'] or tools or '')[:60]:60} | {r['c'][:80]!r}")
