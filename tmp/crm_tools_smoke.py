"""End-to-end smoke of the CRM funnel MCP tools, through the real handlers.
Pre-cleans leftovers of previous runs, then creates a clearly-labeled TEST
pipeline/stage/field/deal, exercises every mutation (incl. cross-pipeline move),
then deletes everything it created."""
import sys

sys.path.insert(0, "/var/www/albery")
from mcp import context_server as cs  # noqa: E402

FAILED = []
TEST_PIPELINE = "ТЕСТ-СМОУК — УДАЛИТЬ"


def step(label, fn, *a):
    try:
        res = fn(*a)
        print("OK  " + label + ": " + str(res)[:220])
        return res
    except Exception as exc:  # noqa: BLE001
        FAILED.append(label)
        print("ERR " + label + ": " + str(exc)[:300])
        return None


def cleanup(quiet=True):
    """Remove any TEST pipelines/fields left over from previous runs."""
    pipes = cs.tool_list_crm_pipelines({"include_stages": False, "include_deal_counts": False})
    for p in pipes.get("pipelines", []):
        if p.get("name") != TEST_PIPELINE:
            continue
        cid = p["category_id"]
        deals = cs.tool_list_crm_deals({"category_id": cid, "limit": 200})
        for d in deals.get("deals", []):
            cs.tool_delete_crm_deal({"deal_id": d["deal_id"], "confirm": True})
        for s in cs.tool_list_crm_pipelines({"include_deal_counts": False})["pipelines"]:
            if s["category_id"] != cid:
                continue
            for st in s.get("stages", []):
                if not st.get("system"):
                    try:
                        cs.tool_manage_crm_pipeline_stage(
                            {"action": "delete", "category_id": cid, "stage": st["stage_id"], "confirm": True})
                    except Exception as exc:  # noqa: BLE001
                        print("  cleanup stage skip: " + str(exc)[:120])
        cs.tool_delete_crm_pipeline({"category_id": cid, "confirm": True})
        print("cleanup: removed leftover pipeline id=%s" % cid)
    try:
        cs.tool_manage_crm_deal_field({"action": "delete", "field_code": "UF_CRM_SMOKE_SRC", "confirm": True})
        print("cleanup: removed leftover field UF_CRM_SMOKE_SRC")
    except Exception:  # noqa: BLE001
        pass


cleanup()

# 1) list pipelines
res = step("list_crm_pipelines", cs.tool_list_crm_pipelines, {"include_deal_counts": False})
baseline = len((res or {}).get("pipelines", []))
default_cat = next((p["category_id"] for p in (res or {}).get("pipelines", []) if p.get("is_default")), 0)

# 2) create test pipeline with an extra stage
res = step("create_crm_pipeline", cs.tool_create_crm_pipeline,
           {"name": TEST_PIPELINE, "sort": 9999,
            "stages": [{"name": "Смоук-стадия", "stage_code": "SMOKE1", "color": "#AA00AA"}]})
cid = (res or {}).get("category_id")
if not cid:
    print("FATAL: pipeline not created");  sys.exit(1)

# 3) stage ops
step("stage add (failure)", cs.tool_manage_crm_pipeline_stage,
     {"action": "add", "category_id": cid, "name": "Смоук-провал", "stage_code": "SMOKEFAIL",
      "semantics": "failure"})
step("stage update by name", cs.tool_manage_crm_pipeline_stage,
     {"action": "update", "category_id": cid, "stage": "Смоук-стадия", "new_name": "Смоук-стадия v2",
      "color": "#00AAAA"})

# 4) custom deal field (enumeration)
step("field add (enumeration)", cs.tool_manage_crm_deal_field,
     {"action": "add", "label": "ТЕСТ-СМОУК источник", "field_code": "SMOKE_SRC",
      "type": "enumeration", "list_items": ["Сайт", "Звонок"]})
step("field update", cs.tool_manage_crm_deal_field,
     {"action": "update", "field_code": "UF_CRM_SMOKE_SRC", "label": "ТЕСТ-СМОУК источник v2"})

# 5) deal in the test pipeline
res = step("create_crm_deal", cs.tool_create_crm_deal,
           {"title": "ТЕСТ-СМОУК сделка — УДАЛИТЬ", "category_id": cid, "stage": "Смоук-стадия v2",
            "amount": 12345.67, "comments": "смоук"})
deal_id = (res or {}).get("deal_id")

if deal_id:
    step("update_crm_deal (rename + stage move)", cs.tool_update_crm_deal,
         {"deal_id": deal_id, "title": "ТЕСТ-СМОУК сделка v2 — УДАЛИТЬ", "stage": "SMOKEFAIL"})
    step("move to default pipeline", cs.tool_update_crm_deal,
         {"deal_id": deal_id, "category_id": default_cat})
    got = step("get_crm_deal after move", cs.tool_get_crm_deal, {"deal_id": deal_id})
    if got and got.get("category_id") != default_cat:
        FAILED.append("cross-pipeline move did not stick")
        print("ERR cross-pipeline move did not stick: category_id=" + str(got.get("category_id")))
    step("move back to test pipeline", cs.tool_update_crm_deal,
         {"deal_id": deal_id, "category_id": cid, "stage": "Смоук-стадия v2"})
    step("list_crm_deals filtered", cs.tool_list_crm_deals,
         {"category_id": cid, "search": "СМОУК", "include_custom_fields": True})
    try:
        cs.tool_delete_crm_deal({"deal_id": deal_id})
        FAILED.append("delete_crm_deal without confirm was NOT refused")
    except cs.McpError:
        print("OK  delete_crm_deal refuses without confirm")
    title_now = (cs.tool_get_crm_deal({"deal_id": deal_id}) or {}).get("title") or ""
    step("delete_crm_deal", cs.tool_delete_crm_deal,
         {"deal_id": deal_id, "confirm": True, "expected_title": title_now})

# 9) cleanup: field, stages, pipeline
step("field delete", cs.tool_manage_crm_deal_field,
     {"action": "delete", "field_code": "UF_CRM_SMOKE_SRC", "confirm": True})
step("stage delete SMOKE1", cs.tool_manage_crm_pipeline_stage,
     {"action": "delete", "category_id": cid, "stage": "SMOKE1", "confirm": True})
step("stage delete SMOKEFAIL", cs.tool_manage_crm_pipeline_stage,
     {"action": "delete", "category_id": cid, "stage": "SMOKEFAIL", "confirm": True})
step("delete_crm_pipeline", cs.tool_delete_crm_pipeline,
     {"category_id": cid, "confirm": True, "expected_name": TEST_PIPELINE})

# 10) final state must equal the baseline
res = step("final list_crm_pipelines", cs.tool_list_crm_pipelines, {"include_stages": False})
final = (res or {}).get("pipelines", [])
if len(final) != baseline:
    FAILED.append("pipeline count %s != baseline %s" % (len(final), baseline))
print("\nFINAL pipelines: " + "; ".join(
    f"{p['category_id']}—{p['name']}({p.get('deals_total')})" for p in final))
print("SMOKE " + ("FAILED: " + ", ".join(FAILED) if FAILED else "OK"))
sys.exit(1 if FAILED else 0)
