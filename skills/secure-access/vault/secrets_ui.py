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

# Design language matched to the approved Vault screenshots: quiet, white, narrow, animated.
CSS = """
:root{--ink:#101828;--muted:#66748a;--soft:#8a99af;--line:#dbe5f0;--line2:#cfd9e6;
 --card:#fff;--bg:#fbfcff;--blue:#2563eb;--blue2:#4f6cff;--blueLine:#b9ccff;
 --orange:#c75a00;--orangeLine:#fed29b;--red:#ff1f2d;--shadow:0 2px 7px rgba(15,23,42,.04);
 --shadow2:0 12px 32px rgba(91,111,151,.13);--ring:0 0 0 4px rgba(83,104,255,.12)}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;color:var(--ink);background:var(--bg);min-height:100vh;-webkit-font-smoothing:antialiased;
 font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif}
a{color:inherit;text-decoration:none} a:hover{text-decoration:none}
.wrap{max-width:834px;margin:0 auto;padding:42px 0 74px;animation:pageIn .34s ease both}
.brand{display:inline-flex;align-items:center;gap:9px;color:#69788f;font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.brand .dot{width:8px;height:8px;border-radius:50%;background:#10b981}
.hero{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;margin-bottom:30px}
.hero-copy{min-width:0}.hero h1{margin:8px 0 4px}
h1{font-size:36px;line-height:1.05;font-weight:800;letter-spacing:-.02em;margin:0;color:var(--ink)}
h2{font-size:16px;line-height:1.25;font-weight:800;margin:0;color:var(--ink)}
.meta{display:flex;align-items:center;gap:10px;color:#5d6d84;font-size:14px;font-weight:600}
.num{display:inline-flex;align-items:center;min-width:30px;height:22px;justify-content:center;border:1px solid var(--line);
 border-radius:7px;background:#fff;color:#1f2a44;box-shadow:var(--shadow);font-size:13px}
.muted{color:var(--muted);font-size:14px;line-height:1.35}.muted.ital{font-style:italic;color:#8b9aaf}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow)}
.repo-list{display:grid;gap:12px;margin-top:30px}
.repo{min-height:92px;padding:21px 22px 20px 24px;display:flex;justify-content:space-between;align-items:center;gap:16px;
 color:inherit;animation:itemIn .32s ease both;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}
.repo:hover,.repo:focus-visible{border-color:var(--blueLine);box-shadow:var(--shadow2),inset 4px 0 0 var(--blue2);transform:translateY(-1px);outline:0}
.repo-info{display:grid;gap:10px;min-width:0}.repo-badges{display:flex;align-items:center;gap:12px;flex:0 0 auto}
.row{display:flex;justify-content:space-between;align-items:center;gap:12px}.stack{display:grid;gap:18px}
.badge{height:26px;display:inline-flex;align-items:center;gap:6px;border-radius:6px;border:1px solid var(--line);
 background:#f8fbff;color:#40506a;font-size:11px;font-weight:800;letter-spacing:.03em;text-transform:uppercase;padding:0 9px;white-space:nowrap}
.badge.priv{background:#fffaf3;color:var(--orange);border-color:var(--orangeLine)}
.badge.pub{background:#f5f9ff;color:#1763ff;border-color:#b8d2ff}
.badge.secret{background:#f8fbff;color:#40506a;border-color:var(--line)}
.badge svg,.btn svg,.section-title svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:1.9}
.searchbox{position:relative;margin-top:26px}
.searchbox input{height:54px;padding:0 68px 0 44px}
.searchbox:before{content:'';position:absolute;left:24px;top:50%;width:6px;height:6px;border:2px solid #8fa0b8;border-radius:50%;transform:translateY(-58%);z-index:1}
.searchbox:after{content:'';position:absolute;left:32px;top:31px;width:7px;height:2px;background:#8fa0b8;transform:rotate(45deg);border-radius:3px;z-index:1}
.kbd{position:absolute;right:16px;top:50%;transform:translateY(-50%);height:20px;padding:0 8px;border:1px solid var(--line);
 border-radius:5px;background:#fff;box-shadow:var(--shadow);color:#8090a7;font-size:11px;font-weight:800;line-height:18px}
input,textarea{width:100%;border-radius:14px;border:1px solid var(--line);background:#fff;color:var(--ink);font:inherit;outline:none;
 box-shadow:inset 0 1px 2px rgba(15,23,42,.02);transition:border-color .16s ease,box-shadow .16s ease}
input{height:46px;padding:0 14px}input::placeholder,textarea::placeholder{color:#92a0b5}
input:focus,textarea:focus{border-color:#aebeff;box-shadow:var(--ring),inset 0 1px 2px rgba(15,23,42,.03)}
textarea{min-height:256px;padding:18px 16px;resize:vertical;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;
 font-size:13px;line-height:1.55;color:#29354b}
.btn,button{height:42px;display:inline-flex;align-items:center;justify-content:center;gap:9px;border-radius:12px;border:1px solid transparent;
 padding:0 22px;font-weight:800;font-size:14px;cursor:pointer;transition:transform .16s ease,box-shadow .16s ease,background .16s ease,border-color .16s ease}
.btn:hover,button:hover{transform:translateY(-1px)}.btn:active,button:active{transform:translateY(0)}
.btn.primary,button.primary{background:#10172a;color:#fff;box-shadow:0 8px 18px rgba(16,23,42,.18)}
.btn.secondary,button.secondary{background:#fff;color:#43536d;border-color:var(--line);box-shadow:var(--shadow)}
.btn.secondary:hover,button.secondary:hover{border-color:#cdd9e8;box-shadow:0 7px 16px rgba(15,23,42,.08)}
.btn.danger,button.danger{background:#fff;color:var(--red);border-color:#ffb8bd;box-shadow:0 7px 16px rgba(255,31,45,.08)}
.btn.danger:hover,button.danger:hover{background:#fff7f7;border-color:#ff9ca4}
.btn.ghost{background:#fff;color:#4b5c76;border-color:var(--line);box-shadow:var(--shadow);height:42px}
button{background:#10172a;color:#fff}
.section-title{display:flex;align-items:center;gap:10px;margin:30px 0 22px;color:var(--ink)}
.section-title h2{font-size:19px}.panel{padding:26px 24px;min-height:72px}.actions-card{padding:12px;margin-top:26px}
.editor-card{padding:26px 24px 24px;margin-top:20px}.editor-hint{margin:0 0 16px;color:#66748a;font-size:14px}
.editor-actions{justify-content:flex-start;margin-top:24px}.empty{color:#63748e;font-size:16px}
table{width:100%;border-collapse:collapse}td{padding:11px 4px;border-bottom:1px solid var(--line);font-size:14px}
code{background:#f4f7fb;border:1px solid #e4ebf4;padding:4px 8px;border-radius:6px;font-size:12px;color:#42526c;font-weight:700}
.note{font-size:13px;color:var(--muted);margin-top:10px}.login{max-width:430px;margin:7vh auto 0}
.manual{margin-top:20px;padding:20px 22px}.manual h2{margin-bottom:12px}
.toast{position:fixed;right:28px;top:24px;z-index:20;background:#10172a;color:#fff;border-radius:14px;padding:13px 16px;
 box-shadow:0 18px 48px rgba(16,23,42,.22);font-size:14px;font-weight:700;animation:toastIn .28s ease both}
.modal{position:fixed;inset:0;background:rgba(16,24,40,.28);display:none;align-items:center;justify-content:center;padding:20px;z-index:30}
.modal.open{display:flex;animation:fadeIn .16s ease both}.modal-box{width:min(420px,100%);background:#fff;border:1px solid var(--line);
 border-radius:18px;padding:24px;box-shadow:0 24px 80px rgba(15,23,42,.24);animation:modalIn .2s ease both}
.modal-box p{margin:10px 0 22px;color:#66748a;line-height:1.5}.modal-actions{display:flex;justify-content:flex-end;gap:10px}
@keyframes pageIn{from{opacity:0}to{opacity:1}}
@keyframes itemIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes toastIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}@keyframes modalIn{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}
@media (max-width:980px){.wrap{width:calc(100vw - 32px);margin:0 auto;padding-top:34px}.hero{align-items:flex-start}.repo{padding:19px 18px}}
@media (max-width:700px){h1{font-size:32px}.hero{display:grid}.repo{align-items:flex-start}.repo-badges{flex-wrap:wrap;justify-content:flex-end}
 .actions-card .row,.editor-actions,.manual .row{display:grid;grid-template-columns:1fr}.btn,button{width:100%}}
"""


BRAND = "<div class=brand><span class=dot></span>andidigital vault</div>"


def page(title: str, body: str) -> bytes:
    return (f"<!doctype html><html lang=ru><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<meta name=theme-color content='#c0fc41'>"
            f"<link rel=icon href='/favicon.svg'><link rel=icon type=image/png href='/favicon-32x32.png'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body><div class=wrap>{body}</div></body></html>").encode("utf-8")


def esc(s: str) -> str:
    return html.escape(s or "")


ICON_LOCK = "<svg viewBox='0 0 24 24'><rect x='5' y='10' width='14' height='10' rx='2'></rect><path d='M8 10V7a4 4 0 0 1 8 0v3'></path></svg>"
ICON_GLOBE = "<svg viewBox='0 0 24 24'><circle cx='12' cy='12' r='9'></circle><path d='M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18'></path></svg>"
ICON_SHIELD = "<svg viewBox='0 0 24 24'><path d='M12 3 19 6v5c0 4.5-2.8 8-7 10-4.2-2-7-5.5-7-10V6l7-3Z'></path><path d='m9.5 12 1.7 1.7 3.7-4'></path></svg>"
ICON_LOGOUT = "<svg viewBox='0 0 24 24'><path d='M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4'></path><path d='M10 17l5-5-5-5M15 12H3'></path></svg>"
ICON_BACK = "<svg viewBox='0 0 24 24'><path d='m15 18-6-6 6-6'></path><path d='M9 12h12'></path></svg>"
ICON_KEY = "<svg viewBox='0 0 24 24'><circle cx='7.5' cy='15.5' r='4.5'></circle><path d='m11 12 8-8 3 3-2 2-2-2-2 2 2 2-2 2'></path></svg>"
ICON_EDIT = "<svg viewBox='0 0 24 24'><path d='M12 20h9'></path><path d='M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z'></path></svg>"
ICON_TRASH = "<svg viewBox='0 0 24 24'><path d='M3 6h18'></path><path d='M8 6V4h8v2'></path><path d='M19 6l-1 14H6L5 6'></path><path d='M10 11v5M14 11v5'></path></svg>"


def visibility_badge(private: bool | None) -> str:
    if private is None:
        return ""
    if private:
        return f"<span class='badge priv'>{ICON_LOCK} PRIVATE</span>"
    return f"<span class='badge pub'>{ICON_GLOBE} PUBLIC</span>"


def secret_badge(count: int) -> str:
    return f"<span class='badge secret'>{ICON_SHIELD} {count} секретов</span>"


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
            return self.view_dashboard(q)
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

    def view_dashboard(self, q: dict):
        repos = github_repos(self.cfg)
        secrets_map = list_secret_slugs(self.cfg)
        pre = self.prefix()
        rows = []
        seen = set()
        for r in repos:
            slug = slugify_repo(r["name"])
            seen.add(slug)
            cnt = secrets_map.get(slug)
            desc = esc(r["description"]) if r["description"] else "Нет описания"
            desc_class = "muted" if r["description"] else "muted ital"
            rows.append(
                f"<a class='card repo' data-name='{esc(r['name'].lower())}' "
                f"href='{pre}/project/{esc(slug)}'><div class=repo-info>"
                f"<h2>{esc(r['name'])}</h2>"
                f"<div class='{desc_class}'>{desc}</div></div>"
                f"<div class=repo-badges>{visibility_badge(r['private'])}{secret_badge(cnt or 0)}</div></a>")
        # secret stores that don't match a repo (manual projects)
        extra = [s for s in secrets_map if s not in seen]
        extra_html = ""
        if extra:
            items = "".join(f"<div class=row><a href='{pre}/project/{esc(s)}'>{esc(s)}</a>"
                            f"{secret_badge(secrets_map[s])}</div>" for s in extra)
            extra_html = f"<div class='card manual'><h2>Прочие проекты</h2>{items}</div>"
        nogh = "" if repos else "<div class='card panel empty'>Не удалось получить список репозиториев GitHub.</div>"
        toast = "<div class=toast>Секреты проекта удалены</div>" if q.get("deleted") else ""
        top = (f"{toast}<header class=hero><div class=hero-copy>{BRAND}<h1>Секреты проектов</h1>"
               f"<div class=meta><span class=num>{len(repos)}</span><span>репозиториев</span><span>·</span>"
               f"<span class=num>{len(secrets_map)}</span><span>с секретами</span></div></div>"
               f"<form method=post action='{pre}/logout' style='margin:0'>{self._csrf()}"
               f"<button class='btn secondary'>{ICON_LOGOUT} Выйти</button></form></header>")
        search = ("<div class=searchbox><input id=q type=text placeholder='Поиск по репозиториям...' autocomplete=off>"
                  "<span class=kbd>⌘ K</span></div>"
                  if repos else "")
        manual = (f"<div class='card manual'><h2>Добавить проект вручную</h2>"
                  f"<form method=post action='{pre}/link-repo'>{self._csrf()}"
                  f"<div class=row style='margin-top:10px'><input type=text name=slug placeholder='имя-проекта (slug)' required>"
                  f"<button class='btn secondary' style='white-space:nowrap'>Создать</button></div></form></div>")
        script = ("<script>const q=document.getElementById('q');q&&q.addEventListener('input',()=>{"
                  "const v=q.value.toLowerCase();document.querySelectorAll('.repo').forEach(e=>"
                  "{e.style.display=e.dataset.name.includes(v)?'':'none'})});"
                  "document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){"
                  "e.preventDefault();q&&q.focus()}});"
                  "setTimeout(()=>document.querySelector('.toast')?.remove(),3200);</script>")
        self.send_html(page("Vault", top + nogh + search + "<div class=repo-list>" + "".join(rows) + "</div>" + extra_html + manual + script))

    def view_project(self, slug: str, q: dict):
        if not SLUG_RE.match(slug):
            return self.not_found()
        pre = self.prefix()
        content = read_env(self.cfg, slug)
        names = var_names(content)
        editing = q.get("edit") == "1"
        repos = github_repos(self.cfg)
        repo = next((r for r in repos if slugify_repo(r["name"]) == slug), None)
        privacy = visibility_badge(repo["private"]) if repo else ""
        toast = "<div class=toast>Секреты сохранены</div>" if q.get("saved") else ""
        names_html = ("<table>" + "".join(f"<tr><td><code>{esc(n)}</code></td></tr>" for n in names) + "</table>"
                      if names else "<div class=empty>Пока ни одной переменной.</div>")
        if editing:
            editor = (
                f"<form method=post action='{pre}/project-save'>{self._csrf()}"
                f"<input type=hidden name=slug value='{esc(slug)}'>"
                f"<p class=editor-hint>Формат: <code>KEY=VALUE</code>, по одной на строку. Значения видны только тебе здесь.</p>"
                f"<textarea name=content spellcheck=false placeholder='API_KEY=your_secret_key&#10;PORT=3000'>{esc(content)}</textarea>"
                f"<div class='row editor-actions'><a class='btn secondary' href='{pre}/project/{esc(slug)}'>Отмена</a>"
                f"<button class=primary>Сохранить</button></div></form>")
        else:
            editor = (f"<div class=row><button type=button class='btn danger' data-open-delete>{ICON_TRASH} Удалить секреты проекта</button>"
                      f"<a class='btn primary' href='{pre}/project/{esc(slug)}?edit=1'>{ICON_EDIT} Редактировать значения</a></div>"
                      f"<div class=modal id=deleteModal aria-hidden=true><div class=modal-box role=dialog aria-modal=true>"
                      f"<h2>Удалить секреты проекта?</h2><p>Будет удален файл с переменными для проекта {esc(slug)}. Это действие нельзя отменить.</p>"
                      f"<div class=modal-actions><button type=button class='btn secondary' data-close-delete>Отмена</button>"
                      f"<form method=post action='{pre}/project-delete' style='margin:0'>"
                      f"{self._csrf()}<input type=hidden name=slug value='{esc(slug)}'>"
                      f"<button class='btn danger'>{ICON_TRASH} Удалить</button></form></div></div></div>")
        body = (f"{toast}<header class=hero><div class=hero-copy>{BRAND}<h1>{esc(slug)}</h1>{privacy}</div>"
                f"<a class='btn ghost' href='{pre}/'>{ICON_BACK} Все проекты</a></header>"
                f"<div class=section-title>{ICON_KEY}<h2>Переменные ({len(names)})</h2></div>"
                f"<div class='card panel'>{names_html}</div>"
                f"<div class='card {'editor-card' if editing else 'actions-card'}'>{editor}</div>"
                f"<script>const m=document.getElementById('deleteModal');document.querySelector('[data-open-delete]')?.addEventListener('click',()=>m.classList.add('open'));"
                f"document.querySelector('[data-close-delete]')?.addEventListener('click',()=>m.classList.remove('open'));"
                f"m?.addEventListener('click',e=>{{if(e.target===m)m.classList.remove('open')}});"
                f"document.addEventListener('keydown',e=>{{if(e.key==='Escape')m?.classList.remove('open')}});"
                f"setTimeout(()=>document.querySelector('.toast')?.remove(),3200);</script>")
        self.send_html(page(f"Vault — {slug}", body))

    # ---- actions
    def act_save(self, p):
        slug = p.get("slug", "")
        if not SLUG_RE.match(slug):
            return self.not_found()
        write_env(self.cfg, slug, p.get("content", ""))
        self.redirect(self.prefix() + "/project/" + slug + "?saved=1")

    def act_delete(self, p):
        slug = p.get("slug", "")
        if SLUG_RE.match(slug):
            delete_project(self.cfg, slug)
        self.redirect(self.prefix() + "/?deleted=1")

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
