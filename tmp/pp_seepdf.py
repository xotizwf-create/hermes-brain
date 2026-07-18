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
v = rpc("view_incoming_contract_document", {"documentId": "30390ab0-3cc0-400a-b9d7-832c73486692", "pages": [1, 7, 13]})
n = 0
for b in v["content"]:
    if b.get("type") == "image":
        n += 1
        print(f"IMGSTART {n}")
        print(b["data"])
        print(f"IMGEND {n}")
