import json, urllib.request
from pathlib import Path
APP = Path("/var/www/prostye-postavki/app")
secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
URL = f"http://127.0.0.1:8000/mcp/{secret}"
def rpc(name, arguments):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":arguments}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type":"application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())["result"]
docs = json.loads(rpc("list_incoming_contract_documents", {})["content"][0]["text"])
for d in docs["documents"]:
    print("DOC:", d["id"], repr(d["filename"]), d["mimeType"], d["sizeBytes"], "processed:", d["processed"])
if docs["documents"]:
    doc = docs["documents"][0]
    r = json.loads(rpc("read_incoming_contract_document", {"documentId": doc["id"], "includeText": True})["content"][0]["text"])
    text = r.get("ocrText") or ""
    print("TEXTLEN:", r.get("textLength"), "PAGES:", r.get("pagesCount"))
    import re
    # show contract headers inside
    for m in re.finditer(r"(договор|контракт)[^\n]{0,80}№[^\n]{0,40}", text, re.IGNORECASE):
        print("HDR:", m.group(0)[:120])
    print("--- first 3000 chars ---")
    print(text[:3000])
