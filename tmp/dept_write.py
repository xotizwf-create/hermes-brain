"""Write-probe: department add/update/delete + user.update (department & position). Cleans up."""
import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, "/var/www/albery")
from shared.db import connect, load_env_value  # noqa: E402

WH = (load_env_value("B24_TESTBOT_WEBHOOK_BASE") or "").rstrip("/")


def wh(method, payload=None):
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(f"{WH}/{method}.json", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        return False, exc.read().decode()[:250]
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:150]


print("=== users table columns ===")
with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
    print([r["column_name"] for r in cur.fetchall()])

print("\n=== department.add (ТЕСТ) ===")
ok, d = wh("department.add", {"NAME": "ТЕСТ отдел — УДАЛИТЬ", "PARENT": 1})
print("add:", d if not ok else d.get("result"))
dep_id = d.get("result") if ok else None

if dep_id:
    print("\n=== department.update (переименование + руководитель id14) ===")
    ok, d = wh("department.update", {"ID": dep_id, "NAME": "ТЕСТ отдел 2", "UF_HEAD": 14})
    print("update:", d if not ok else d.get("result"))

    print("\n=== проверка ===")
    ok, d = wh("department.get", {"ID": dep_id})
    print((d.get("result") if ok else d))

    print("\n=== user.update: перевод человека в отдел + должность (на ИИ Агенте id22) ===")
    ok, d = wh("user.update", {"ID": 22, "UF_DEPARTMENT": [dep_id], "WORK_POSITION": "ТЕСТ должность"})
    print("user.update:", d if not ok else d.get("result"))
    ok, d = wh("user.get", {"ID": 22})
    u = (d.get("result") or [{}])[0] if ok else {}
    print("  проверка: отделы =", u.get("UF_DEPARTMENT"), "| должность =", u.get("WORK_POSITION"))

    print("\n=== ОТКАТ: вернуть ИИ Агента в отдел 1, снять тест-должность ===")
    ok, d = wh("user.update", {"ID": 22, "UF_DEPARTMENT": [1], "WORK_POSITION": ""})
    print("restore user:", d if not ok else d.get("result"))
    ok, d = wh("department.delete", {"ID": dep_id})
    print("department.delete:", d if not ok else d.get("result"))
    ok, d = wh("department.get")
    print("итог оргструктуры:", [(x.get("ID"), x.get("NAME")) for x in (d.get("result") or [])])
    ok, d = wh("user.get", {"ID": 22})
    u = (d.get("result") or [{}])[0] if ok else {}
    print("ИИ Агент после отката: отделы =", u.get("UF_DEPARTMENT"), "должность =", repr(u.get("WORK_POSITION")))
