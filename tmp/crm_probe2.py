"""Read-only probe #2: webhook scope list + does the local-app OAuth token have crm scope."""
import json
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, "/var/www/albery")

# 1) webhook scopes (both bases point to b24-0xrp3s)
from crm_probe import call, load_env  # noqa: E402  (probe #1 sits next to this file in /tmp)

base = load_env("BITRIX_WEBHOOK_BASE").rstrip("/")
ok, _ = call(base, "scope", {})
req = urllib.request.Request(f"{base}/scope.json", data=b"{}", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=30) as r:
    print("webhook scopes:", json.loads(r.read().decode()).get("result"))

# 2) local-app OAuth token
import b24bot  # noqa: E402

endpoint, token = b24bot._b24_app_access_token()
print("app endpoint host:", urllib.parse.urlparse(endpoint).netloc, "token:", "present" if token else "MISSING")
if token:
    def app_call(method, payload):
        try:
            return True, b24bot._b24_app_call(endpoint, token, method, payload)
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)[:250]

    ok, res = app_call("scope", {})
    print("app scopes:", res.get("result") if ok else res)
    for method, payload in [
        ("crm.category.list", {"entityTypeId": 2}),
        ("crm.status.list", {"filter": {"ENTITY_ID": "DEAL_STAGE"}}),
        ("crm.deal.list", {"select": ["ID", "TITLE", "STAGE_ID", "CATEGORY_ID"], "start": 0}),
        ("crm.deal.userfield.list", {}),
        ("userfieldconfig.list", {"moduleId": "crm", "filter": {"entityId": "CRM_DEAL"}}),
    ]:
        ok, res = app_call(method, payload)
        if ok:
            r = res.get("result")
            if isinstance(r, dict):
                inner = r.get("categories") or r.get("items") or r.get("fields")
                n = len(inner) if isinstance(inner, (list, dict)) else None
                print(f"OK  {method}: dict keys={list(r.keys())[:6]}" + (f" inner_count={n}" if n is not None else ""))
            elif isinstance(r, list):
                print(f"OK  {method}: list len={len(r)}")
            else:
                print(f"OK  {method}: {str(r)[:120]}")
        else:
            print(f"ERR {method}: {res}")
