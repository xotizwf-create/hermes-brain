"""E2E: upload via MCP (fileUrl + multipart) then full pipeline touch (miramed32)."""
import io, json, subprocess, time, urllib.request
from pathlib import Path
APP = Path("/var/www/prostye-postavki/app")
import sys
sys.path.insert(0, str(APP))
PENDING = APP / "backend" / "data" / "pending_contract_files"
secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
URL = f"http://127.0.0.1:8000/mcp/{secret}"
def rpc(name, arguments):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":name,"arguments":arguments}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type":"application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())
def call(name, arguments):
    p = rpc(name, arguments)
    if "error" in p: raise RuntimeError(f"{name}: {p['error']}")
    return json.loads(p["result"]["content"][0]["text"])

uploaded_ids = []
try:
    # build a small test docx locally
    from docx import Document
    d = Document(); d.add_paragraph("ТЕСТ загрузка через MCP — УДАЛИТЬ")
    buf = io.BytesIO(); d.save(buf)
    test_path = Path("/tmp/тест_загрузка_mcp.docx")
    test_path.write_bytes(buf.getvalue())

    # 1) multipart endpoint (как агент curl'ом с локальным вложением)
    out = subprocess.run(
        ["curl", "-s", "-F", f"file=@{test_path};filename=ТЕСТ загрузка mcp.docx",
         f"http://127.0.0.1:8000/mcp/{secret}/incoming-documents/upload"],
        capture_output=True, text=True, timeout=120)
    resp = json.loads(out.stdout)
    assert resp["status"] == "uploaded", resp
    doc1 = resp["document"]["id"]
    uploaded_ids.append(doc1)
    print(f"multipart upload OK: id={doc1}, preview={resp['document']['previewType']}")

    # 2) fileUrl: настоящий внешний URL (как у агента будет ссылка на файл)
    src_url = "https://raw.githubusercontent.com/mozilla/pdf.js/master/web/compressed.tracemonkey-pldi-09.pdf"
    up = call("upload_incoming_document", {"fileUrl": src_url, "filename": "ТЕСТ по ссылке — УДАЛИТЬ.pdf"})
    doc2 = up["document"]["id"]
    uploaded_ids.append(doc2)
    assert up["status"] == "uploaded" and up["downloadUrl"], up
    print(f"fileUrl upload OK: id={doc2}, size={up['document']['sizeBytes']}, next={bool(up['nextSteps'])}")

    # 3) документы видны и обрабатываются штатно (view первой страницы)
    docs = call("list_incoming_contract_documents", {})
    assert any(x["id"] == doc1 for x in docs["documents"]) and any(x["id"] == doc2 for x in docs["documents"])
    v = rpc("view_incoming_contract_document", {"documentId": doc2, "pages": [1]})
    imgs = [b for b in v["result"]["content"] if b.get("type") == "image"]
    assert imgs, "uploaded doc not viewable"
    print(f"uploaded docs listed + viewable OK (view page1: {len(imgs)} image)")

    # 4) SSRF guard
    p = rpc("upload_incoming_document", {"fileUrl": "http://127.0.0.1:8000/api/health"})
    assert "запрещено" in (p.get("error") or {}).get("message", ""), p
    print("SSRF guard OK")
    print("UPLOAD_OK")
finally:
    for doc_id in uploaded_ids:
        for suffix in (".json", ".bin", ".preview.bin"):
            p = PENDING / f"{doc_id}{suffix}"
            if p.exists(): p.unlink()
    Path("/tmp/тест_загрузка_mcp.docx").unlink(missing_ok=True)
    print("cleanup done")
