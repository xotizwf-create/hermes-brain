import json, urllib.request
from pathlib import Path
APP = Path("/var/www/prostye-postavki/app")
secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
URL = f"http://127.0.0.1:8000/mcp/{secret}"
def call(name, arguments):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":arguments}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        p = json.loads(resp.read().decode())
    if "error" in p: raise RuntimeError(p["error"])
    return json.loads(p["result"]["content"][0]["text"])
for q in ("LUM", "Унеч"):
    rows = call("read_table_rows", {"table": "contracts", "search": q, "limit": 30})
    print(f"=== search {q!r}: {len(rows.get('rows', []))} rows ===")
    for r in rows.get("rows", []):
        items = r.get("items_json") or []
        if isinstance(items, str): items = json.loads(items)
        fs = r.get("form_snapshot") or {}
        if isinstance(fs, str): fs = json.loads(fs)
        stages = fs.get("planStages") or []
        print(f"- {r.get('contract_number')!r} | signed {r.get('signed_date')} | deadline {r.get('delivery_deadline')} | status {r.get('status')} | planStages: {len(stages)}")
        for it in items[:4]:
            print(f"    item: {str(it.get('name'))[:45]!r} qty={it.get('count')} price={it.get('price')} planDate={it.get('planDate')!r} planQty={it.get('planQty')}")
