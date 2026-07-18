"""Read-only probe: which crm.* REST methods the Albery webhooks are allowed to call.
Prints portal host (no tokens) + per-method ok/error summary. Run on the prod box."""
import json
import urllib.error
import urllib.parse
import urllib.request

ENV_PATH = "/var/www/albery/.env"


def load_env(key: str) -> str:
    with open(ENV_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def call(base: str, method: str, payload: dict) -> tuple[bool, str]:
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        f"{base}/{method}.json", data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode())
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode()[:200]
        except Exception:
            pass
        return False, f"HTTP {exc.code} {detail}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:200]
    if isinstance(body, dict) and body.get("error"):
        return False, f"{body.get('error')} {body.get('error_description') or ''}"[:200]
    res = body.get("result") if isinstance(body, dict) else body
    if isinstance(res, dict):
        keys = list(res.keys())[:6]
        inner = res.get("categories") or res.get("items") or res.get("fields")
        n = len(inner) if isinstance(inner, (list, dict)) else None
        return True, f"dict keys={keys}" + (f" inner_count={n}" if n is not None else "")
    if isinstance(res, list):
        sample = ""
        if res and isinstance(res[0], dict):
            sample = f" first_keys={list(res[0].keys())[:6]}"
        return True, f"list len={len(res)}{sample}"
    return True, str(res)[:120]


PROBES = [
    ("scope", {}),
    ("crm.category.list", {"entityTypeId": 2}),
    ("crm.dealcategory.list", {}),
    ("crm.status.list", {"filter": {"ENTITY_ID": "DEAL_STAGE"}}),
    ("crm.status.fields", {}),
    ("crm.deal.fields", {}),
    ("crm.deal.userfield.list", {}),
    ("crm.deal.list", {"select": ["ID", "TITLE", "STAGE_ID", "CATEGORY_ID"], "start": 0}),
    ("userfieldconfig.list", {"moduleId": "crm", "filter": {"entityId": "CRM_DEAL"}}),
]

for env_key in ("BITRIX_WEBHOOK_BASE", "B24_TESTBOT_WEBHOOK_BASE"):
    base = load_env(env_key).rstrip("/")
    host = urllib.parse.urlparse(base).netloc if base else "(not set)"
    print(f"\n=== {env_key} -> {host} ===")
    if not base:
        continue
    for method, payload in PROBES:
        ok, info = call(base, method, payload)
        print(f"  {'OK ' if ok else 'ERR'} {method}: {info}")
