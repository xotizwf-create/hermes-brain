import json
import sys

sys.path.insert(0, "/var/www/albery")
from mcp import context_server

result = context_server.TOOLS["list_company_files"]["handler"](
    {"limit": 500, "include_empty": True}
)
rows = result.get("items") or result.get("files") or []
needles = (
    "иу",
    "услов",
    "договор",
    "вопрос",
    "ответ",
    "faq",
)
selected = []
for row in rows:
    name = str(row.get("name") or "")
    path = str(row.get("path") or "")
    if any(needle in f"{name} {path}".casefold() for needle in needles):
        selected.append(
            {
                "name": name,
                "path": path,
                "mime_type": row.get("mime_type"),
                "has_google_file_id": bool(row.get("google_file_id")),
                "has_content": bool(row.get("has_content")),
            }
        )
print(json.dumps(selected, ensure_ascii=True, indent=2, default=str))
