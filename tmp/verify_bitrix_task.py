import json
import sys

sys.path.insert(0, "/var/www/albery")
from mcp import context_server

response = context_server._bitrix_call_with_fallback(
    "tasks.task.get",
    {"taskId": 2350},
)
result = response.get("result") or {}
task = result.get("task") if isinstance(result, dict) else {}
print(
    json.dumps(
        {
            "id": task.get("id"),
            "title": task.get("title"),
            "status": task.get("status"),
            "responsible_id": task.get("responsibleId")
            or task.get("responsible_id"),
        },
        ensure_ascii=False,
    )
)
