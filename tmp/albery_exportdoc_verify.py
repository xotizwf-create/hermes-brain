# Verify-only: lawyer connector advertises export_document and renders a contract docx.
import io
import json
import zipfile

import requests

import app  # noqa: F401
from app import pg_connect

with pg_connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT mcp_token FROM agents WHERE slug = 'agent-sklad'")
        token = cur.fetchone()["mcp_token"]

base = f"http://127.0.0.1:5002/mcp-agent/agent-sklad/{token}"
tools = requests.post(base, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, timeout=30).json()
names = {t["name"] for t in tools["result"]["tools"]}
print("tools/list:", "OK" if "export_document" in names else "MISSING", f"({len(names)} tools)")

html = """
<h1 style="text-align:center">ДОГОВОР ПОСТАВКИ № 07-2026</h1>
<table border="0"><tr><td>г. Москва</td><td style="text-align:right">«05» июля 2026 г.</td></tr></table>
<p style="text-indent:1.25cm">ООО «Ромашка» («Поставщик») и ООО «Лютик» («Покупатель») заключили договор.</p>
<h2>1. ПРЕДМЕТ ДОГОВОРА</h2>
<p style="text-indent:1.25cm">1.1. Поставщик обязуется поставить ткань согласно Приложению № 1.</p>
<h2>9. РЕКВИЗИТЫ И ПОДПИСИ СТОРОН</h2>
<table border="0"><tr>
<td><b>Поставщик:</b><br>ООО «Ромашка»<br>ИНН [заполнить]<br><br>___________ / [ФИО]</td>
<td><b>Покупатель:</b><br>ООО «Лютик»<br>ИНН [заполнить]<br><br>___________ / [ФИО]</td>
</tr></table>
<h2 style="page-break-before:always; text-align:right">Приложение № 1</h2>
<table><tr><th>Товар</th><th>Кол-во</th><th>Цена</th></tr><tr><td>Ткань х/б</td><td>100 м</td><td>[заполнить]</td></tr></table>
"""
call = requests.post(base, json={
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {"name": "export_document",
               "arguments": {"title": "Договор поставки ткани (тест)", "html": html, "line_spacing": 1.5}},
}, timeout=60).json()
if "result" not in call:
    print("tools/call FAILED:", json.dumps(call, ensure_ascii=False)[:400])
else:
    payload = json.loads(call["result"]["content"][0]["text"])
    url = payload["url"]
    blob = requests.get(url, timeout=30).content
    zf = zipfile.ZipFile(io.BytesIO(blob))
    body = zf.read("word/document.xml").decode("utf-8")
    print("tools/call: OK | docx", len(blob), "bytes")
    print("page break:", "pageBreakBefore" in body, "| TNR:", "Times New Roman" in body,
          "| borders on spec table:", "tblBorders" in body)
    print("url:", url[:110])
