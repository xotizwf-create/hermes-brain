"""Verify the extended safety instruction is served to agents (via the same loader start_here uses)."""
import sys

sys.path.insert(0, "/var/www/albery")
from agent_knowledge import load_instructions  # noqa: E402

rows = load_instructions()
hit = [r for r in rows if "бэкап" in str(r.get("name") or "").lower()]
for r in hit:
    body = str(r.get("content") or r.get("body") or "")
    print("name:", r.get("name"), "| scope:", r.get("scope"), "| len:", len(body))
    print("has new block:", "Дополнительные правила безопасности" in body,
          "| mentions AGENTS.md:", "AGENTS.md" in body)
print("total instructions:", len(rows))
