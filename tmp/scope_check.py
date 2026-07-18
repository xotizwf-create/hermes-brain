"""Verify instruction scoping: the safety instruction reaches ONLY agent-razrabotchik."""
import sys

sys.path.insert(0, "/var/www/albery")
from agent_knowledge import allowed_instruction_paths  # noqa: E402

TARGET = "Обязательный бэкап перед изменениями"
for slug in ("agent-razrabotchik", "agent-sklad", "agent-finansist", "main"):
    paths = allowed_instruction_paths(slug) or set()
    print(f"{slug}: sees_backup={TARGET in paths} | total={len(paths)}")
