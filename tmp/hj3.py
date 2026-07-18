import sqlite3, json, time
conn = sqlite3.connect("file:/root/.hermes/state.db?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", tables[:30])
# find a messages-like table
for t in tables:
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})")]
    if any("content" in c for c in cols) and any("role" in c or "type" in c for c in cols):
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(t, cols, cnt)
