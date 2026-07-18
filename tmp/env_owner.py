"""Set TG agent access: only @AlberyAIManager (username whitelist), clear the id list."""
from pathlib import Path

p = Path("/var/www/albery/.env")
lines = [ln for ln in p.read_text(encoding="utf-8").splitlines()
         if not ln.startswith(("TG_AGENT_OWNER_IDS", "TG_AGENT_OWNER_USERNAMES"))]
lines += ["TG_AGENT_OWNER_IDS=", "TG_AGENT_OWNER_USERNAMES=AlberyAIManager"]
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
p.chmod(0o600)
print("owner access set to @AlberyAIManager only")
