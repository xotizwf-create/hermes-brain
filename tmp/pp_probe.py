"""Probe: what exactly survives law-scrub in a real contract preamble (runs on miramed32)."""
import json
import urllib.request
from pathlib import Path

APP = Path("/var/www/prostye-postavki/app")
secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
        break
URL = f"http://127.0.0.1:8000/mcp/{secret}"


def call(name, arguments):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": arguments}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())
    if "error" in payload:
        raise RuntimeError(f"{name}: {payload['error']}")
    return json.loads(payload["result"]["content"][0]["text"])


exported = call("export_contract_template", {
    "contractId": "54587121-ab06-4a05-b08e-a8bf9ea9448a",
    "templateName": "ТЕСТ — УДАЛИТЬ", "overwrite": True,
})
print("lawMentions detected:")
for ln in exported["detected"].get("lawMentions") or []:
    print("  |", ln[:250])
print("dates detected:", exported["detected"].get("dates"))
print("money mentions:", exported["detected"].get("moneyMentions"))

created = call("create_contract_from_template", {
    "templateName": "ТЕСТ — УДАЛИТЬ",
    "contractDate": "10.07.2026",
    "items": [{"name": "Тестовый товар", "unit": "шт", "qty": 2, "price": 100}],
    "vatPercent": 0,
})
rep = created["report"]
print("\nlawScrub:")
for ch in rep.get("lawScrub") or []:
    print("  BEFORE:", ch["before"][:250])
    print("  AFTER :", ch["after"][:250])
print("\npreambleAfter:")
print(rep.get("preambleAfter", "")[:1500])
print("\nvalidity:")
for v in rep.get("validityParagraphs") or []:
    print("  |", v[:200])
call("delete_contract_template", {"templateName": "ТЕСТ — УДАЛИТЬ"})
print("\nPROBE_DONE")
