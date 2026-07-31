import sys
from urllib.parse import urlsplit

sys.path.insert(0, "/var/www/albery")
from shared.db import load_env_value

parts = urlsplit(
    load_env_value("BITRIX_PORTAL_URL")
    or load_env_value("BITRIX_WEBHOOK_BASE")
)
print(parts.hostname or "")
