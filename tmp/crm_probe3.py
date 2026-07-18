"""Write-path probe on the bot-portal CRM via the app OAuth token.
Creates a clearly-labeled TEST pipeline + stage + deal userfield, then deletes everything.
Every step prints result; nothing permanent is left behind."""
import sys

sys.path.insert(0, "/var/www/albery")
import b24bot  # noqa: E402

endpoint, token = b24bot._b24_app_access_token()
assert token, "no app token"


def call(method, payload):
    try:
        return True, b24bot._b24_app_call(endpoint, token, method, payload)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:300]


def show(label, ok, res):
    print(("OK  " if ok else "ERR ") + label + ": " + str(res)[:400])
    return ok, res


# 1) create test pipeline
ok, res = call("crm.category.add", {"entityTypeId": 2, "fields": {"name": "ТЕСТ ВОРОНКА — УДАЛИТЬ", "sort": 9999}})
show("crm.category.add", ok, res)
cat_id = None
if ok:
    r = res.get("result") or {}
    cat_id = (r.get("category") or {}).get("id") if isinstance(r, dict) else None
print("cat_id =", cat_id)
if not cat_id:
    sys.exit(1)

# 2) list stages of the new pipeline
ok, res = call("crm.status.list", {"filter": {"ENTITY_ID": f"DEAL_STAGE_{cat_id}"}})
show("stages of new cat", ok, res)

# 3) add a custom stage
ok, res = call("crm.status.add", {"fields": {
    "ENTITY_ID": f"DEAL_STAGE_{cat_id}", "STATUS_ID": f"C{cat_id}:TESTSTAGE",
    "NAME": "Тестовая стадия", "SORT": 15}})
show("crm.status.add", ok, res)
status_row_id = res.get("result") if ok else None

# 4) update the stage
ok, res = call("crm.status.update", {"id": status_row_id, "fields": {"NAME": "Тестовая стадия 2"}})
show("crm.status.update", ok, res)

# 5) update pipeline name
ok, res = call("crm.category.update", {"entityTypeId": 2, "id": cat_id, "fields": {"name": "ТЕСТ ВОРОНКА 2 — УДАЛИТЬ"}})
show("crm.category.update", ok, res)

# 6) get pipeline
ok, res = call("crm.category.get", {"entityTypeId": 2, "id": cat_id})
show("crm.category.get", ok, res)

# 7) deal userfield add
ok, res = call("crm.deal.userfield.add", {"fields": {
    "FIELD_NAME": "UF_CRM_TEST_DELETE_ME", "USER_TYPE_ID": "string",
    "EDIT_FORM_LABEL": {"ru": "ТЕСТ удалить", "en": "TEST delete"},
    "LIST_COLUMN_LABEL": {"ru": "ТЕСТ удалить", "en": "TEST delete"}}})
show("crm.deal.userfield.add", ok, res)
uf_id = res.get("result") if ok else None

# 7b) userfield list / update
ok, res = call("crm.deal.userfield.list", {"filter": {"FIELD_NAME": "UF_CRM_TEST_DELETE_ME"}})
show("crm.deal.userfield.list", ok, res)
ok, res = call("crm.deal.userfield.update", {"id": uf_id, "fields": {"MANDATORY": "N", "EDIT_FORM_LABEL": {"ru": "ТЕСТ2", "en": "TEST2"}}})
show("crm.deal.userfield.update", ok, res)

# 8) cleanup: delete userfield, stage, pipeline
if uf_id:
    ok, res = call("crm.deal.userfield.delete", {"id": uf_id})
    show("crm.deal.userfield.delete", ok, res)
if status_row_id:
    ok, res = call("crm.status.delete", {"id": status_row_id})
    show("crm.status.delete", ok, res)
ok, res = call("crm.category.delete", {"entityTypeId": 2, "id": cat_id})
show("crm.category.delete", ok, res)

# verify gone
ok, res = call("crm.category.get", {"entityTypeId": 2, "id": cat_id})
show("crm.category.get (after delete, expect ERR)", ok, res)
