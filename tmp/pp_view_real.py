import json, base64, urllib.request
from pathlib import Path
APP = Path("/var/www/prostye-postavki/app")
secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
URL = f"http://127.0.0.1:8000/mcp/{secret}"
def call_raw(name, arguments):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":arguments}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type":"application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        p = json.loads(resp.read().decode())
    if "error" in p: raise RuntimeError(p["error"])
    return p["result"]
def call(n,a):
    return json.loads(call_raw(n,a)["content"][0]["text"])
docs = call("list_incoming_contract_documents", {"includeProcessed": True, "limit": 100})
for d in docs["documents"][:15]:
    print(d["id"], d["mimeType"], d.get("previewType"), repr(d["filename"][:45]))
target = next((d for d in docs["documents"] if not d["filename"].lower().endswith(".docx")), None) or (docs["documents"][0] if docs["documents"] else None)
if target:
    v = call_raw("view_incoming_contract_document", {"documentId": target["id"], "maxPages": 2})
    imgs = [b for b in v["content"] if b.get("type") == "image"]
    ok = imgs and base64.b64decode(imgs[0]["data"])[:2] == b"\xff\xd8"
    print(f"VIEW_REAL: {target['filename']!r} mime={target['mimeType']} -> {len(imgs)} image(s), jpeg={ok}")
else:
    print("no incoming docs at all")
