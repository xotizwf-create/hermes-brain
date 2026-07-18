"""Live e2e: contract templates sourced from the «Контракты» section (runs on miramed32).

Read-only w.r.t. real contracts: finds a real contract DOCX via MCP, downloads it via
the new /contract-files/ route, exports it as template "ТЕСТ — УДАЛИТЬ", generates a
contract, checks the report, then deletes the test template.
"""
import json
import urllib.request
from pathlib import Path

APP = Path("/var/www/prostye-postavki/app")
secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
        break
assert secret, "no MCP secret"
URL = f"http://127.0.0.1:8000/mcp/{secret}"


def call(name, arguments):
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode())
    if "error" in payload:
        raise RuntimeError(f"{name}: {payload['error']}")
    result = payload["result"]
    if isinstance(result, dict) and result.get("isError"):
        raise RuntimeError(f"{name}: {result}")
    return json.loads(result["content"][0]["text"])


# 1. Find a real contract DOCX via read_table_rows (read-only).
rows = call("read_table_rows", {"table": "contract_files", "limit": 200})
docx_rows = [r for r in rows.get("rows", []) if str(r.get("original_name") or "").lower().endswith(".docx")]
print(f"contract_files total shown: {len(rows.get('rows', []))}, docx: {len(docx_rows)}")
assert docx_rows, "В разделе Контракты нет ни одного DOCX-файла — нечего тестировать"
target = docx_rows[0]
contract_id = str(target["contract_id"])
print(f"target contract: {contract_id}, file: {target['original_name']!r}")

# 2. get_contract_files by contractId
files = call("get_contract_files", {"contractId": contract_id})
assert files["count"] >= 1, files
docx_files = [f for f in files["files"] if f["isDocx"] and f["available"]]
assert docx_files, f"get_contract_files не видит DOCX: {files}"
f0 = docx_files[0]
print(f"get_contract_files OK: {f0['filename']!r} customer={f0['customer']!r} number={f0['contractNumber']!r}")

# 3. download via new MCP route (как обычная кнопка скачивания, но через MCP)
dl_url = f0["downloadUrl"]
if not dl_url.startswith("http"):
    dl_url = f"http://127.0.0.1:8000{dl_url}"
dl = urllib.request.urlopen(dl_url, timeout=60)
data = dl.read()
assert dl.status == 200 and len(data) == f0["sizeBytes"], (dl.status, len(data), f0["sizeBytes"])
assert data[:2] == b"PK", "not a docx/zip"
print(f"download route OK ({len(data)} bytes)")

# 4. export as template from the contract section
exported = call("export_contract_template", {
    "contractId": contract_id, "templateName": "ТЕСТ — УДАЛИТЬ", "overwrite": True,
})
det = exported["detected"]
meta_kind = exported.get("sourceDocumentId", "")
print(f"exported: {exported['status']} source={meta_kind} number={det.get('number')!r} inns={det.get('inns')}")
assert meta_kind.startswith("contract-file:"), exported

# 5. also test search by organizationQuery (customer name fragment)
customer = (f0.get("customer") or "").strip()
if len(customer) >= 4:
    frag = customer.split()[0][:10]
    exported2 = call("export_contract_template", {
        "organizationQuery": frag, "templateName": "ТЕСТ — УДАЛИТЬ", "overwrite": True,
    })
    print(f"organizationQuery '{frag}' -> {exported2['sourceDocumentId']} OK")

# 6. generate a contract from the REAL template
created = call("create_contract_from_template", {
    "templateName": "ТЕСТ — УДАЛИТЬ",
    "contractDate": "10.07.2026",
    "items": [{"name": "Тестовый товар", "unit": "шт", "qty": 2, "price": 100}],
    "vatPercent": 0,
    "includeResultText": True,
})
rep = created["report"]
rt = created.get("resultText", "")
print(f"created: {created['filename']!r} size={created['sizeBytes']}")
print(f"  replacements: {[(r['find'][:40], r['count']) for r in rep.get('replacements', [])]}")
print(f"  lawScrub: {len(rep.get('lawScrub') or [])}, specTables: {rep.get('specTables')}, totalSum: {rep.get('totalSum')}")
print(f"  warnings: {rep.get('warnings')}")
print(f"  validity paragraphs reported: {len(rep.get('validityParagraphs') or [])}")
assert created["filename"] == "Договор №10.07.2026.docx"
assert "10.07.2026" in rt
fz_pre = "ФЗ" in (rep.get("preambleAfter") or "")
print(f"  preamble contains ФЗ after scrub: {fz_pre}")

deleted = call("delete_contract_template", {"templateName": "ТЕСТ — УДАЛИТЬ"})
assert deleted["status"] == "deleted", deleted
print("test template deleted")
print("LIVE_E2E_CONTRACTS_OK")
