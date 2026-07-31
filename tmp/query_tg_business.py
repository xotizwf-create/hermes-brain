import hashlib
import pathlib
import sys

sys.path.insert(0, "/var/www/albery")
import tg_agent

tg_agent._load_env_file()
state = tg_agent.load_state()
business = state.get("business") or {}

for idx, connection_id in enumerate(business, 1):
    masked = hashlib.sha256(str(connection_id).encode()).hexdigest()[:12]
    try:
        current = tg_agent.api(
            "getBusinessConnection",
            business_connection_id=connection_id,
        )
    except Exception as exc:
        message = str(exc).replace(str(connection_id), "<connection>")
        print(f"connection_{idx}=sha256:{masked} query=error detail={message[:240]}")
        continue
    rights = current.get("rights") or {}
    print(
        f"connection_{idx}=sha256:{masked} query=ok "
        f"enabled={current.get('is_enabled')!r} "
        f"can_reply={rights.get('can_reply')!r}"
    )
