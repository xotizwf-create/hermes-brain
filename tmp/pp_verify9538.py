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
rows = call("read_table_rows", {"table": "contracts", "search": "9538", "limit": 5})
for r in rows.get("rows", []):
    print("number:", r.get("contract_number"), "| status:", r.get("status"), "| deadline:", r.get("delivery_deadline"), "| signed:", r.get("signed_date"))
    items = r.get("items_json") or []
    if isinstance(items, str): items = json.loads(items)
    total = 0
    for it in items:
        s = float(it.get("count",0))*float(it.get("price",0)); total += s
        print(f"  - {it.get('name','')[:60]!r} | unit={it.get('unit')} | qty={it.get('count')} | price={it.get('price')} | sum={s}")
    print("  TOTAL:", round(total,2))
    cid = r.get("id")
    files = call("get_contract_files", {"contractId": str(cid)})
    print("  attached files:", [(f["filename"], f["isDocx"]) for f in files["files"]])
docs = call("list_incoming_contract_documents", {})
print("incoming left:", [(d["filename"], d["processed"]) for d in docs["documents"]])
