#!/usr/bin/env python3
"""Smoke-test every OpenAI Codex credential in the active Hermes profile.

Usage examples:
  HERMES_HOME=/root/.hermes PYTHONPATH=/usr/local/lib/hermes-agent \
    /usr/local/lib/hermes-agent/venv/bin/python scripts/check_codex_pool.py

  HERMES_HOME=/root/.hermes/profiles/temuralbery CHECK_PROFILE=temuralbery \
    PYTHONPATH=/usr/local/lib/hermes-agent \
    /usr/local/lib/hermes-agent/venv/bin/python scripts/check_codex_pool.py

Prints labels, HTTP status and errors only; never prints tokens.
"""
from __future__ import annotations

import json
import os
import sys
import time

try:
    from agent.credential_pool import load_pool
except Exception:
    sys.path.insert(0, "/usr/local/lib/hermes-agent")
    from agent.credential_pool import load_pool

import httpx


def main() -> int:
    profile = os.environ.get("CHECK_PROFILE", os.environ.get("HERMES_PROFILE", "default"))
    pool = load_pool("openai-codex")
    entries = pool.entries()
    print(f"PROFILE {profile}: entries={len(entries)}")

    for index, entry in enumerate(entries, 1):
        label = entry.label or entry.id
        status_before = entry.last_status
        refreshed = entry

        try:
            # Codex access tokens expire; use Hermes pool logic so single-use refresh
            # tokens are rotated and persisted safely instead of hand-refreshing.
            pool._current_id = entry.id  # noqa: SLF001 - intentional internal probe
            if entry.auth_type == "oauth" and entry.refresh_token:
                maybe = pool._refresh_entry(entry, force=True)  # noqa: SLF001
                if maybe is not None:
                    refreshed = maybe
        except Exception as exc:
            print(json.dumps({
                "index": index,
                "id": entry.id,
                "label": label,
                "source": entry.source,
                "ok": False,
                "stage": "refresh",
                "error": type(exc).__name__,
                "message": str(exc)[:300],
            }, ensure_ascii=False))
            continue

        token = refreshed.runtime_api_key
        base_url = (refreshed.runtime_base_url or "https://chatgpt.com/backend-api/codex").rstrip("/")
        if not token:
            print(json.dumps({
                "index": index,
                "id": refreshed.id,
                "label": label,
                "source": refreshed.source,
                "ok": False,
                "stage": "token",
                "error": "empty token",
            }, ensure_ascii=False))
            continue

        payload = {
            "model": "gpt-5.5",
            "store": False,
            "instructions": "You are a minimal health-check assistant.",
            "input": [{"role": "user", "content": "Reply with exactly: OK"}],
            # Codex backend requires streaming and rejects some standard
            # Responses parameters such as max_output_tokens.
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        started = time.time()
        try:
            response = httpx.post(f"{base_url}/responses", headers=headers, json=payload, timeout=45)
            elapsed = round(time.time() - started, 2)
            error = None
            if not (200 <= response.status_code < 300):
                try:
                    body = response.json()
                    detail = body.get("error") or body.get("detail") or body.get("message")
                    error = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)[:300]
                except Exception:
                    error = response.text[:300].replace("\n", " ")
            print(json.dumps({
                "index": index,
                "id": refreshed.id,
                "label": label,
                "source": refreshed.source,
                "http": response.status_code,
                "ok": 200 <= response.status_code < 300,
                "seconds": elapsed,
                "status_before": status_before,
                "error": error,
            }, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({
                "index": index,
                "id": refreshed.id,
                "label": label,
                "source": refreshed.source,
                "ok": False,
                "stage": "request",
                "error": type(exc).__name__,
                "message": str(exc)[:300],
            }, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
