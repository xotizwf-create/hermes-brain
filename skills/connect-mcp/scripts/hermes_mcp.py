#!/usr/bin/env python3
"""hermes_mcp — non-interactive manager for Hermes MCP connectors.

Hermes' native `hermes mcp add` is interactive (TTY prompts), so it can't be driven from a
Telegram tool call. This wrapper writes the same canonical `mcp_servers` schema into
~/.hermes/config.yaml non-interactively, so the owner can paste an MCP URL and Hermes connects
itself.

All OWNER-FACING output is in Russian and free of technical noise (no paths, commands, ids or
stack traces) — see profile/communication.md. Code comments/docstrings stay English (not shown).

Naming flow (MANDATORY): `probe --url <url>` connects and lists the tools WITHOUT saving, and
ends by asking the owner for a name. NEVER invent a name yourself — wait for the owner's answer,
then `add <name> --url <url>` (the name is slugified to a safe MCP id automatically).

Refresh is an INFRA action, not an LLM one: `refresh --apply` restarts the gateway so it
re-discovers every server's tools. A systemd timer (skills/connect-mcp/systemd/) runs it daily.

Usage:
  python3 hermes_mcp.py probe --url <url>
  python3 hermes_mcp.py list
  python3 hermes_mcp.py add <name> --url <url> [--bearer-env ENV | --header "K: V"]
                                 [--timeout N] [--connect-timeout N] [--apply] [--restart]
  python3 hermes_mcp.py disable <name> [--apply] [--restart]
  python3 hermes_mcp.py enable  <name> [--apply] [--restart]
  python3 hermes_mcp.py remove  <name> [--apply] [--restart]
  python3 hermes_mcp.py test    <name>
  python3 hermes_mcp.py refresh [--apply]
  python3 hermes_mcp.py registry-snippet <name>
  python3 hermes_mcp.py rollback
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

for _s in (sys.stdout, sys.stderr):  # utf-8/emoji safe on any console
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import yaml
except ImportError:
    print("Не найдена библиотека YAML в окружении Hermes.")
    raise SystemExit(1)

CONFIG = Path(os.environ.get("HERMES_CONFIG", "/root/.hermes/config.yaml"))
KEY = "mcp_servers"
GATEWAY_UNIT = os.environ.get("HERMES_GATEWAY_UNIT", "hermes-gateway")
URL_RE = re.compile(r"^https?://", re.I)
RELOAD_HINT = "Изменения подхватятся автоматически — ничего больше делать не нужно."

# Cyrillic → latin, for turning a human name ("Простые поставки") into a safe id.
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e",
    "ю": "yu", "я": "ya",
}


def fail(msg: str) -> "NoReturn":
    """Print a human Russian message to stdout (relayed to the owner) and exit non-zero."""
    print(msg)
    raise SystemExit(1)


def slugify(name: str) -> str:
    s = "".join(_TRANSLIT.get(ch, ch) for ch in name.strip().lower())
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


# --------------------------------------------------------------------------- io

def load() -> dict:
    if not CONFIG.exists():
        fail("Файл конфигурации Hermes не найден.")
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        fail("Конфигурация Hermes повреждена — не похоже на корректный файл.")
    return data


def servers(data: dict) -> dict:
    block = data.get(KEY)
    if block is None:
        return {}
    if not isinstance(block, dict):
        fail("Раздел MCP-серверов в конфигурации повреждён — не трогаю его.")
    return block


def backup() -> None:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(CONFIG, CONFIG.with_suffix(CONFIG.suffix + f".bak.{stamp}"))


def write(data: dict) -> None:
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    yaml.safe_load(text)  # parse-back guard
    tmp = CONFIG.with_suffix(CONFIG.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG)


def detached_restart(delay: int = 4) -> bool:
    """Restart the gateway OUT of its own cgroup, after a short delay.

    Restarting hermes-gateway synchronously from inside a gateway turn is self-defeating:
    `systemctl restart` tears down the whole service cgroup, which includes THIS process —
    the one currently answering the owner. The turn dies mid-reply ("Gateway shutting down")
    and the owner gets garbage. `systemd-run` launches the restart as a SEPARATE transient
    unit (run by PID 1, outside our cgroup), so it survives our death, and `--on-active`
    delays it a few seconds — long enough for the current reply to be delivered first.
    """
    unit = f"hermes-gateway-refresh-{dt.datetime.now():%H%M%S}"
    cmd = ["systemd-run", "--collect", f"--unit={unit}",
           f"--on-active={delay}", "systemctl", "restart", GATEWAY_UNIT]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except OSError:
        return False
    return r.returncode == 0


def apply_live(restart: bool) -> None:
    if not restart:
        print(RELOAD_HINT)
        return
    if detached_restart():
        print("🔄 Перезапускаюсь, чтобы применить — несколько секунд, секунду не пиши.")
    else:
        print("⚠️ Не получилось перезапуститься автоматически. Скажи ещё раз чуть позже.")


# ----------------------------------------------------------------------- redact

def entry_url(entry) -> str | None:
    if isinstance(entry, dict):
        v = entry.get("url")
        if isinstance(v, str) and URL_RE.match(v):
            return v
    return None


def host_of(url: str | None) -> str:
    m = re.match(r"^https?://([^/]+)", url or "")
    return m.group(1) if m else "—"


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


# --------------------------------------------------------------------- commands

def cmd_probe(a) -> int:
    if not a.url or not URL_RE.match(a.url):
        fail("Нужна ссылка на MCP-сервер, начинающаяся с http:// или https://")
    try:
        from hermes_cli.mcp_config import _probe_single_server
    except Exception:
        fail("Проверку можно запускать только внутри окружения Hermes.")
    cfg = {"url": a.url}
    for h in a.header or []:
        k, _, v = h.partition(":")
        cfg.setdefault("headers", {})[k.strip()] = v.strip()
    if a.bearer_env:
        cfg.setdefault("headers", {})["Authorization"] = f"Bearer ${{{a.bearer_env}}}"
    print("Подключаюсь к серверу…")
    try:
        tools = _probe_single_server("probe", cfg, connect_timeout=a.connect_timeout or 30)
    except Exception:
        fail("❌ Не удалось подключиться к серверу. Проверь ссылку и доступность сервера.")
    print(f"✅ Подключился. Инструментов: {len(tools)}")
    for name, desc in tools:
        short = (desc[:70] + "…") if len(desc) > 70 else desc
        print(f"  • {name}{(' — ' + short) if short else ''}")
    print("\nКак назовём этот сервер?")
    return 0


def cmd_list(_a) -> int:
    block = servers(load())
    if not block:
        print("MCP-серверов пока нет.")
        return 0
    print("MCP-серверы:")
    for name, entry in block.items():
        mark = "🟢 включён " if is_enabled(entry) else "⚪ выключен"
        print(f"  {mark}  {name}  ({host_of(entry_url(entry))})")
    return 0


def cmd_add(a) -> int:
    if not a.url or not URL_RE.match(a.url):
        fail("Нужна ссылка на MCP-сервер (http/https).")
    name = slugify(a.name)
    if not name:
        fail(f"Не получилось сделать имя из «{a.name}». Дай короткое название.")
    data = load()
    block = servers(data)
    if name in block:
        fail(f"Сервер с именем «{name}» уже есть. Выбери другое имя.")

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

    display = a.name.strip()
    note = f" (сохраню как «{name}»)" if name != display else ""
    if not a.apply:
        print(f"Добавлю сервер «{display}»{note}.")
        return 0
    backup()
    data.setdefault(KEY, {})[name] = entry
    write(data)
    print(f"✅ Сервер «{display}» подключён и включён.")
    apply_live(a.restart)
    return 0


def _set_enabled(raw: str, value: bool, apply: bool, restart: bool) -> int:
    name, display = slugify(raw), raw.strip()
    data = load()
    block = servers(data)
    if name not in block:
        fail(f"Сервер «{display}» не найден.")
    if not isinstance(block[name], dict):
        fail(f"Запись сервера «{display}» нестандартная — поправь вручную.")
    word = "включён" if value else "выключен"
    if is_enabled(block[name]) == value:
        print(f"Сервер «{display}» уже {word}.")
        return 0
    if not apply:
        print(f"{'Включу' if value else 'Выключу'} сервер «{display}».")
        return 0
    backup()
    data[KEY][name]["enabled"] = value
    write(data)
    print(f"✅ Сервер «{display}» {word}.")
    apply_live(restart)
    return 0


def cmd_enable(a) -> int:
    return _set_enabled(a.name, True, a.apply, a.restart)


def cmd_disable(a) -> int:
    return _set_enabled(a.name, False, a.apply, a.restart)


def cmd_remove(a) -> int:
    name, display = slugify(a.name), a.name.strip()
    data = load()
    block = servers(data)
    if name not in block:
        fail(f"Сервер «{display}» не найден.")
    if not a.apply:
        print(f"Удалю сервер «{display}».")
        return 0
    backup()
    data[KEY].pop(name)
    write(data)
    print(f"✅ Сервер «{display}» удалён.")
    apply_live(a.restart)
    return 0


def cmd_test(a) -> int:
    name = slugify(a.name)
    try:
        r = subprocess.run(["hermes", "mcp", "test", name], capture_output=True, text=True)
    except OSError:
        fail("Не удалось запустить проверку в окружении Hermes.")
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode == 0:
        print(f"✅ Сервер «{name}» на связи.")
    else:
        print(f"❌ Сервер «{name}» не отвечает. Проверь ссылку и доступность.")
    return r.returncode


def cmd_refresh(a) -> int:
    if not a.apply:
        print("Обновлю инструменты — заново подключусь ко всем серверам и подтяну новые. Несколько секунд.")
        return 0
    # NB: the daily systemd timer runs this same command from its OWN unit, where a direct
    # restart is fine. From a chat turn it is NOT — see detached_restart(). Always detach.
    if detached_restart():
        print("🔄 Обновляю инструменты — несколько секунд. Новые подтянутся сами, "
              "секунду не пиши: я перезапускаюсь.")
        return 0
    fail("Не получилось запустить обновление. Попробуй ещё раз чуть позже.")


def cmd_registry_snippet(a) -> int:
    name = slugify(a.name)
    block = servers(load())
    if name not in block:
        fail(f"Сервер «{name}» не найден.")
    entry = block[name]
    url = entry_url(entry) or ""
    has_url_secret = bool(re.search(r"/[^/?#]{12,}/?($|[?#])", url))
    # YAML for the brain registry (developer step) — secret stripped.
    print(yaml.safe_dump({"connectors": [{
        "slug": name,
        "url_template": secret_ref_url(url, name) if has_url_secret else (url or "<url>"),
        "transport": "http",
        "auth": "none" if has_url_secret else ("header" if isinstance(entry, dict) and entry.get("headers") else "none"),
        "enabled": is_enabled(entry),
        "scope": "<one line>",
    }]}, allow_unicode=True, sort_keys=False))
    return 0


def cmd_rollback(_a) -> int:
    backups = sorted(CONFIG.parent.glob(CONFIG.name + ".bak.*"))
    if not backups:
        fail("Резервных копий конфигурации не найдено.")
    shutil.copy2(backups[-1], CONFIG)
    os.chmod(CONFIG, 0o600)
    print("Откатил конфигурацию к последней резервной копии.")
    apply_live(restart=True)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="hermes_mcp", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(fn=cmd_list)

    pr = sub.add_parser("probe")
    pr.add_argument("--url", required=True)
    pr.add_argument("--bearer-env", dest="bearer_env", default="")
    pr.add_argument("--header", action="append")
    pr.add_argument("--connect-timeout", dest="connect_timeout", type=int)
    pr.set_defaults(fn=cmd_probe)

    rf = sub.add_parser("refresh")
    rf.add_argument("--apply", action="store_true")
    rf.set_defaults(fn=cmd_refresh)

    a = sub.add_parser("add")
    a.add_argument("name")
    a.add_argument("--url", required=True)
    a.add_argument("--bearer-env", dest="bearer_env", default="")
    a.add_argument("--header", action="append")
    a.add_argument("--timeout", type=int)
    a.add_argument("--connect-timeout", dest="connect_timeout", type=int)
    a.add_argument("--apply", action="store_true")
    a.add_argument("--restart", action="store_true")
    a.set_defaults(fn=cmd_add)

    for nm, fn in (("enable", cmd_enable), ("disable", cmd_disable), ("remove", cmd_remove)):
        s = sub.add_parser(nm)
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
