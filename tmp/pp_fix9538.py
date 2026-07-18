"""Fix contract 9538: overwrite the owner's card with correct data (incl. computed deadline),
then remove the duplicate created by the agent test. Runs on miramed32."""
import json, urllib.request
from pathlib import Path
APP = Path("/var/www/prostye-postavki/app")
KEEP = "7010a609-21f0-4c3c-80eb-678372caeae7"   # owner's card (created via UI 15:07 MSK)
DUP = "752eec83-74b1-429f-bfc7-75f752125fb1"    # agent-test duplicate (23:11 MSK)
env = {}
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"')
URL = f"http://127.0.0.1:8000/mcp/{env['MCP_SERVER_SECRET']}"
def call(name, arguments):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":arguments}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        p = json.loads(resp.read().decode())
    if "error" in p: raise RuntimeError(p["error"])
    return json.loads(p["result"]["content"][0]["text"])

# item full names from the agent's extraction (kept in the dup row)
import psycopg
db_url = (env.get("DATABASE_URL") or "").replace("postgresql+psycopg2://", "postgresql://")
with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT items_json FROM contracts WHERE id = %s", (DUP,))
        items_json = cur.fetchone()[0]
items = items_json if isinstance(items_json, list) else json.loads(items_json)
extracted_items = [
    {"name": it["name"], "docName": it.get("docName") or it["name"], "unit": it.get("unit") or "шт",
     "qty": it.get("count"), "price": it.get("price")}
    for it in items
]
res = call("save_contract_from_incoming_document", {
    "contractId": KEEP,
    "extracted": {
        "contractNumber": "Контракт №9538",
        "contractDate": "10.07.2026",
        "deadlineDays": 21,
        "deadlineDaysType": "calendar",
        "deadlineText": "в течение 21 календарного дня со дня подписания договора",
        "customerInn": "6722011027",
        "supplierInn": "519015986470",
        "vatPercent": "5",
        "items": extracted_items,
    },
})
print("overwrite:", res["status"], "| deadlineSaved:", res.get("deadlineSaved"), "| total:", res.get("totalAmount"))
print("warnings:", res.get("sumWarnings"))
lo = res["linkedOrganizations"]
print("customer:", lo["customer"]["name"][:40], lo["customer"]["isPlaceholder"], "| supplier:", lo["supplier"]["name"][:40], lo["supplier"]["isPlaceholder"])
assert res["status"] == "updated" and res.get("deadlineSaved"), res

# remove the duplicate (agent-test artifact)
with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT storage_key FROM contract_files WHERE contract_id = %s", (DUP,))
        for (key,) in cur.fetchall():
            p = (APP / key).resolve()
            if "contract_files_store" in str(p) and p.exists():
                p.unlink()
        cur.execute("DELETE FROM inventory_movements WHERE contract_id = %s", (DUP,))
        cur.execute("DELETE FROM delivery_stage_items WHERE stage_id IN (SELECT id FROM delivery_stages WHERE contract_id = %s)", (DUP,))
        cur.execute("DELETE FROM delivery_stages WHERE contract_id = %s", (DUP,))
        cur.execute("DELETE FROM contract_items WHERE contract_id = %s", (DUP,))
        cur.execute("DELETE FROM contract_files WHERE contract_id = %s", (DUP,))
        cur.execute("DELETE FROM contracts WHERE id = %s", (DUP,))
    conn.commit()
print("duplicate removed")
rows = call("get_contracts", {"query": "9538", "limit": 10})
print("contracts named 9538 now:", rows.get("count") or len(rows.get("contracts") or rows.get("rows") or []))
