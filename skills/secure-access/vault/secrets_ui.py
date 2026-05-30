#!/usr/bin/env python3
"""Hermes Vault — a small, dependency-free web UI to manage per-project secrets.

Stdlib only (no pip): http.server + hashlib.scrypt + hmac. Runs as the unprivileged `hermesvault`
user, bound to 127.0.0.1, exposed by nginx over TLS at  https://<host><base_path>/<url_token>/ .

Security model (see engineering/secrets-access.md + skills/secure-access/vault/README.md):
  * Two factors: (1) an unguessable URL token in the path, (2) a password stored only as a
    scrypt hash. After login, an HMAC-signed, httponly+secure+samesite cookie session.
  * CSRF token on every mutating form. Per-IP login rate-limit/lockout.
  * Values live only under vault_dir (/opt/hermes/secure/projects/<slug>/.env, 660, group hermessec) —
    the same store the agent reads. Never logged. Slugs are strictly validated (no path traversal).
  * GitHub repo list via the REST API with a token readable only by hermesvault.

Universal/turnkey: everything instance-specific (name, url_token, password hash, secrets) is in
config.json / the data dir — resale = a fresh config, no code change.

CLI:
  secrets_ui.py init [--base-path P] [--port N] [--instance NAME]   # generate config.json if missing
  secrets_ui.py serve                                               # run the server
  secrets_ui.py set-url-token                                       # rotate the URL token, print nothing
"""
from __future__ import annotations

import html
import hmac
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
from hashlib import scrypt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("VAULT_CONFIG", "/opt/hermes/vault/config.json"))
GH_TOKEN_PATH = Path(os.environ.get("VAULT_GH_TOKEN", "/opt/hermes/vault/gh_token"))
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,60}[a-z0-9]$")
VAR_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
SCRYPT = dict(n=16384, r=8, p=1, dklen=32, maxmem=64 * 1024 * 1024)
SESSION_TTL = 3600  # seconds
LOCK_FAILS = 6
LOCK_SECS = 300

# --------------------------------------------------------------------------- config

def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG_PATH)


def hash_password(pw: str) -> dict:
    salt = secrets.token_bytes(16)
    dk = scrypt(pw.encode("utf-8"), salt=salt, **SCRYPT)
    return {"algo": "scrypt", "salt": salt.hex(), "hash": dk.hex()}


def verify_password(pw: str, rec: dict) -> bool:
    if not rec:
        return False
    dk = scrypt(pw.encode("utf-8"), salt=bytes.fromhex(rec["salt"]), **SCRYPT)
    return hmac.compare_digest(dk.hex(), rec["hash"])


# --------------------------------------------------------------------------- sessions

def _sign(secret: str, msg: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), msg, "sha256").hexdigest()


def make_session(secret: str) -> tuple[str, str]:
    csrf = secrets.token_hex(16)
    payload = json.dumps({"exp": int(time.time()) + SESSION_TTL, "csrf": csrf}).encode("utf-8")
    body = urllib.parse.quote(payload)
    token = f"{body}.{_sign(secret, payload)}"
    return token, csrf


def read_session(secret: str, cookie_val: str | None) -> dict | None:
    if not cookie_val or "." not in cookie_val:
        return None
    body, _, sig = cookie_val.rpartition(".")
    try:
        payload = urllib.parse.unquote(body).encode("utf-8")
    except Exception:
        return None
    if not hmac.compare_digest(_sign(secret, payload), sig):
        return None
    try:
        data = json.loads(payload)
    except Exception:
        return None
    if int(data.get("exp", 0)) < int(time.time()):
        return None
    return data


# --------------------------------------------------------------------------- vault store

def vault_dir(cfg: dict) -> Path:
    return Path(cfg.get("vault_dir", "/opt/hermes/secure/projects"))


def proj_path(cfg: dict, slug: str) -> Path:
    if not SLUG_RE.match(slug):
        raise ValueError("bad slug")
    return vault_dir(cfg) / slug


def read_env(cfg: dict, slug: str) -> str:
    f = proj_path(cfg, slug) / ".env"
    return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""


def var_names(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = VAR_RE.match(line)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def write_env(cfg: dict, slug: str, content: str) -> None:
    d = proj_path(cfg, slug)
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o2770)
    except OSError:
        pass
    f = d / ".env"
    tmp = d / ".env.tmp"
    tmp.write_text(content.replace("\r\n", "\n"), encoding="utf-8")
    os.chmod(tmp, 0o660)
    os.replace(tmp, f)


def delete_project(cfg: dict, slug: str) -> None:
    d = proj_path(cfg, slug)
    if d.exists():
        for p in d.iterdir():
            p.unlink()
        d.rmdir()


def list_secret_slugs(cfg: dict) -> dict[str, int]:
    base = vault_dir(cfg)
    out: dict[str, int] = {}
    if base.exists():
        for d in base.iterdir():
            if d.is_dir() and (d / ".env").exists():
                out[d.name] = len(var_names((d / ".env").read_text(encoding="utf-8", errors="replace")))
    return out


def slugify_repo(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-").lower()
    return s[:62] or "project"


# --------------------------------------------------------------------------- github

_REPO_CACHE: dict = {"t": 0.0, "data": None}
_REPO_TTL = 120  # seconds — keep the dashboard snappy without hammering the GitHub API


def github_repos(cfg: dict) -> list[dict]:
    if _REPO_CACHE["data"] is not None and (time.time() - _REPO_CACHE["t"]) < _REPO_TTL:
        return _REPO_CACHE["data"]
    if not GH_TOKEN_PATH.exists():
        return []
    token = GH_TOKEN_PATH.read_text(encoding="utf-8").strip()
    repos: list[dict] = []
    for page in range(1, 6):
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&sort=updated&affiliation=owner"
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "hermes-vault",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                batch = json.loads(r.read().decode("utf-8"))
        except Exception:
            break
        if not batch:
            break
        for it in batch:
            repos.append({
                "full_name": it.get("full_name", ""),
                "name": it.get("name", ""),
                "private": bool(it.get("private")),
                "description": it.get("description") or "",
                "html_url": it.get("html_url", ""),
            })
        if len(batch) < 100:
            break
    _REPO_CACHE["data"] = repos
    _REPO_CACHE["t"] = time.time()
    return repos


# --------------------------------------------------------------------------- HTML

# Design language matched to the andidigital site: light theme, slate ink, bright-lime accent.
CSS = """
:root{--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--line2:#cbd5e1;--card:#fff;
 --lime:#c0fc41;--lime2:#a3e635;--olive:#6f9e2a;--shadow:0 8px 24px rgba(15,23,42,.06);
 --shadow2:0 16px 34px rgba(148,163,184,.22)}
*{box-sizing:border-box}
body{margin:0;color:var(--ink);background:linear-gradient(180deg,#f8fafc 0%,#f3f8ff 100%);
 min-height:100vh;-webkit-font-smoothing:antialiased;
 font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif}
a{color:var(--olive);text-decoration:none;font-weight:600} a:hover{text-decoration:underline}
.wrap{max-width:1000px;margin:0 auto;padding:26px 20px 64px}
.brand{display:inline-flex;align-items:center;gap:10px;font-weight:800;font-size:18px;letter-spacing:-.02em;color:var(--ink)}
.brand .dot{width:12px;height:12px;border-radius:50%;background:var(--lime);box-shadow:0 0 0 4px rgba(192,252,65,.28)}
.topbar{display:flex;justify-content:space-between;align-items:center;margin:4px 0 20px;gap:12px;flex-wrap:wrap}
h1{font-size:26px;font-weight:800;letter-spacing:-.025em;margin:0 0 2px}
h2{font-size:15px;font-weight:700;margin:0}
.muted{color:var(--muted);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px 20px;margin:14px 0;box-shadow:var(--shadow)}
.repo{display:flex;justify-content:space-between;align-items:center;gap:14px;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease}
.repo:hover{transform:translateY(-2px);box-shadow:var(--shadow2);border-color:#dbe7c4}
.row{display:flex;justify-content:space-between;align-items:center;gap:12px}
.badge{font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;background:#f1f5f9;color:#64748b;border:1px solid var(--line)}
.badge.priv{background:#fff7ed;color:#b45309;border-color:#fed7aa}
.badge.has{background:#f2ffd6;color:#4d7c0f;border-color:#d6f29a}
input,textarea{width:100%;padding:11px 12px;border-radius:12px;border:1px solid var(--line2);background:#fff;color:var(--ink);font:inherit;outline:none}
input:focus,textarea:focus{border-color:var(--lime2);box-shadow:0 0 0 4px rgba(163,230,53,.18)}
textarea{min-height:260px;font-family:ui-monospace,Consolas,monospace;font-size:13px;line-height:1.55}
button{cursor:pointer;border:0;border-radius:12px;padding:11px 18px;font-weight:700;font-size:14px;color:#1a2e05;
 background:var(--lime);box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 6px 16px rgba(146,200,40,.35);
 transition:transform .1s ease,box-shadow .1s ease,background .1s ease}
button:hover{background:var(--lime2);transform:translateY(-1px)} button:active{transform:translateY(0)}
button.sec{background:#fff;color:var(--ink);border:1px solid var(--line2);box-shadow:var(--shadow)}
button.sec:hover{background:#f8fafc}
button.danger{background:#fee2e2;color:#b91c1c;box-shadow:none} button.danger:hover{background:#fecaca}
table{width:100%;border-collapse:collapse} td{padding:8px 4px;border-bottom:1px solid var(--line);font-size:14px}
code{background:#f1f5f9;border:1px solid var(--line);padding:2px 7px;border-radius:7px;font-size:12.5px;color:#334155}
.note{font-size:12px;color:var(--muted);margin-top:8px}
.login{max-width:430px;margin:7vh auto 0}
.search{margin-bottom:4px}
.empty{color:var(--muted);font-size:14px}
"""


BRAND = "<a class=brand href='#'><span class=dot></span>andidigital · Vault</a>"


def page(title: str, body: str) -> bytes:
    return (f"<!doctype html><html lang=ru><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<meta name=theme-color content='#c0fc41'>"
            f"<link rel=icon href='/favicon.svg'><link rel=icon type=image/png href='/favicon-32x32.png'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body><div class=wrap>{body}</div></body></html>").encode("utf-8")


def esc(s: str) -> str:
    return html.escape(s or "")


# --------------------------------------------------------------------------- server

class Handler(BaseHTTPRequestHandler):
    server_version = "hv"

    # silence default logging (never log secrets/tokens/paths)
    def log_message(self, *a):
        pass

    # ---- helpers
    @property
    def cfg(self) -> dict:
        return self.server.cfg  # type: ignore[attr-defined]

    def prefix(self) -> str:
        return f"{self.cfg['base_path']}/{self.cfg['url_token']}"

    def client_ip(self) -> str:
        return self.headers.get("X-Real-IP") or self.client_address[0]

    def cookies(self) -> dict:
        out = {}
        for part in (self.headers.get("Cookie") or "").split(";"):
            if "=" in part:
                k, _, v = part.strip().partition("=")
                out[k] = v
        return out

    def session(self) -> dict | None:
        return read_session(self.cfg["session_secret"], self.cookies().get("vault_session"))

    def send_html(self, body: bytes, code=200, headers=None):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or []):
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, to: str, headers=None):
        self.send_response(303)
        self.send_header("Location", to)
        for k, v in (headers or []):
            self.send_header(k, v)
        self.end_headers()

    def not_found(self):
        self.send_html(page("404", "<div class=card>Не найдено.</div>"), code=404)

    def set_session_cookie(self) -> tuple[str, list]:
        tok, csrf = make_session(self.cfg["session_secret"])
        cookie = (f"vault_session={tok}; Path={self.cfg['base_path']}; HttpOnly; Secure; "
                  f"SameSite=Strict; Max-Age={SESSION_TTL}")
        return csrf, [("Set-Cookie", cookie)]

    def body_params(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n).decode("utf-8") if n else ""
        return {k: v[0] for k, v in urllib.parse.parse_qs(raw, keep_blank_values=True).items()}

    # ---- routing
    def route(self) -> tuple[str, dict]:
        """Return (subpath, query) after validating base_path + url_token, else raise KeyError."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        base = self.cfg["base_path"]
        if not (path == base or path.startswith(base + "/")):
            raise KeyError("base")
        rest = path[len(base):].lstrip("/")            # "<token>/sub..."
        token, _, sub = rest.partition("/")
        if not hmac.compare_digest(token, self.cfg["url_token"]):
            raise KeyError("token")
        return "/" + sub, {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}

    def do_GET(self):
        try:
            sub, q = self.route()
        except KeyError:
            return self.not_found()
        pw_set = bool(self.cfg.get("password"))
        if not pw_set:
            return self.view_setup()
        if not self.session():
            return self.view_login()
        if sub in ("/", ""):
            return self.view_dashboard()
        if sub.startswith("/project/"):
            return self.view_project(sub[len("/project/"):], q)
        return self.not_found()

    def do_POST(self):
        try:
            sub, _q = self.route()
        except KeyError:
            return self.not_found()
        params = self.body_params()
        # setup (first run): set the password
        if not self.cfg.get("password"):
            if sub == "/setup":
                return self.act_setup(params)
            return self.view_setup()
        if sub == "/login":
            return self.act_login(params)
        sess = self.session()
        if not sess:
            return self.view_login()
        # all further POSTs require a valid CSRF token
        if not hmac.compare_digest(params.get("csrf", ""), sess.get("csrf", "")):
            return self.send_html(page("Ошибка", "<div class=card>Сессия устарела, обнови страницу.</div>"), code=400)
        if sub == "/logout":
            return self.redirect(self.prefix() + "/", headers=[(
                "Set-Cookie", f"vault_session=; Path={self.cfg['base_path']}; Max-Age=0")])
        if sub == "/project-save":
            return self.act_save(params)
        if sub == "/project-delete":
            return self.act_delete(params)
        if sub == "/link-repo":
            return self.act_link(params)
        return self.not_found()

    # ---- views
    def view_setup(self):
        body = ("<div class=login>" + BRAND +
                "<div class=card style='margin-top:14px'><h1 style='font-size:21px'>Первый запуск</h1>"
                "<p class=muted>Задай пароль для входа в хранилище. Он сохранится только как scrypt-хэш.</p>"
                "<form method=post action='" + self.prefix() + "/setup'>"
                "<p><input type=password name=pw1 placeholder='Пароль (мин. 10 символов)' minlength=10 required></p>"
                "<p><input type=password name=pw2 placeholder='Повтори пароль' minlength=10 required></p>"
                "<button style='width:100%'>Установить пароль</button>"
                "<div class=note>После этого вход — по этой секретной ссылке + паролю.</div>"
                "</form></div></div>")
        self.send_html(page("Vault — setup", body))

    def act_setup(self, p):
        pw1, pw2 = p.get("pw1", ""), p.get("pw2", "")
        if len(pw1) < 10 or pw1 != pw2:
            return self.send_html(page("setup", "<div class=card>Пароли не совпадают или короче 10 символов. <a href='" + self.prefix() + "/'>Назад</a></div>"), code=400)
        cfg = load_config()
        cfg["password"] = hash_password(pw1)
        save_config(cfg)
        self.server.cfg = cfg  # type: ignore[attr-defined]
        self.redirect(self.prefix() + "/")

    def view_login(self, err: str = ""):
        ip = self.client_ip()
        if self._locked(ip):
            body = "<h1>Вход</h1><div class=card>Слишком много попыток. Подожди несколько минут.</div>"
            return self.send_html(page("Вход", body), code=429)
        e = f"<div class=note style='color:#dc2626'>{esc(err)}</div>" if err else ""
        body = ("<div class=login>" + BRAND +
                "<div class=card style='margin-top:14px'><h1 style='font-size:21px'>Вход в хранилище</h1>"
                "<p class=muted>Введи пароль для доступа к секретам проектов.</p>"
                "<form method=post action='" + self.prefix() + "/login'>"
                "<p><input type=password name=pw placeholder='Пароль' required autofocus></p>"
                f"<button style='width:100%'>Войти</button>{e}</form></div></div>")
        self.send_html(page("Вход", body))

    def act_login(self, p):
        ip = self.client_ip()
        if self._locked(ip):
            return self.view_login("Слишком много попыток.")
        if verify_password(p.get("pw", ""), self.cfg.get("password")):
            self._fails.pop(ip, None)
            csrf, hdrs = self.set_session_cookie()
            return self.redirect(self.prefix() + "/", headers=hdrs)
        self._record_fail(ip)
        self.view_login("Неверный пароль.")

    def view_dashboard(self):
        repos = github_repos(self.cfg)
        secrets_map = list_secret_slugs(self.cfg)
        pre = self.prefix()
        rows = []
        seen = set()
        for r in repos:
            slug = slugify_repo(r["name"])
            seen.add(slug)
            cnt = secrets_map.get(slug)
            badge = (f"<span class='badge has'>секретов: {cnt}</span>" if cnt
                     else "<span class=badge>нет секретов</span>")
            vis = "<span class='badge priv'>private</span>" if r["private"] else "<span class=badge>public</span>"
            rows.append(
                f"<a class='card repo' data-name='{esc(r['name'].lower())}' "
                f"href='{pre}/project/{esc(slug)}' style='color:inherit'><div>"
                f"<h2>{esc(r['name'])}</h2>"
                f"<div class=muted>{esc(r['description']) or '—'}</div></div>"
                f"<div class=row style='gap:8px'>{vis} {badge}</div></a>")
        # secret stores that don't match a repo (manual projects)
        extra = [s for s in secrets_map if s not in seen]
        extra_html = ""
        if extra:
            items = "".join(f"<div class=row><a href='{pre}/project/{esc(s)}'>{esc(s)}</a>"
                            f"<span class='badge has'>секретов: {secrets_map[s]}</span></div>" for s in extra)
            extra_html = f"<div class=card><h2>Прочие проекты (без репозитория)</h2>{items}</div>"
        nogh = "" if repos else "<div class=card class=empty>Не удалось получить список репозиториев GitHub (проверь токен).</div>"
        top = (f"{BRAND}"
               f"<div class=topbar><div><h1>Секреты проектов</h1>"
               f"<div class=muted>{len(repos)} репозиториев · {len(secrets_map)} с секретами</div></div>"
               f"<form method=post action='{pre}/logout' style='margin:0'>{self._csrf()}"
               f"<button class=sec>Выйти</button></form></div>")
        search = ("<input class=search id=q type=text placeholder='Поиск по репозиториям…' autocomplete=off>"
                  if repos else "")
        manual = (f"<div class=card><h2>Добавить проект вручную</h2>"
                  f"<form method=post action='{pre}/link-repo'>{self._csrf()}"
                  f"<div class=row style='margin-top:10px'><input type=text name=slug placeholder='имя-проекта (slug)' required>"
                  f"<button class=sec style='white-space:nowrap'>Создать</button></div></form></div>")
        script = ("<script>const q=document.getElementById('q');q&&q.addEventListener('input',()=>{"
                  "const v=q.value.toLowerCase();document.querySelectorAll('.repo').forEach(e=>"
                  "{e.style.display=e.dataset.name.includes(v)?'':'none'})});</script>")
        self.send_html(page("Vault", top + nogh + search + "".join(rows) + extra_html + manual + script))

    def view_project(self, slug: str, q: dict):
        if not SLUG_RE.match(slug):
            return self.not_found()
        pre = self.prefix()
        content = read_env(self.cfg, slug)
        names = var_names(content)
        editing = q.get("edit") == "1"
        names_html = ("<table>" + "".join(f"<tr><td><code>{esc(n)}</code></td></tr>" for n in names) + "</table>"
                      if names else "<div class=muted>Пока ни одной переменной.</div>")
        if editing:
            editor = (
                f"<form method=post action='{pre}/project-save'>{self._csrf()}"
                f"<input type=hidden name=slug value='{esc(slug)}'>"
                f"<p class=muted>Формат: <code>KEY=VALUE</code>, по одной на строку. Значения видны только тебе здесь.</p>"
                f"<textarea name=content spellcheck=false>{esc(content)}</textarea>"
                f"<div class=row style='margin-top:10px'><button>Сохранить</button>"
                f"<a href='{pre}/project/{esc(slug)}'><button type=button class=sec>Отмена</button></a></div></form>")
        else:
            editor = (f"<div class=row><a href='{pre}/project/{esc(slug)}?edit=1'><button>✏️ Редактировать значения</button></a>"
                      f"<form method=post action='{pre}/project-delete' onsubmit=\"return confirm('Удалить все секреты проекта?')\" style='margin:0'>"
                      f"{self._csrf()}<input type=hidden name=slug value='{esc(slug)}'>"
                      f"<button class=danger>Удалить</button></form></div>")
        body = (f"{BRAND}"
                f"<div class=topbar><h1>{esc(slug)}</h1><a href='{pre}/'>← все проекты</a></div>"
                f"<div class=card><h2>Переменные ({len(names)})</h2><div style='margin-top:8px'>{names_html}</div></div>"
                f"<div class=card>{editor}</div>")
        self.send_html(page(f"Vault — {slug}", body))

    # ---- actions
    def act_save(self, p):
        slug = p.get("slug", "")
        if not SLUG_RE.match(slug):
            return self.not_found()
        write_env(self.cfg, slug, p.get("content", ""))
        self.redirect(self.prefix() + "/project/" + slug)

    def act_delete(self, p):
        slug = p.get("slug", "")
        if SLUG_RE.match(slug):
            delete_project(self.cfg, slug)
        self.redirect(self.prefix() + "/")

    def act_link(self, p):
        slug = slugify_repo(p.get("slug", ""))
        if SLUG_RE.match(slug):
            write_env(self.cfg, slug, read_env(self.cfg, slug))  # ensure dir exists
        self.redirect(self.prefix() + "/project/" + slug)

    # ---- csrf + rate limit (per-process, in-memory)
    _fails: dict = {}

    def _csrf(self) -> str:
        s = self.session()
        return f"<input type=hidden name=csrf value='{esc(s['csrf']) if s else ''}'>"

    def _locked(self, ip: str) -> bool:
        rec = self._fails.get(ip)
        return bool(rec and rec[0] >= LOCK_FAILS and time.time() < rec[1])

    def _record_fail(self, ip: str):
        n = (self._fails.get(ip, [0, 0])[0]) + 1
        self._fails[ip] = [n, time.time() + LOCK_SECS]


# --------------------------------------------------------------------------- CLI

def cmd_init(args) -> int:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cfg = load_config() if CONFIG_PATH.exists() else {}
    cfg.setdefault("instance", args.instance or "hermes")
    cfg.setdefault("base_path", args.base_path or "/vault")
    cfg.setdefault("bind_host", "127.0.0.1")
    cfg.setdefault("bind_port", args.port or 8787)
    cfg.setdefault("vault_dir", "/opt/hermes/secure/projects")
    cfg.setdefault("url_token", secrets.token_urlsafe(24))
    cfg.setdefault("session_secret", secrets.token_hex(32))
    cfg.setdefault("password", None)
    save_config(cfg)
    # print the public path WITHOUT exposing it in logs elsewhere — caller redirects to a file
    print(f"{cfg['base_path']}/{cfg['url_token']}/")
    return 0


def cmd_set_url_token(_args) -> int:
    cfg = load_config()
    cfg["url_token"] = secrets.token_urlsafe(24)
    save_config(cfg)
    print(f"{cfg['base_path']}/{cfg['url_token']}/")
    return 0


def cmd_serve(_args) -> int:
    cfg = load_config()
    httpd = ThreadingHTTPServer((cfg["bind_host"], int(cfg["bind_port"])), Handler)
    httpd.cfg = cfg  # type: ignore[attr-defined]
    httpd.serve_forever()
    return 0


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(prog="secrets_ui")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--base-path"); i.add_argument("--port", type=int); i.add_argument("--instance")
    i.set_defaults(fn=cmd_init)
    sub.add_parser("serve").set_defaults(fn=cmd_serve)
    sub.add_parser("set-url-token").set_defaults(fn=cmd_set_url_token)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
