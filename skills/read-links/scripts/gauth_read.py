#!/usr/bin/env python3
"""gauth_read — read private Google Docs/Sheets/Slides via the agent's service account.

The agent has a Google identity: a service-account key at
/root/.hermes/secure/google_service_account.json (mode 600, NOT in git; override with
HERMES_GOOGLE_SA). The owner shares docs/folders with the service-account e-mail, and this module
reads them via the read-only Drive/Sheets APIs. fetch_url.py uses it for Google links when the key
is present, and falls back to the public export URL otherwise.

Returns clean text. Raises NoAccess (share the doc with the SA) or NotGoogle / Unavailable so the
caller can show a Russian message. Used only when a key exists — google libs are imported lazily.
"""
from __future__ import annotations

import json
import os
import re

KEY = os.environ.get("HERMES_GOOGLE_SA", "/root/.hermes/secure/google_service_account.json")
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]
_FILE = re.compile(r"/(document|spreadsheets|presentation)/d/([A-Za-z0-9_-]+)")
_DRIVE = re.compile(r"(?:/file/d/|[?&]id=)([A-Za-z0-9_-]+)")


class NoAccess(Exception):
    pass


class NotGoogle(Exception):
    pass


class Unavailable(Exception):
    pass


def have_key() -> bool:
    return os.path.exists(KEY)


def sa_email() -> str | None:
    try:
        with open(KEY, encoding="utf-8") as fh:
            return json.load(fh).get("client_email")
    except Exception:
        return None


def _ident(url: str):
    m = _FILE.search(url)
    if m:
        return m.group(1), m.group(2)
    m = _DRIVE.search(url)
    if m and "drive.google.com" in url:
        return "drive", m.group(1)
    return None, None


def _csv_field(v) -> str:
    s = "" if v is None else str(v)
    return '"' + s.replace('"', '""') + '"' if any(c in s for c in ',"\n') else s


def read(url: str, gid: str | None = None) -> str:
    if not have_key():
        raise Unavailable("no service account key")
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except Exception as e:  # libs missing
        raise Unavailable(f"google libs unavailable: {e}")

    kind, fid = _ident(url)
    if not fid:
        raise NotGoogle("not a google doc url")

    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    try:
        if kind == "spreadsheets":
            svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
            meta = svc.spreadsheets().get(spreadsheetId=fid).execute()
            blocks = []
            for sh in meta.get("sheets", []):
                props = sh.get("properties", {})
                title = props.get("title", "Лист")
                sgid = str(props.get("sheetId"))
                if gid and sgid != str(gid):
                    continue
                rng = f"'{title}'"
                vals = svc.spreadsheets().values().get(
                    spreadsheetId=fid, range=rng).execute().get("values", [])
                rows = "\n".join(",".join(_csv_field(c) for c in row) for row in vals)
                blocks.append(f"# {title}\n{rows}".rstrip())
            return "\n\n".join(blocks).strip()

        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        data = drive.files().export(fileId=fid, mimeType="text/plain").execute()
        return data.decode("utf-8", "replace") if isinstance(data, (bytes, bytearray)) else str(data)
    except HttpError as e:
        status = getattr(getattr(e, "resp", None), "status", None)
        if status in (401, 403, 404):
            raise NoAccess(str(status))
        raise Unavailable(f"google api error: {status}")
