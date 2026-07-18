"""Recon of the Hermes TG agent on 186 (read-only, secrets masked)."""
import re
import subprocess
from pathlib import Path

cfg = Path("/root/.hermes/config.yaml").read_text(encoding="utf-8")
cfg_masked = re.sub(r"(token|secret|key|password)(\s*:\s*)\S+", r"\1\2***", cfg, flags=re.IGNORECASE)

print("=== config.yaml: model / toolsets / persona-ish keys ===")
for i, line in enumerate(cfg_masked.splitlines()):
    if re.search(r"model|toolset|persona|system_prompt|prompt_file|allowlist|reasoning|compression", line,
                 re.IGNORECASE) and not line.strip().startswith("#"):
        print(f"{i:4} {line}")

print("\n=== connectors (names + url paths only) ===")
for m in re.finditer(r"^\s{2,}([a-z0-9_-]+):\s*$|url:\s*(\S+)", cfg_masked, re.MULTILINE):
    if m.group(1):
        print("connector:", m.group(1))
    elif m.group(2):
        print("   url:", re.sub(r"/[A-Za-z0-9_-]{16,}", "/<token>", m.group(2)))

print("\n=== hermes cron list ===")
out = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=60)
print((out.stdout or out.stderr)[:3000])
