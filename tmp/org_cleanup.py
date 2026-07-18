"""URGENT cleanup: Александр остался в ТЕСТ-отделе (Bitrix авто-добавляет руководителя).
Вернуть всех в корневой отдел, удалить тест-отдел, проверить итог."""
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from mcp import context_server as cs  # noqa: E402

before = cs.tool_get_bitrix_departments({})
test_deps = [d for d in before["departments"] if "ТЕСТ" in (d["name"] or "").upper()]
print("тест-отделы:", [(d["department_id"], d["name"],
                        [e["full_name"] for e in d["employees"]]) for d in test_deps])

for d in test_deps:
    for e in d["employees"]:
        cs.tool_assign_employee_department({
            "employees": [e["bitrix_user_id"]], "department_ids": [1], "position": "",
            "requested_by_bitrix_user_id": 14, "confirm": True})
        print(f"  вернул в отдел 1: {e['full_name']} (id {e['bitrix_user_id']})")
    res = cs.tool_manage_bitrix_department({"action": "delete", "department_id": d["department_id"],
                                            "requested_by_bitrix_user_id": 14, "confirm": True})
    print("  удалён отдел:", res.get("name"))

final = cs.tool_get_bitrix_departments({})
print("\nИТОГ оргструктуры:")
for d in final["departments"]:
    print(f"  отдел {d['department_id']} «{d['name']}» рук.={d.get('head_name') or '—'} "
          f"людей={len(d['employees'])}")
# должности сотрудников, которых трогали, не должны остаться тестовыми
for d in final["departments"]:
    for e in d["employees"]:
        if "ТЕСТ" in (e["position"] or "").upper():
            print("  ⚠️ осталась тест-должность у", e["full_name"])
print("\nЧИСТО" if not any("ТЕСТ" in (d["name"] or "").upper() for d in final["departments"]) else "\nОСТАЛИСЬ ТЕСТ-ОТДЕЛЫ")
