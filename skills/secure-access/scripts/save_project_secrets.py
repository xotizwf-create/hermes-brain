#!/usr/bin/env python3
"""Securely ingest a project's secrets into the server secure store — without ever echoing values.

The owner pastes a project's `.env` (or a prod-server password/key) to Hermes; Hermes writes it here.
Everything lands under /opt/hermes/secure/projects/<slug>/ (dir 2770, files 660, group hermessec) — never in
git, never in chat, never repeated back. Confirmation prints variable NAMES only, never their values.

This is the deliberate exception to "the agent does not type secrets" (engineering/secrets-access.md):
RECEIVING a pasted secret and locking it into the secure zone is allowed; inventing/echoing is not.

Usage (owner-facing output is Russian, value-free):
  # read content from STDIN (preferred — value never appears in argv) or from a file the model wrote:
  save_project_secrets.py save-env    <slug> [--from FILE]
  save_project_secrets.py save-server <slug> --host H --user U [--port N] [--as password|key] [--from FILE]
  save_project_secrets.py show <slug>        # non-secret summary: which secrets exist + var NAMES
  save_project_secrets.py list              # projects that have stored secrets

Env override for testing: HERMES_VAULT_DIR (default /opt/hermes/secure).
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SECURE = Path(os.environ.get("HERMES_VAULT_DIR", "/opt/hermes/secure"))
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,48}[a-z0-9]$")
VAR_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


def fail(msg: str) -> "NoReturn":
    print(msg)
    raise SystemExit(1)


def proj_dir(slug: str) -> Path:
    if not SLUG_RE.match(slug):
        fail(f"Имя проекта «{slug}» не годится. Только латиница в нижнем регистре, цифры и дефис.")
    return SECURE / "projects" / slug


def _read_payload(from_file: str | None) -> str:
    """Read the secret from a file the model already wrote, or from STDIN. Never from argv."""
    if from_file:
        p = Path(from_file)
        if not p.exists():
            fail("Файл с данными не найден.")
        data = p.read_text(encoding="utf-8", errors="replace")
        try:  # the temp paste file is itself sensitive — remove it after ingest
            p.unlink()
        except OSError:
            pass
        return data
    if sys.stdin is None or sys.stdin.isatty():
        fail("Нет данных. Передай содержимое через stdin или --from FILE.")
    return sys.stdin.read()


def _harden(path: Path, mode: int) -> None:
    os.chmod(path, mode)


def _ensure_dir(slug: str) -> Path:
    d = proj_dir(slug)
    d.parent.mkdir(parents=True, exist_ok=True)
    d.mkdir(parents=True, exist_ok=True)
    _harden(d.parent, 0o2770)  # setgid so files inherit group hermessec (agent root + web hermesvault)
    _harden(d, 0o2770)
    return d


def _backup(path: Path) -> None:
    if path.exists():
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        path.replace(path.with_name(path.name + f".bak.{stamp}"))


def var_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = VAR_RE.match(line)
        if m and m.group(1) not in names:
            names.append(m.group(1))
    return names


# ------------------------------------------------------------------ commands

def cmd_save_env(a) -> int:
    d = _ensure_dir(a.slug)
    text = _read_payload(a.from_file)
    if not text.strip():
        fail("Пустой .env — нечего сохранять.")
    names = var_names(text)
    target = d / ".env"
    _backup(target)
    target.write_text(text, encoding="utf-8")
    _harden(target, 0o660)
    if names:
        print(f"✅ Сохранил .env проекта «{a.slug}» в защищённую зону: {len(names)} переменных.")
        print("Переменные (без значений): " + ", ".join(names))
    else:
        print(f"✅ Сохранил .env проекта «{a.slug}» (переменных в формате KEY=VALUE не распознал — "
              f"проверь формат).")
    print("Значения нигде не показываю и в git не кладу.")
    return 0


def cmd_save_server(a) -> int:
    d = _ensure_dir(a.slug)
    secret = _read_payload(a.from_file)
    if not secret.strip():
        fail("Пустой секрет сервера — нечего сохранять.")
    kind = a.as_kind or "password"
    fname = "server_key" if kind == "key" else "server_password"
    target = d / fname
    _backup(target)
    target.write_text(secret if secret.endswith("\n") else secret + "\n", encoding="utf-8")
    _harden(target, 0o660)
    # Non-secret connection facts go into a value-free note for quick server-side recall.
    note = d / "server.txt"
    note.write_text(
        f"host: {a.host}\nuser: {a.user}\nport: {a.port or 22}\nauth: {kind} "
        f"(-> {fname})\nupdated: {dt.datetime.now():%Y-%m-%d %H:%M}\n",
        encoding="utf-8")
    _harden(note, 0o660)
    print(f"✅ Доступ к прод-серверу проекта «{a.slug}» сохранён: {a.user}@{a.host}:{a.port or 22} "
          f"(аутентификация — {kind}).")
    print("Секрет лежит в защищённой зоне, в чат и git не попадает. "
          "Хост и пользователь не секретны — продублируй их в манифесте проекта.")
    return 0


def cmd_show(a) -> int:
    d = proj_dir(a.slug)
    if not d.exists():
        print(f"По проекту «{a.slug}» сохранённых секретов нет.")
        return 0
    print(f"Проект «{a.slug}» — что лежит в защищённой зоне (значения не показываю):")
    env = d / ".env"
    if env.exists():
        names = var_names(env.read_text(encoding="utf-8", errors="replace"))
        print(f"  • .env: {len(names)} переменных — " + (", ".join(names) or "формат не распознан"))
    else:
        print("  • .env: нет")
    note = d / "server.txt"
    if note.exists():
        for line in note.read_text(encoding="utf-8").splitlines():
            print("  • сервер " + line)
    else:
        print("  • прод-сервер: не сохранён")
    return 0


def cmd_list(_a) -> int:
    base = SECURE / "projects"
    if not base.exists():
        print("Проектов с сохранёнными секретами пока нет.")
        return 0
    slugs = sorted(p.name for p in base.iterdir() if p.is_dir())
    if not slugs:
        print("Проектов с сохранёнными секретами пока нет.")
        return 0
    print("Проекты с секретами в защищённой зоне: " + ", ".join(slugs))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="save_project_secrets", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("save-env")
    e.add_argument("slug")
    e.add_argument("--from", dest="from_file")
    e.set_defaults(fn=cmd_save_env)

    s = sub.add_parser("save-server")
    s.add_argument("slug")
    s.add_argument("--host", required=True)
    s.add_argument("--user", required=True)
    s.add_argument("--port", type=int)
    s.add_argument("--as", dest="as_kind", choices=["password", "key"])
    s.add_argument("--from", dest="from_file")
    s.set_defaults(fn=cmd_save_server)

    sh = sub.add_parser("show")
    sh.add_argument("slug")
    sh.set_defaults(fn=cmd_show)

    sub.add_parser("list").set_defaults(fn=cmd_list)

    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
