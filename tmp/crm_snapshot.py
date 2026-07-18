"""Snapshot the portal CRM funnel state (pipelines, stages, deal userfields, deals) to a JSON
backup file — rollback reference before enabling funnel-management tools."""
import json
import sys
from datetime import datetime

sys.path.insert(0, "/var/www/albery")
import b24bot  # noqa: E402

endpoint, token = b24bot._b24_app_access_token()
call = lambda m, p: b24bot._b24_app_call(endpoint, token, m, p)  # noqa: E731

snap = {"taken_at": datetime.now().isoformat()}
cats = (call("crm.category.list", {"entityTypeId": 2}).get("result") or {}).get("categories") or []
snap["categories"] = cats
snap["stages"] = {}
for c in cats:
    ent = f"DEAL_STAGE_{c['id']}" if not (str(c.get("isDefault")) == "Y" and int(c["id"]) == 0) else "DEAL_STAGE"
    snap["stages"][str(c["id"])] = call("crm.status.list", {"filter": {"ENTITY_ID": ent}}).get("result") or []
snap["deal_userfields"] = call("crm.deal.userfield.list", {}).get("result") or []
deals = []
start = 0
while True:
    r = call("crm.deal.list", {"select": ["*", "UF_*"], "start": start})
    deals.extend(r.get("result") or [])
    if not r.get("next"):
        break
    start = r["next"]
snap["deals"] = deals

path = f"/var/backups/albery/crm_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(path, "w", encoding="utf-8") as fh:
    json.dump(snap, fh, ensure_ascii=False, indent=1, default=str)
print(f"saved {path}: {len(cats)} pipelines, {len(snap['deal_userfields'])} userfields, {len(deals)} deals")
