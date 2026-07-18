"""E2E of the org-structure tools: read, gates (who may change / confirm), create dept, set head,
move employee, protections, full cleanup."""
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from mcp import context_server as cs  # noqa: E402

FAILED = []


def expect_refusal(label, fn, args, needle):
    try:
        fn(args)
        FAILED.append(label)
        print(f"ERR {label}: НЕ отказал (дыра в защите!)")
    except cs.McpError as exc:
        ok = needle.lower() in str(exc).lower()
        print(f"{'OK ' if ok else 'ERR'} {label}: отказал — {str(exc)[:110]}")
        if not ok:
            FAILED.append(label)


print("=== 1. Чтение живой оргструктуры ===")
deps = cs.tool_get_bitrix_departments({})
for d in deps["departments"]:
    print(f"  отдел {d['department_id']} «{d['name']}» рук.={d.get('head_name') or '—'} "
          f"людей={len(d['employees'])}")

print("\n=== 2. Защиты (кто может менять) ===")
expect_refusal("Александр (16) — не вправе",
               cs.tool_manage_bitrix_department,
               {"action": "create", "name": "Х", "requested_by_bitrix_user_id": 16, "confirm": True},
               "нет прав")
expect_refusal("Софья (36) — не вправе",
               cs.tool_assign_employee_department,
               {"employees": [36], "department_ids": [1], "requested_by_bitrix_user_id": 36, "confirm": True},
               "нет прав")
expect_refusal("без confirm (даже Евгений)",
               cs.tool_manage_bitrix_department,
               {"action": "create", "name": "Х", "requested_by_bitrix_user_id": 14},
               "confirm=true")
expect_refusal("без указания, кто просит",
               cs.tool_manage_bitrix_department,
               {"action": "create", "name": "Х", "confirm": True},
               "requested_by")

print("\n=== 3. Евгений (14) создаёт отдел + назначает руководителя ===")
res = cs.tool_manage_bitrix_department({
    "action": "create", "name": "ТЕСТ-отдел — УДАЛИТЬ", "parent_id": 1,
    "head_bitrix_user_id": 16, "requested_by_bitrix_user_id": 14, "confirm": True})
print("  создан:", {k: res[k] for k in ("department_id", "name", "head_bitrix_user_id")}, "|", res["sync"])
dep_id = res["department_id"]

print("\n=== 4. ИИ Агент (22) переводит сотрудника + должность ===")
res = cs.tool_assign_employee_department({
    "employees": ["Софья Погорелова"], "department_ids": [dep_id], "position": "ТЕСТ должность",
    "requested_by_bitrix_user_id": 22, "confirm": True})
print("  перевод:", res["employees"])

print("\n=== 5. Защита: удалить непустой отдел нельзя ===")
expect_refusal("непустой отдел", cs.tool_manage_bitrix_department,
               {"action": "delete", "department_id": dep_id,
                "requested_by_bitrix_user_id": 14, "confirm": True},
               "ещё есть сотрудники")

print("\n=== 6. Проверка структуры ===")
for d in cs.tool_get_bitrix_departments({})["departments"]:
    if d["department_id"] == dep_id:
        print(f"  отдел {d['department_id']} «{d['name']}» рук.={d.get('head_name')} "
              f"люди={[e['full_name'] + ' (' + e['position'] + ')' for e in d['employees']]}")

print("\n=== 7. ЗАЧИСТКА: вернуть человека, удалить тест-отдел ===")
cs.tool_assign_employee_department({"employees": ["Софья Погорелова"], "department_ids": [1],
                                    "position": "", "requested_by_bitrix_user_id": 14, "confirm": True})
res = cs.tool_manage_bitrix_department({"action": "delete", "department_id": dep_id,
                                        "requested_by_bitrix_user_id": 14, "confirm": True})
print("  удалён:", res.get("deleted"), res.get("name"))
final = cs.tool_get_bitrix_departments({})
print("  итог:", [(d["department_id"], d["name"], len(d["employees"])) for d in final["departments"]])

print("\nE2E " + ("FAILED: " + ", ".join(FAILED) if FAILED else "OK — все защиты держат, всё работает"))
sys.exit(1 if FAILED else 0)
