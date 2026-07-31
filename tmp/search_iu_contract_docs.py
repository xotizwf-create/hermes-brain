import json
import sys

sys.path.insert(0, "/var/www/albery")
from mcp import context_server

queries = [
    "примерный договор ИУ",
    "шаблон договора ИУ",
    "договор индивидуальные условия Wildberries",
]
answers = {}
for query in queries:
    result = context_server.TOOLS["search_company_knowledge"]["handler"](
        {"query": query, "limit": 20}
    )
    matches = result.get("results") or result.get("items") or []
    answers[query] = [
        {
            "name": item.get("name") or item.get("title"),
            "path": item.get("path"),
            "google_file_id": bool(item.get("google_file_id")),
            "mime_type": item.get("mime_type"),
        }
        for item in matches
    ]
print(json.dumps(answers, ensure_ascii=True, indent=2, default=str))
