"""Where did the digest get cut: last_result vs stored digest vs delivered chat message."""
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402
from shared.db import connect  # noqa: E402

with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT length(last_result) AS n, right(last_result, 300) AS tail FROM agent_automations WHERE id=37")
    r = dict(cur.fetchone())
    print("last_result len:", r["n"])
    print("last_result tail:", r["tail"])
    cur.execute("SELECT id, length(summary) AS n, right(summary, 300) AS tail FROM tg_news_digests ORDER BY created_at DESC LIMIT 1")
    d = dict(cur.fetchone())
    print("\nstored digest id:", d["id"], "len:", d["n"])
    print("digest tail:", d["tail"])

endpoint, token = b24bot._b24_app_access_token()
data = b24bot._b24_app_call(endpoint, token, "im.dialog.messages.get", {"DIALOG_ID": "16", "LIMIT": 2})
for m in sorted((data.get("result") or {}).get("messages") or [], key=lambda x: int(x.get("id") or 0)):
    text = str(m.get("text") or "")
    print(f"\nchat msg [{m.get('id')}] len={len(text)} tail: …{text[-250:]}")
