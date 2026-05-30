#!/usr/bin/env python3
"""fetch_url — read the content behind a link for Hermes.

One deterministic, no-LLM-cost reader the agent can call from a terminal tool when the owner
pastes a link. Handles two cases:

  * Google Docs / Sheets / Slides / Drive — converts the share URL to its export URL
    (Docs→txt, Sheets→csv, Slides→txt) and fetches the clean content. Works for documents shared
    "anyone with the link"; private docs are detected and reported (they need access / Google auth).
  * Any other web page — fetches the HTML and reduces it to readable text (scripts/styles removed,
    tags stripped, entities decoded), capped to a sane size.

All owner-facing output is Russian and free of technical noise (see profile/communication.md).
Stdlib only. Usage:
    python3 fetch_url.py <url> [--gid N] [--max N] [--format txt|csv|html]
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.error
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

UA = "Mozilla/5.0 (compatible; HermesReader/1.0)"
DEFAULT_MAX = 20000
G_FILE = re.compile(r"/(document|spreadsheets|presentation)/d/([A-Za-z0-9_-]+)")
G_DRIVE = re.compile(r"/file/d/([A-Za-z0-9_-]+)")
G_IDPARAM = re.compile(r"[?&]id=([A-Za-z0-9_-]+)")
GID = re.compile(r"[#&?]gid=(\d+)")


def fail(msg: str) -> "NoReturn":
    print(msg)
    raise SystemExit(1)


def fetch(url: str, timeout: int = 30):
    """Return (final_url, status, content_type, body_text). Follows redirects."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ru,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        ctype = r.headers.get("Content-Type", "")
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", ctype)
        if m:
            charset = m.group(1)
        return r.geturl(), r.status, ctype, raw.decode(charset, "replace")


# ---------------------------------------------------------------- google links

def google_export_url(url: str, gid: str | None, fmt: str | None) -> str | None:
    m = G_FILE.search(url)
    if m:
        kind, doc_id = m.group(1), m.group(2)
        if kind == "document":
            return f"https://docs.google.com/document/d/{doc_id}/export?format={fmt or 'txt'}"
        if kind == "presentation":
            return f"https://docs.google.com/presentation/d/{doc_id}/export/{fmt or 'txt'}"
        if kind == "spreadsheets":
            g = gid or (GID.search(url).group(1) if GID.search(url) else None)
            base = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format={fmt or 'csv'}"
            return base + (f"&gid={g}" if g else "")
    m = G_DRIVE.search(url) or G_IDPARAM.search(url)
    if m and ("drive.google.com" in url):
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    return None


def looks_private(final_url: str, body: str) -> bool:
    if "accounts.google.com" in final_url or "ServiceLogin" in final_url:
        return True
    head = body[:2000].lower()
    return ("sign in" in head and "google" in head) or "you need access" in head or "request access" in head


# ------------------------------------------------------------------- html→text

def html_to_text(htmltext: str) -> str:
    s = re.sub(r"(?is)<(script|style|head|noscript|svg)[^>]*>.*?</\1>", " ", htmltext)
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?i)<(br|/p|/div|/li|/tr|/h[1-6]|/section|/article)\s*[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\f\v]+", " ", s)
    s = re.sub(r"\n[ \t]+", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# ----------------------------------------------------------------------- main

def main() -> int:
    p = argparse.ArgumentParser(prog="fetch_url")
    p.add_argument("url")
    p.add_argument("--gid", default=None, help="Google Sheets tab id")
    p.add_argument("--max", type=int, default=DEFAULT_MAX)
    p.add_argument("--format", default=None, help="google export format (txt|csv|html|pdf)")
    a = p.parse_args()

    if not re.match(r"^https?://", a.url, re.I):
        fail("Дай ссылку, начинающуюся с http:// или https://")

    is_google = "google.com" in a.url
    export = google_export_url(a.url, a.gid, a.format) if is_google else None

    # Google doc + the agent has a Google identity (service account) → read it directly,
    # which also covers PRIVATE docs shared with the agent. Falls through to the public
    # export URL when there's no key or the SA simply isn't shared on this doc.
    if export:
        try:
            import gauth_read as _ga
        except Exception:
            _ga = None
        if _ga is not None and _ga.have_key():
            try:
                text = _ga.read(a.url, a.gid)
                if text.strip():
                    out = text if len(text) <= a.max else text[:a.max]
                    print(out)
                    if len(text) > a.max:
                        print(f"\n… (показал первые {a.max} символов; в документе больше — скажи, если нужно продолжение)")
                    return 0
            except _ga.NoAccess:
                if _ga.mode() == "sa":
                    em = _ga.sa_email() or "сервис-аккаунтом агента"
                    fail("Этот документ закрыт. Поделись им (доступ «Читатель») с агентом — его адрес:\n"
                         f"{em}\nПосле этого пришли ссылку снова.")
                fail("Под твоим Google-аккаунтом нет доступа к этому документу — проверь, что он "
                     "открывается у тебя, и что ссылка верная.")
            except Exception:
                pass  # SA unavailable / not-this-doc → try the public export below

    target = export or a.url

    try:
        final_url, status, ctype, body = fetch(target)
    except urllib.error.HTTPError as e:
        if is_google and e.code in (401, 403):
            fail("Этот Google-документ не открыт по ссылке. Открой доступ «всем, у кого есть ссылка» "
                 "(просмотр) — или дай мне доступ к Google, тогда смогу читать и закрытые.")
        if e.code == 404:
            fail("Не нашёл документ по ссылке — проверь, что она верная.")
        fail("Не удалось открыть ссылку. Проверь, что она верная и доступна.")
    except Exception:
        fail("Не удалось открыть ссылку. Проверь, что она верная и доступна.")

    if is_google and export and looks_private(final_url, body):
        fail("Этот Google-документ не открыт по ссылке. Открой доступ «всем, у кого есть ссылка» "
             "(просмотр) — или дай мне доступ к Google, тогда смогу читать и закрытые.")

    is_text = export is not None or "text/" in ctype or "csv" in ctype or "json" in ctype
    content = body if is_text and "html" not in ctype else html_to_text(body)
    content = content.strip()
    if not content:
        fail("Страница открылась, но текста в ней не нашлось. Возможно, это динамический сайт — "
             "тогда лучше открыть его через браузерный инструмент.")

    truncated = len(content) > a.max
    if truncated:
        content = content[:a.max]
    print(content)
    if truncated:
        print(f"\n… (показал первые {a.max} символов; в документе больше — скажи, если нужно продолжение)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
