"""Backend checks: incoming download, mandatory-cell validation, BP sanitizer (on miramed32)."""
import json
import urllib.request
from pathlib import Path

APP = Path("/var/www/prostye-postavki/app")
import sys
sys.path.insert(0, str(APP))

secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
URL = f"http://127.0.0.1:8000/mcp/{secret}"


def rpc(name, arguments):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": arguments}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def call(name, arguments):
    p = rpc(name, arguments)
    if "error" in p:
        raise RuntimeError(f"{name}: {p['error']}")
    return json.loads(p["result"]["content"][0]["text"])


# 1. BP sanitizer (pure function, import uses live DB schema ensure like a restart)
from backend.app.main import _bp_sanitize_text  # noqa: E402
assert _bp_sanitize_text("Коврик 10×10 см") == "Коврик 10x10 см", _bp_sanitize_text("Коврик 10×10 см")
assert _bp_sanitize_text("Салфетки 5✕7 — №1…") == 'Салфетки 5x7 - №1...', _bp_sanitize_text("Салфетки 5✕7 — №1…")
assert _bp_sanitize_text("Ø25 µл ½") == "d25 мкл 1/2", _bp_sanitize_text("Ø25 µл ½")
assert _bp_sanitize_text("обычный текст, №5 «ок»") == "обычный текст, №5 «ок»"
print("BP sanitizer OK (× ✕ — … Ø µ ½ -> cp1251-safe, обычный текст не тронут)")

# 2. download incoming document via MCP
docs = call("list_incoming_contract_documents", {})
assert docs["documents"], "no incoming docs"
doc = docs["documents"][0]
assert doc.get("downloadUrl"), doc
dl_url = doc["downloadUrl"]
if not dl_url.startswith("http"):
    dl_url = f"http://127.0.0.1:8000{dl_url}"
resp = urllib.request.urlopen(dl_url, timeout=60)
data = resp.read()
assert resp.status == 200 and len(data) == doc["sizeBytes"], (resp.status, len(data), doc["sizeBytes"])
if doc["filename"].lower().endswith(".docx"):
    assert data[:2] == b"PK"
print(f"download incoming OK: {doc['filename']!r} {len(data)} bytes")

# 3. mandatory-cell validation refuses partial saves (nothing is written)
p = rpc("save_contract_from_incoming_document", {
    "documentId": doc["id"],
    "extracted": {"contractNumber": "X", "items": [{"name": "y", "qty": 0}]},
})
err = (p.get("error") or {}).get("message", "")
assert "ПУСТЫЕ ОБЯЗАТЕЛЬНЫЕ ЯЧЕЙКИ" in err, err
for frag in ("дата договора", "дедлайн", "customerInn", "supplierInn", "docName", "unit", "qty", "цена"):
    assert frag in err, (frag, err)
print("mandatory-cell validation OK (перечисляет все пустые ячейки, ничего не записано)")

# 4. extracted is required — stored parsedEdits are not used
p2 = rpc("save_contract_from_incoming_document", {"documentId": doc["id"]})
err2 = (p2.get("error") or {}).get("message", "")
assert "extracted" in err2 and "автораспознавание" in err2, err2
print("extracted required OK (parsedEdits не используется)")

print("LIVE_HARDENING_OK")
