# Простые поставки: входящие договоры через MCP

Use this when processing incoming contract documents in the `prostye_postavki` connector.

## Workflow

1. Read the MCP prompt/guide for `incoming_contract_processing` before editing documents.
2. List unprocessed documents with `list_incoming_contract_documents(includeProcessed=false)`.
3. Read each selected document with `read_incoming_contract_document(includeText=true)` and extract fields manually from OCR/text.
4. Resolve customer/supplier by INN against `organizations` before saving; prefer standardized names returned by the app.
5. Search products/stock by distinctive terms, but if no confident match exists, preserve the full contract item name and note that no catalog/stock match was found.
6. Save only parsed fields with `save_incoming_contract_document_fields`; do not create a contract unless the user explicitly asks for it.
7. Verify by a separate `read_incoming_contract_document(includeText=false)` call after saving.

## Large OCR/truncated output workaround

Some incoming documents can exceed the chat/tool output budget. If normal tool output is truncated but the MCP connector is available over HTTP in Hermes config, make a direct JSON-RPC MCP call from a local script and filter inside the script before printing. Print only safe snippets around terms such as `срок`, `поставка`, `Спецификация`, `Цена Контракта`, `НДС`, `ИНН`, `Заказчик`, `Поставщик`. Never print the connector URL or secrets.

Safe pattern:

```python
import json, pathlib, re, requests, yaml
url = yaml.safe_load(pathlib.Path('/root/.hermes/config.yaml').read_text())['mcp_servers']['prostye_postavki']['url']
headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
requests.post(url, headers=headers, json={
    'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
    'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'hermes-filter', 'version': '1'}}
}, timeout=20)
payload = {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {
    'name': 'read_incoming_contract_document',
    'arguments': {'documentId': '<uuid>', 'includeText': True},
}}
data = requests.post(url, headers=headers, json=payload, timeout=60).json()
text = '\n'.join(c.get('text', '') for c in data.get('result', {}).get('content', []) if isinstance(c, dict))
obj = json.loads(text)
obj = json.loads(obj['result']) if isinstance(obj.get('result'), str) else obj
ocr = re.sub(r'[ \t]+', ' ', obj.get('ocrText', ''))
for kw in ['срок', 'поставка', 'Спецификация', 'Цена Контракта', 'НДС', 'ИНН']:
    for m in re.finditer(kw, ocr, flags=re.I):
        print(ocr[max(0, m.start()-700):m.end()+1200].replace('\n', ' '))
        break
```

## Date/deadline notes

- If the contract date field is blank in the source, use the upload/current processing date only when the app workflow requires a date, and add an explicit note: `Дата договора в бланке не заполнена; использована дата загрузки ...`.
- For duration deadlines, pass `deadlineDays` + `deadlineDaysType` and keep the exact source phrase in `deadlineText`.
- For split deliveries, preserve the split schedule in `deadlineText`; if only one date field is available, use the final/outer deadline and explain the split in notes.

## Save-output quirk

The app's parsed item shape may display quantity and unit price as `price`/`total` labels in the read-back JSON (for example `price: "100"`, `total: "871.92"`, `planQty: "100"`). Verify the semantic fields by checking `planQty`, `sum`, `unit`, and the original OCR/specification, not label names alone.
