#!/usr/bin/env python3
"""gauth_read — read Google Docs/Sheets/Slides under the agent's Google profile.

The agent's profile is the OWNER'S Google account via OAuth (read-only): an authorized-user token
at /root/.hermes/secure/google_oauth_token.json lets the agent read everything the owner can access,
with no per-doc sharing. (A service-account key at /root/.hermes/secure/google_service_account.json
is supported as an alternative — then docs must be shared with the SA e-mail.)

fetch_url.py uses this for Google links when a token/key is present, and falls back to the public
export URL otherwise. Returns clean text. Raises NoAccess / NotGoogle / Unavailable so the caller can
show a Russian message. Google libs are imported lazily (only when creds exist).
"""
from __future__ import annotations

import json
import os
import re

OAUTH = os.environ.get("HERMES_GOOGLE_OAUTH", "/root/.hermes/secure/google_oauth_token.json")
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


def mode() -> str | None:
    if os.path.exists(OAUTH):
        return "oauth"
    if os.path.exists(KEY):
        return "sa"
    return None


def have_key() -> bool:
    return mode() is not None


def sa_email() -> str | None:
    try:
        with open(KEY, encoding="utf-8") as fh:
            return json.load(fh).get("client_email")
    except Exception:
        return None


def _credentials():
    m = mode()
    if m == "oauth":
        from google.oauth2.credentials import Credentials
        return Credentials.from_authorized_user_file(OAUTH, SCOPES)
    if m == "sa":
        from google.oauth2 import service_account
        return service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    raise Unavailable("no google credentials")


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
        raise Unavailable("no google credentials")
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except Exception as e:
        raise Unavailable(f"google libs unavailable: {e}")

    kind, fid = _ident(url)
    if not fid:
        raise NotGoogle("not a google doc url")

    creds = _credentials()
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
                vals = svc.spreadsheets().values().get(
                    spreadsheetId=fid, range=f"'{title}'").execute().get("values", [])
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
