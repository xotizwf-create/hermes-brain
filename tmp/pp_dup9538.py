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
    if "9538" not in str(r.get("contract_number","")): continue
    fs = r.get("form_snapshot") or {}
    if isinstance(fs, str): fs = json.loads(fs)
    print("id:", r.get("id"))
    print("  created:", r.get("created_at"), "| updated:", r.get("updated_at"), "| status:", r.get("status"))
    print("  deadline:", r.get("delivery_deadline"), "| fs.deadline:", fs.get("deadline"), "| fs.contractDate:", fs.get("contractDate"), "| fs.number:", fs.get("number"))
    print("  comment:", str(r.get("comment") or "")[:120])
