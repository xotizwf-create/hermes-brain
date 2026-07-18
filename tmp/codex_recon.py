"""Recon before touching codex CLI: how is it installed, where are creds, is it in hermes' path?"""
import json
import os
import subprocess
from pathlib import Path


def run(cmd, timeout=60):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str))
    return (r.stdout or "") + (r.stderr or "")


print("=== codex binary ===")
print("which:", run("which codex").strip())
print("version:", run("codex --version").strip()[:60])
print("realpath:", run("readlink -f $(which codex)").strip())
print("npm global?:", run("npm ls -g --depth=0 2>/dev/null | grep -i codex").strip() or "(not npm-global)")

print("\n=== creds locations (existence + mtime only, NO contents) ===")
for p in ("/root/.codex/auth.json", "/root/.codex/config.toml", "/root/.hermes/credentials.json",
          "/root/.hermes/auth.json", "/root/.hermes/secure/"):
    path = Path(p)
    print(f"  {p}: {'EXISTS' if path.exists() else 'no'}"
          + (f" mtime={path.stat().st_mtime:.0f} size={path.stat().st_size if path.is_file() else '-'}"
             if path.exists() else ""))

print("\n=== hermes credential store (accounts, no secrets) ===")
out = run(["hermes", "auth", "status"], timeout=90)
print(out[:900])

print("\n=== does hermes SHELL OUT to the codex binary? ===")
hermes_pkg = run("python3 -c \"import hermes,os;print(os.path.dirname(hermes.__file__))\"").strip()
print("hermes pkg:", hermes_pkg)
if hermes_pkg and Path(hermes_pkg).is_dir():
    hits = run(f"grep -rl --include=*.py -E '\\bcodex\\b.*(subprocess|Popen|exec)|(subprocess|Popen).*codex' {hermes_pkg} | head -5")
    print("files invoking codex binary:", hits.strip() or "(none found — provider talks HTTP itself)")
    prov = run(f"grep -rl --include=*.py 'openai-codex\\|openai_codex' {hermes_pkg} | head -5")
    print("provider impl files:", prov.strip()[:400])

print("\n=== codex login status ===")
print(run(["codex", "login", "status"], timeout=60)[:300])
