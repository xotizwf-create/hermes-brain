"""Verify the persona wiring: which section holds `personality: albery` + a live one-shot turn."""
import subprocess
from pathlib import Path

lines = Path("/root/.hermes/config.yaml").read_text(encoding="utf-8").splitlines()
for i, ln in enumerate(lines):
    if "personality: albery" in ln:
        # walk up to the nearest top-level parent
        j = i
        while j > 0 and (lines[j].startswith(" ") or not lines[j].strip()):
            j -= 1
        print(f"personality: albery at line {i}, top-level parent: {lines[j].strip()}")

out = subprocess.run(["hermes", "-z", "Представься одним предложением: кто ты и что умеешь?",
                      "-t", "albery"],
                     capture_output=True, text=True, timeout=240)
print("turn rc:", out.returncode)
print("answer:", (out.stdout or out.stderr).strip()[:500])
