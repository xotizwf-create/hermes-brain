"""Repair /var/www/albery/.env: drop the mangled 'nTG_AGENT...' line, append clean TG_AGENT_* keys."""
from pathlib import Path

TOKEN = "8886445861:AAHloRXsQ_QZzik6u24vrq4xzYXKjR9vKJY"
p = Path("/var/www/albery/.env")
lines = p.read_text(encoding="utf-8").splitlines()
lines = [ln for ln in lines if "TG_AGENT_BOT_TOKEN" not in ln and "TG_AGENT_OWNER_IDS" not in ln]
lines += [f"TG_AGENT_BOT_TOKEN={TOKEN}", "TG_AGENT_OWNER_IDS=1451982360"]
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
p.chmod(0o600)
print("env fixed; TG_AGENT lines:", sum(1 for ln in lines if ln.startswith("TG_AGENT")))
