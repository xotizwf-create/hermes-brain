"""Recon: department.* + user.update via webhook vs app token; current org structure; owner ids."""
import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402
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
        return False, exc.read().decode()[:200]
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:150]


print("=== webhook scopes ===")
ok, d = wh("scope")
print(d.get("result") if ok else d)

print("\n=== app-token scopes (для сравнения) ===")
try:
    ep, tok = b24bot._b24_app_access_token()
    print(b24bot._b24_app_call(ep, tok, "scope", {}).get("result"))
except Exception as exc:  # noqa: BLE001
    print("app scope failed:", str(exc)[:120])

print("\n=== department.get (текущая оргструктура на портале) ===")
ok, d = wh("department.get")
if ok:
    for dep in (d.get("result") or []):
        print(f"  id={dep.get('ID')} «{dep.get('NAME')}» parent={dep.get('PARENT')} head={dep.get('UF_HEAD')}")
else:
    print("ERR", d)

print("\n=== department.fields ===")
ok, d = wh("department.fields")
print((list((d.get("result") or {}).keys()) if ok else d))

print("\n=== активные пользователи портала (id, ФИО, отдел) ===")
ok, d = wh("user.get", {"ACTIVE": "true"})
if ok:
    for u in (d.get("result") or [])[:40]:
        name = " ".join(x for x in (u.get("NAME"), u.get("LAST_NAME")) if x)
        print(f"  id={u.get('ID'):>3} {name:<28} отделы={u.get('UF_DEPARTMENT')} должность={u.get('WORK_POSITION') or '-'}")
else:
    print("ERR", d)

print("\n=== оргструктура в НАШЕЙ базе (users) ===")
with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT count(*) AS n FROM users WHERE is_active")
    print("  активных в users:", cur.fetchone()["n"])
    cur.execute("SELECT bitrix_user_id, full_name, work_position, department FROM users WHERE is_active ORDER BY bitrix_user_id LIMIT 15")
    for r in cur.fetchall():
        print(f"  {r['bitrix_user_id']:>3} {r['full_name']:<28} {r['work_position'] or '-':<25} отдел={r['department'] or '-'}")
