import sqlite3, json, time, datetime
conn = sqlite3.connect("file:/root/.hermes/state.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
since = time.time() - 12 * 3600
rows = conn.execute(
    "SELECT id, session_id, role, tool_name, timestamp, tool_calls, token_count, "
    "substr(COALESCE(content,''),1,150) AS c FROM messages WHERE timestamp > ? ORDER BY id",
    (since,),
).fetchall()
print("messages last 12h:", len(rows))
sess = {}
for r in rows:
    sess[r["session_id"]] = sess.get(r["session_id"], 0) + 1
print("sessions:", sess)
def fmt(ts):
    return datetime.datetime.utcfromtimestamp(ts).strftime("%H:%M:%S")
for sid, n in sorted(sess.items(), key=lambda kv: -kv[1])[:2]:
    print(f"\n===== session {sid} ({n} msgs) =====")
    prev = None
    for r in rows:
        if r["session_id"] != sid:
            continue
        tools = ""
        if r["tool_calls"]:
            try:
                calls = json.loads(r["tool_calls"])
                tools = ",".join(c.get("function", {}).get("name", "?") for c in calls)
            except Exception:
                tools = str(r["tool_calls"])[:60]
        gap = f"+{int(r['timestamp']-prev):>4}s" if prev else "     "
        prev = r["timestamp"]
        body = (r["tool_name"] or tools or "")
        print(f"{fmt(r['timestamp'])} {gap} | {r['role']:9} | {body[:55]:55} | {r['c'][:60]!r}")
