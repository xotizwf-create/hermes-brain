"""Verify: BOTH developer instructions reach only agent-razrabotchik."""
import sys

sys.path.insert(0, "/var/www/albery")
from agent_knowledge import allowed_instruction_paths  # noqa: E402

TARGETS = ("Обязательный бэкап перед изменениями", "Проверка логики перед сдачей")
for slug in ("agent-razrabotchik", "agent-sklad", "agent-finansist", "main"):
    paths = allowed_instruction_paths(slug) or set()
    flags = {t.split()[0]: (t in paths) for t in TARGETS}
    print(f"{slug}: {flags} | total={len(paths)}")
