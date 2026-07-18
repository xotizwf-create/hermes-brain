# Smoke: automation creator attribution + self-tool guards (run with PYTHONPATH=/var/www/albery).
import app  # noqa: F401
import agent_automations as aa

fake_agent = {"slug": "main", "name": "Агент Албери"}

# 1. schedule with requested_by -> creator_label carries the requester
res = aa.automation_self_tool_call(fake_agent, "schedule_my_automation", {
    "name": "__attr_smoke__", "schedule": "0 7 * * 1",
    "task": "тест", "deliver_to": "22", "requested_by": "Тест Тестов",
})
rows = aa._load_rows("WHERE agent_slug = 'main' AND name = '__attr_smoke__'")
print("label:", rows[0]["creator_label"], "| status json:", aa._automation_json(rows[0])["last_status"] or "(none)")

# 2. requester fallback from deliver_to (numeric dialog = user id)
print("fallback name for 22:", aa._requester_name("", "22") or "(directory empty)")

# 3. too-frequent self schedule is rejected
try:
    aa.automation_self_tool_call(fake_agent, "schedule_my_automation", {
        "name": "__attr_smoke2__", "schedule": "*/5 * * * *",
        "task": "тест", "deliver_to": "22", "requested_by": "X",
    })
    print("freq guard: FAIL (accepted)")
except ValueError as e:
    print("freq guard: OK —", str(e)[:60])

# 4. self delete works; owner rows stay protected (seeded system row)
print("delete self:", aa.automation_self_tool_call(fake_agent, "delete_my_automation", {"name": "__attr_smoke__"}))
try:
    aa.automation_self_tool_call(fake_agent, "delete_my_automation", {"name": "Разбор Zoom-созвонов"})
    print("system protect: FAIL")
except ValueError as e:
    print("system protect: OK —", str(e)[:60])
