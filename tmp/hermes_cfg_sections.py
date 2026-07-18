"""Print the config.yaml sections relevant to the persona/toolsets upgrade (secrets masked)."""
import re
from pathlib import Path

text = Path("/root/.hermes/config.yaml").read_text(encoding="utf-8")
text = re.sub(r"(token|secret|api_key|key|password)(\s*:\s*)(?!\*\*\*)\S+", r"\1\2***", text,
              flags=re.IGNORECASE)
lines = text.splitlines()


def show(start, end, label):
    print(f"\n===== {label} (lines {start}-{end}) =====")
    for i in range(start, min(end, len(lines))):
        print(f"{i:4} {lines[i]}")


# top: model + agent block
show(0, 40, "model/agent head")
# personality area
for i, ln in enumerate(lines):
    if re.match(r"^personality:", ln):
        show(max(i - 5, 0), i + 8, "personality")
# system prompt / persona files
for i, ln in enumerate(lines):
    if "system_prompt" in ln or "persona" in ln.lower():
        print(f"HIT {i:4} {ln}")
# platform_toolsets + telegram platform section
for i, ln in enumerate(lines):
    if re.match(r"^platform_toolsets:", ln):
        show(i, i + 25, "platform_toolsets")
    if re.match(r"^platforms:", ln):
        show(i, i + 60, "platforms")
