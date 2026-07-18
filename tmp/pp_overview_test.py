"""Read-only test of get_contracts_overview on real data (miramed32)."""
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

ov = call("get_contracts_overview", {"limit": 5})
print("statusCounts:", ov["statusCounts"], "| total:", ov["totalContracts"], "| shown:", ov["shown"])
for c in ov["contracts"][:3]:
    print(f"- {c['number'][:40]!r} {c['status']} deadline={c['deadline']} total={c['totalAmount']} docsSent={c['docsSent']} docsCreated={c['documentsCreated']}")
    for d in c["documents"][:4]:
        print(f"    doc: {d['typeName']} №{d['number']} этап {d['stageNumber']} от {d['createdAt']}")

wd = call("get_contracts_overview", {"hasDocuments": True, "limit": 5})
print("\nс документами:", wd["shown"])
for c in wd["contracts"][:3]:
    print(f"- {c['number'][:40]!r}: " + "; ".join(f"{d['typeName']} №{d['number']}" for d in c["documents"][:3]))

nd = call("get_contracts_overview", {"hasDocuments": False, "status": "active", "limit": 5})
print("\nактивные БЕЗ документов:", nd["shown"], [c["number"][:30] for c in nd["contracts"][:5]])

un = call("get_contracts_overview", {"query": "0127200000226001863", "limit": 10})
print("\nУнеча 1863: statusCounts", un["statusCounts"], "| записей:", un["shown"])
for c in un["contracts"]:
    print(f"  deadline {c['deadline']} status {c['status']} total {c['totalAmount']} docs={len(c['documents'])}")
print("OVERVIEW_OK")
