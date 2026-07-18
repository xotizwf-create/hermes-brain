"""Live e2e test of contract template tools on prostye-postavki prod (runs on miramed32).

There are no DOCX contracts among real incoming documents (all scans/PDF), so this
seeds a synthetic contract DOCX as a pending document in the app's own storage
format, runs the FULL MCP flow (export template -> list -> create contract ->
delete template), asserts every business rule, then removes the seeded files.
Nothing else is touched: no contract records, no organizations.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

APP = Path("/var/www/prostye-postavki/app")
sys.path.insert(0, str(APP))
sys.path.insert(0, str(APP / "backend" / "tools"))

from contract_template_smoke import build_source_contract  # noqa: E402

PENDING = APP / "backend" / "data" / "pending_contract_files"
DOC_ID = "smoketest-contract-tpl"

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


def cleanup():
    for suffix in (".json", ".bin", ".preview.bin"):
        p = PENDING / f"{DOC_ID}{suffix}"
        if p.exists():
            p.unlink()


content = build_source_contract()
PENDING.mkdir(parents=True, exist_ok=True)
(PENDING / f"{DOC_ID}.bin").write_bytes(content)
(PENDING / f"{DOC_ID}.json").write_text(json.dumps({
    "id": DOC_ID,
    "filename": "ТЕСТ договор для шаблона — УДАЛИТЬ.docx",
    "size_bytes": len(content),
    "uploaded_at": int(time.time() * 1000),
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "processed_at": int(time.time() * 1000),
}, ensure_ascii=False), encoding="utf-8")

try:
    exported = call("export_contract_template", {
        "documentId": DOC_ID, "templateName": "ТЕСТ — УДАЛИТЬ", "overwrite": True,
    })
    det = exported["detected"]
    print(f"exported: {exported['status']} id={exported['templateId']}")
    print(f"  number={det.get('number')!r} inns={det.get('inns')} laws={len(det.get('lawMentions') or [])}")
    assert det.get("number") == "123/45", det
    assert "3200000001" in (det.get("inns") or []), det

    listed = call("list_contract_templates", {})
    assert any(t["name"] == "ТЕСТ — УДАЛИТЬ" for t in listed["templates"]), listed
    print(f"template listed OK (total {listed['count']})")

    created = call("create_contract_from_template", {
        "templateName": "ТЕСТ — УДАЛИТЬ",
        "contractDate": "09.07.2026",
        "items": [
            {"name": "Тестовый товар А", "unit": "шт", "qty": 2, "price": 100},
            {"name": "Тестовый товар Б", "unit": "уп", "qty": 1, "price": 49.5},
        ],
        "vatPercent": 0,
        "replacements": [
            {"find": "действует до 31.12.2026", "replace": "действует до 31.12.2027", "required": True},
        ],
        "includeResultText": True,
    })
    rep = created["report"]
    rt = created.get("resultText", "")
    print(f"created: {created['filename']!r} size={created['sizeBytes']} number={created['contractNumber']!r}")
    print(f"  lawScrub: {len(rep.get('lawScrub') or [])}, specTables: {rep.get('specTables')}, totalSum: {rep.get('totalSum')}")
    print(f"  warnings: {rep.get('warnings')}")
    assert created["filename"] == "Договор №09.07.2026.docx", created["filename"]
    assert "№ 09.07.2026" in rt and "№ 123/45" not in rt, "number swap failed"
    assert "44-ФЗ" not in rt and "Федеральным законом" not in rt, "law refs survived"
    assert "Тестовый товар А" in rt and "Старый товар А" not in rt, "spec not rebuilt"
    assert rep.get("totalSum") == 249.5, rep.get("totalSum")
    assert "249,50" in rt, "total not in text"
    assert "31.12.2027" in rt and "31.12.2026" not in rt, "validity not replaced"
    assert any("действует до" in p for p in rep.get("validityParagraphs") or []), "validity not reported"

    export_file = APP / "backend" / "data" / "mcp_contract_exports" / created["downloadPath"].split("/")[-1]
    assert export_file.exists() and export_file.stat().st_size == created["sizeBytes"], "export file mismatch"
    print("export file on disk OK")

    # download route (through the real HTTP app)
    dl = urllib.request.urlopen(f"http://127.0.0.1:8000{created['downloadPath']}", timeout=30)
    data = dl.read()
    assert dl.status == 200 and len(data) == created["sizeBytes"], "download route failed"
    print("download route OK")

    deleted = call("delete_contract_template", {"templateName": "ТЕСТ — УДАЛИТЬ"})
    assert deleted["status"] == "deleted", deleted
    print("test template deleted")
    print("LIVE_E2E_OK")
finally:
    cleanup()
    print("seeded pending files removed")
