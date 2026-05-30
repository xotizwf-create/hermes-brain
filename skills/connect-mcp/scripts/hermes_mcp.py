#!/usr/bin/env python3
"""hermes_mcp — non-interactive manager for Hermes MCP connectors.

Hermes' native `hermes mcp add` is **interactive** (it prompts "Enable all tools?" and,
for header auth, asks for the token on a TTY). That can't be driven from a Telegram tool
call or a cron job. This wrapper writes the **same canonical schema** the native CLI uses,
straight into the `mcp_servers` section of ~/.hermes/config.yaml — no TTY needed — so the
owner can just paste an MCP URL to the bot and Hermes connects itself.

Canonical entry schema (from the bundled native-mcp skill):
    mcp_servers:
      <name>:
        url: "https://host/mcp/..."     # HTTP transport (secret may be in the path)
        headers: {Authorization: "Bearer ${ENV}"}   # optional, for header auth
        enabled: true                   # native on/off switch — read by discovery + `hermes mcp list`
        timeout: 120                    # optional
        connect_timeout: 60             # optional

Switching connectors = the native `enabled` flag (true/false). Disabled servers stay in the
file; Hermes' discovery and `hermes mcp list` skip them.

Apply changes live WITHOUT a restart: in the Telegram chat send **/reload-mcp** (the gateway
reconnects/adds/removes servers and reports the new tool count). `--restart` is a heavier
fallback (systemctl restart hermes-gateway). Either way the config is read fresh.

Safety: default is DRY-RUN; nothing is written until --apply. Every write backs up config.yaml
first (rollback restores it). Secrets (URL paths, tokens) live only in config.yaml (600) and
are redacted in all output; the brain registry gets a secret-free `url_template`.

Usage:
  python3 hermes_mcp.py list
  python3 hermes_mcp.py add <name> --url <url> [--bearer-env ENV | --header "K: V"]
                                 [--timeout N] [--connect-timeout N] [--apply] [--restart]
  python3 hermes_mcp.py disable <name> [--apply] [--restart]
  python3 hermes_mcp.py enable  <name> [--apply] [--restart]
  python3 hermes_mcp.py remove  <name> [--apply] [--restart]
  python3 hermes_mcp.py test    <name>             # hermes mcp test (connect + discover)
  python3 hermes_mcp.py registry-snippet <name>
  python3 hermes_mcp.py rollback                   # restore the most recent backup + restart
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):  # emoji/utf-8 safe on any console
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required (it ships in the Hermes venv): pip install pyyaml")

CONFIG = Path(os.environ.get("HERMES_CONFIG", "/root/.hermes/config.yaml"))
KEY = "mcp_servers"
GATEWAY_UNIT = os.environ.get("HERMES_GATEWAY_UNIT", "hermes-gateway")
URL_RE = re.compile(r"^https?://", re.I)


# --------------------------------------------------------------------------- io

def load() -> dict:
    if not CONFIG.exists():
        sys.exit(f"config not found: {CONFIG} (set HERMES_CONFIG to override)")
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        sys.exit(f"config is not a YAML mapping: {CONFIG}")
    return data


def servers(data: dict) -> dict:
    block = data.get(KEY)
    if block is None:
        return {}
    if not isinstance(block, dict):
        sys.exit(f"'{KEY}' in config is not a mapping; refusing to touch it.")
    return block


def backup() -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = CONFIG.with_suffix(CONFIG.suffix + f".bak.{stamp}")
    shutil.copy2(CONFIG, dst)
    return dst


def write(data: dict) -> None:
    """Atomic write with a YAML round-trip guard; never leaves a half-written file."""
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    yaml.safe_load(text)  # parse-back guard
    tmp = CONFIG.with_suffix(CONFIG.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG)


def apply_live(restart: bool) -> None:
    if restart:
        print(f"→ systemctl restart {GATEWAY_UNIT}")
        try:
            r = subprocess.run(["systemctl", "restart", GATEWAY_UNIT], capture_output=True, text=True)
        except OSError as e:  # off-server / no systemctl — config is already written, don't crash
            print(f"  WARNING: could not run systemctl ({e}). Restart manually: systemctl restart {GATEWAY_UNIT}")
            return
        print("  gateway restarted." if r.returncode == 0 else f"  WARNING: restart failed: {r.stderr.strip()}")
        print("  ⚠ Now write /reset (or /new) in Telegram so the session reloads tools.")
    else:
        print("→ To apply live WITHOUT a restart: send /reload-mcp in the Telegram chat.")
        print("  (It reconnects servers and reports the new tool count. No session is lost.)")


# ----------------------------------------------------------------------- redact

def entry_url(entry) -> str | None:
    if isinstance(entry, dict):
        v = entry.get("url")
        if isinstance(v, str) and URL_RE.match(v):
            return v
    return None


def redact(url: str | None) -> str:
    if not url:
        return "—"
    m = re.match(r"^(https?://[^/]+/.*/)([^/?#]{12,})(/?[?#].*)?$", url)
    if m:
        return f"{m.group(1)}<secret>{m.group(3) or ''}"
    m = re.match(r"^(https?://[^/]+/)([^/?#]{16,})$", url)
    return f"{m.group(1)}<secret>" if m else url


def secret_ref_url(url: str, name: str) -> str:
    m = re.match(r"^(https?://[^/]+/.*/)([^/?#]{12,})(/?.*)?$", url)
    if m:
        return f"{m.group(1)}{{proj/<slug>/{name}/secret}}{m.group(3) or ''}"
    return redact(url)


def is_enabled(entry) -> bool:
    if not isinstance(entry, dict):
        return True
    v = entry.get("enabled", True)
    return v.lower() in {"true", "1", "yes"} if isinstance(v, str) else bool(v)


def describe(entry) -> str:
    if isinstance(entry, dict) and "command" in entry:
        return f"stdio: {entry['command']} {' '.join(entry.get('args', []))}".strip()
    return redact(entry_url(entry))


# --------------------------------------------------------------------- commands

def cmd_list(_a) -> int:
    data = load()
    block = servers(data)
    print(f"config: {CONFIG}")
    if not block:
        print("\n(no MCP servers configured)")
        return 0
    print(f"\nMCP servers ({len(block)}):")
    for name, entry in block.items():
        mark = "🟢 enabled " if is_enabled(entry) else "⚪ disabled"
        print(f"  {mark}  {name:<16} {describe(entry)}")
    return 0


def cmd_add(a) -> int:
    if not a.url or not URL_RE.match(a.url):
        sys.exit("add requires --url starting with http:// or https://")
    data = load()
    block = servers(data)
    if a.name in block:
        sys.exit(f"connector '{a.name}' already exists — `remove` it first or pick another name.")

    entry: dict = {"url": a.url}
    if a.bearer_env:
        entry["headers"] = {"Authorization": f"Bearer ${{{a.bearer_env}}}"}
    for h in a.header or []:
        k, _, v = h.partition(":")
        entry.setdefault("headers", {})[k.strip()] = v.strip()
    if a.timeout:
        entry["timeout"] = a.timeout
    if a.connect_timeout:
        entry["connect_timeout"] = a.connect_timeout
    entry["enabled"] = True

    shown = dict(entry)
    if "url" in shown:
        shown["url"] = redact(shown["url"])
    print(f"Would add to {KEY}:")
    print("  " + yaml.safe_dump({a.name: shown}, allow_unicode=True, sort_keys=False).replace("\n", "\n  ").rstrip())
    if a.bearer_env:
        print(f"\nnote: token is referenced as ${{{a.bearer_env}}} — put the real value in "
              f"{CONFIG.parent}/.env as {a.bearer_env}=... (600), never in the brain.")

    if not a.apply:
        print("\n(dry-run) re-run with --apply to write config.")
        return 0
    print(f"backup: {backup()}")
    data.setdefault(KEY, {})[a.name] = entry
    write(data)
    print(f"added '{a.name}'. Validate it now:  python3 {Path(__file__).name} test {a.name}")
    apply_live(a.restart)
    print(f"Then register it in the brain:  python3 {Path(__file__).name} registry-snippet {a.name}")
    return 0


def _set_enabled(name: str, value: bool, apply: bool, restart: bool) -> int:
    data = load()
    block = servers(data)
    if name not in block:
        sys.exit(f"connector '{name}' not found.")
    if not isinstance(block[name], dict):
        sys.exit(f"entry '{name}' is not a mapping; edit config.yaml by hand.")
    verb = "enable" if value else "disable"
    if is_enabled(block[name]) == value:
        print(f"'{name}' is already {verb}d — nothing to do.")
        return 0
    print(f"Would {verb} '{name}' (set enabled: {value}).")
    if not apply:
        print("(dry-run) re-run with --apply.")
        return 0
    print(f"backup: {backup()}")
    data[KEY][name]["enabled"] = value
    write(data)
    print(f"{verb}d '{name}'.")
    apply_live(restart)
    return 0


def cmd_enable(a) -> int:
    return _set_enabled(a.name, True, a.apply, a.restart)


def cmd_disable(a) -> int:
    return _set_enabled(a.name, False, a.apply, a.restart)


def cmd_remove(a) -> int:
    data = load()
    block = servers(data)
    if a.name not in block:
        sys.exit(f"connector '{a.name}' not found.")
    print(f"Would REMOVE '{a.name}' from {KEY} (backup is kept; rollback restores it).")
    if not a.apply:
        print("(dry-run) re-run with --apply.")
        return 0
    print(f"backup: {backup()}")
    data[KEY].pop(a.name)
    write(data)
    print(f"removed '{a.name}'.")
    apply_live(a.restart)
    return 0


def cmd_test(a) -> int:
    print(f"→ hermes mcp test {a.name}")
    try:
        r = subprocess.run(["hermes", "mcp", "test", a.name], capture_output=True, text=True)
    except OSError as e:
        sys.exit(f"could not run hermes: {e}")
    sys.stdout.write(r.stdout)
    if r.stderr.strip():
        sys.stderr.write(r.stderr)
    return r.returncode


def cmd_registry_snippet(a) -> int:
    block = servers(load())
    if a.name not in block:
        sys.exit(f"connector '{a.name}' not found.")
    entry = block[a.name]
    url = entry_url(entry) or ""
    has_url_secret = bool(re.search(r"/[^/?#]{12,}/?($|[?#])", url))
    print("# paste into connectors/registry.yaml (commit under approval) — no secret included:")
    print(yaml.safe_dump({"connectors": [{
        "slug": a.name,
        "url_template": secret_ref_url(url, a.name) if has_url_secret else (url or "<url>"),
        "transport": "http",
        "auth": "none" if has_url_secret else ("header" if isinstance(entry, dict) and entry.get("headers") else "none"),
        "enabled": is_enabled(entry),
        "scope": "<one line: what this MCP server is for + tools count>",
    }]}, allow_unicode=True, sort_keys=False))
    return 0


def cmd_rollback(_a) -> int:
    backups = sorted(CONFIG.parent.glob(CONFIG.name + ".bak.*"))
    if not backups:
        sys.exit("no backups found.")
    latest = backups[-1]
    shutil.copy2(latest, CONFIG)
    os.chmod(CONFIG, 0o600)
    print(f"restored {CONFIG} from {latest}")
    apply_live(restart=True)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="hermes_mcp", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(fn=cmd_list)

    a = sub.add_parser("add")
    a.add_argument("name")
    a.add_argument("--url", required=True)
    a.add_argument("--bearer-env", dest="bearer_env", default="",
                   help="name of an env var in ~/.hermes/.env holding the bearer token")
    a.add_argument("--header", action="append", help='extra HTTP header "Key: Value" (repeatable)')
    a.add_argument("--timeout", type=int)
    a.add_argument("--connect-timeout", dest="connect_timeout", type=int)
    a.add_argument("--apply", action="store_true")
    a.add_argument("--restart", action="store_true", help="hard restart gateway instead of /reload-mcp")
    a.set_defaults(fn=cmd_add)

    for name, fn in (("enable", cmd_enable), ("disable", cmd_disable), ("remove", cmd_remove)):
        s = sub.add_parser(name)
        s.add_argument("name")
        s.add_argument("--apply", action="store_true")
        s.add_argument("--restart", action="store_true")
        s.set_defaults(fn=fn)

    t = sub.add_parser("test")
    t.add_argument("name")
    t.set_defaults(fn=cmd_test)

    rs = sub.add_parser("registry-snippet")
    rs.add_argument("name")
    rs.set_defaults(fn=cmd_registry_snippet)

    sub.add_parser("rollback").set_defaults(fn=cmd_rollback)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
