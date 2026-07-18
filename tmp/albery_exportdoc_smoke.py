# Enable export_document for main + lawyer, then e2e through the lawyer's REAL connector:
# tools/list advertises it, tools/call renders a sample contract HTML -> valid .docx URL.
import io
import json
import zipfile

import requests

import app  # noqa: F401
from app import pg_connect

# 1. enable for both customized agents (idempotent)
with pg_connect() as conn:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE agents SET tools = array_append(tools, 'export_document') "
                "WHERE slug IN ('main', 'agent-sklad') AND tools_customized "
                "AND NOT ('export_document' = ANY(tools)) RETURNING slug"
            )
            print("enabled for:", [r["slug"] for r in cur.fetchall()] or "(already on)")
        with conn.cursor() as cur:
            cur.execute("SELECT mcp_token FROM agents WHERE slug = 'agent-sklad'")
            token = cur.fetchone()["mcp_token"]

import agent_center
agent_center._agent_cache_bust()

base = f"http://127.0.0.1:5002/mcp-agent/agent-sklad/{token}"

# 2. connector advertises it
tools = requests.post(base, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, timeout=30).json()
names = {t["name"] for t in tools["result"]["tools"]}
print("tools/list:", "OK" if "export_document" in names else "MISSING", f"({len(names)} tools)")

# 3. real render through the connector
html = """
<h1 style="text-align:center">ДОГОВОР ПОСТАВКИ № 07-2026</h1>
<table border="0"><tr><td>г. Москва</td><td style="text-align:right">«05» июля 2026 г.</td></tr></table>
<p style="text-indent:1.25cm">ООО «Ромашка», именуемое в дальнейшем «Поставщик», и ООО «Лютик»,
именуемое в дальнейшем «Покупатель», заключили настоящий договор о нижеследующем.</p>
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
payload = json.loads(call["result"]["content"][0]["text"])
url = payload["url"]
print("tools/call:", "OK" if url.startswith("https://") else call)

# 4. the URL serves a valid docx
blob = requests.get(url, timeout=30).content
zf = zipfile.ZipFile(io.BytesIO(blob))
ok = "word/document.xml" in zf.namelist()
body = zf.read("word/document.xml").decode("utf-8")
print("docx valid:", ok, "| size", len(blob), "bytes")
print("page break in xml:", '<w:pageBreakBefore/>' in body or 'pageBreakBefore' in body)
print("times new roman:", "Times New Roman" in body)
print("url:", url[:100])
