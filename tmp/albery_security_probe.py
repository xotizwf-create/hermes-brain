from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


env = dotenv_values(Path("/var/www/albery/.env"))


def configured(name: str) -> str:
    value = str(env.get(name) or "").strip()
    return "yes" if value else "no"


def enabled(name: str) -> str:
    value = str(env.get(name) or "").strip().lower()
    return "yes" if value in {"1", "true", "yes", "on"} else "no"


print("FLASK_SECRET_KEY configured:", configured("FLASK_SECRET_KEY"))
print("ADMIN_PASSWORD_HASH configured:", configured("ADMIN_PASSWORD_HASH"))
print("MCP_SHARED_SECRET configured:", configured("MCP_SHARED_SECRET"))
print("MCP_ALLOW_UNAUTHENTICATED enabled:", enabled("MCP_ALLOW_UNAUTHENTICATED"))
print("MCP_ALLOW_PATH_TOKEN enabled:", enabled("MCP_ALLOW_PATH_TOKEN"))
print("ALLOW_LEGACY_HTTP_API enabled:", enabled("ALLOW_LEGACY_HTTP_API"))
print("SESSION_COOKIE_SECURE disabled:", "yes" if enabled("SESSION_COOKIE_SECURE") == "no" and str(env.get("SESSION_COOKIE_SECURE") or "").strip() else "no")
print("FLASK_ENV development:", "yes" if str(env.get("FLASK_ENV") or "").strip().lower() == "development" else "no")
