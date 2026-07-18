"""Check event bindings after deploy; bind explicitly if the startup thread hasn't yet."""
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import b24bot  # noqa: E402

endpoint, token = b24bot._b24_app_access_token()
data = b24bot._b24_app_call(endpoint, token, "event.get", {})
rows = data.get("result") or []
print("bindings now:", [(e.get("event"), str(e.get("handler"))[:70]) for e in rows])

need = {"ONTASKCOMMENTADD", "ONTASKCOMMENTUPDATE"}
have = {str(e.get("event") or "").upper() for e in rows}
if not need <= have:
    b24bot._B24_TASK_EVENT_BIND_CHECKED = False
    b24bot._b24_ensure_task_comment_event_bound(endpoint, token)
    data = b24bot._b24_app_call(endpoint, token, "event.get", {})
    print("bindings after ensure:", [(e.get("event"), str(e.get("handler"))[:70])
                                     for e in (data.get("result") or [])])
else:
    print("already bound by the service startup thread")
