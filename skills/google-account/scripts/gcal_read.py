#!/usr/bin/env python3
"""gcal_read — read the owner's Google Calendar agenda (read-only) under the agent's Google profile.

Uses the same credentials as gauth_read (OAuth token at /root/.hermes/secure/google_oauth_token.json,
or a service-account key). Russian output, no technical noise. Usage:
    python3 gcal_read.py [--days N] [--max N] [--calendar primary]
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

OAUTH = os.environ.get("HERMES_GOOGLE_OAUTH", "/root/.hermes/secure/google_oauth_token.json")
KEY = os.environ.get("HERMES_GOOGLE_SA", "/root/.hermes/secure/google_service_account.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def fail(msg: str):
    print(msg)
    raise SystemExit(1)


def _credentials():
    if os.path.exists(OAUTH):
        from google.oauth2.credentials import Credentials
        return Credentials.from_authorized_user_file(OAUTH, SCOPES)
    if os.path.exists(KEY):
        from google.oauth2 import service_account
        return service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    fail("Google-аккаунт ещё не подключён.")


def _fmt(ev) -> str:
    start = ev.get("start", {})
    when = start.get("dateTime") or start.get("date") or ""
    when = when.replace("T", " ")[:16]
    title = ev.get("summary", "(без названия)")
    loc = ev.get("location")
    return f"📅 {when} — {title}" + (f" ({loc})" if loc else "")


def main() -> int:
    p = argparse.ArgumentParser(prog="gcal_read")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--max", type=int, default=25)
    p.add_argument("--calendar", default="primary")
    a = p.parse_args()

    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except Exception:
        fail("Не получилось обратиться к Google — попробуй позже.")

    creds = _credentials()
    now = dt.datetime.now(dt.timezone.utc)
    tmin = now.isoformat()
    tmax = (now + dt.timedelta(days=a.days)).isoformat()
    try:
        svc = build("calendar", "v3", credentials=creds, cache_discovery=False)
        items = svc.events().list(
            calendarId=a.calendar, timeMin=tmin, timeMax=tmax,
            maxResults=a.max, singleEvents=True, orderBy="startTime",
        ).execute().get("items", [])
    except HttpError:
        fail("Нет доступа к календарю под твоим аккаунтом. Проверь подключение Google.")
    except Exception:
        fail("Не получилось прочитать календарь. Попробуй позже.")

    if not items:
        print(f"На ближайшие {a.days} дн. событий нет.")
        return 0
    print(f"События на ближайшие {a.days} дн.:")
    for ev in items:
        print("  " + _fmt(ev))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
