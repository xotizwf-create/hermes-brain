#!/usr/bin/env python3
"""Send email from the owner's Gmail via the Gmail API (HTTPS).

Exists because the 217 host blocks ALL outbound SMTP (25/465/587) — himalaya
send / msmtp can never work there. The Gmail API goes over 443.

Usage:
    python3 gmail_send.py --to addr [--to addr2] --subject "..." \
        (--body "text" | --body-file path) [--attach path ...] \
        [--cc addr] [--bcc addr] [--html]

Success prints `SENT id=<messageId>` and exits 0. Anything else is a failure —
do not tell the owner the mail was sent.
"""
import argparse
import mimetypes
import os
import sys
from email.message import EmailMessage
from email.utils import formataddr

TOKEN_PATHS = (
    "/root/.hermes/secure/google_oauth_token.json",
    "/root/.hermes/google_token.json",
)
SENDER = ("Александр Никитенко", "alexxandr.nikitenko@gmail.com")
SEND_URL = ("https://gmail.googleapis.com/upload/gmail/v1/users/me/"
            "messages/send?uploadType=media")


def _credentials():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    last_err = None
    for path in TOKEN_PATHS:
        if not os.path.exists(path):
            continue
        try:
            creds = Credentials.from_authorized_user_file(path)
            if not creds.valid:
                creds.refresh(Request())
            return creds
        except Exception as exc:  # try the other path before giving up
            last_err = exc
    raise SystemExit(f"FAIL: no usable Google token ({last_err})")


def build_message(args) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr(SENDER)
    msg["To"] = ", ".join(args.to)
    if args.cc:
        msg["Cc"] = ", ".join(args.cc)
    if args.bcc:
        msg["Bcc"] = ", ".join(args.bcc)
    msg["Subject"] = args.subject

    body = args.body
    if args.body_file:
        with open(args.body_file, encoding="utf-8") as fh:
            body = fh.read()
    if body is None:
        raise SystemExit("FAIL: --body or --body-file is required")
    if args.html:
        msg.set_content("Это письмо в HTML; включите отображение HTML.")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    for path in args.attach or []:
        if not os.path.isfile(path):
            raise SystemExit(f"FAIL: attachment not found: {path}")
        ctype, _ = mimetypes.guess_type(path)
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        with open(path, "rb") as fh:
            msg.add_attachment(fh.read(), maintype=maintype, subtype=subtype,
                               filename=os.path.basename(path))
    return msg


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--to", action="append", required=True)
    p.add_argument("--cc", action="append")
    p.add_argument("--bcc", action="append")
    p.add_argument("--subject", required=True)
    p.add_argument("--body")
    p.add_argument("--body-file")
    p.add_argument("--attach", action="append")
    p.add_argument("--html", action="store_true")
    args = p.parse_args()

    creds = _credentials()
    if "https://www.googleapis.com/auth/gmail.send" not in (creds.scopes or []):
        raise SystemExit("FAIL: token lacks gmail.send scope — re-auth per skills/google-account")

    raw = build_message(args).as_bytes()

    import requests
    resp = requests.post(
        SEND_URL,
        headers={"Authorization": f"Bearer {creds.token}",
                 "Content-Type": "message/rfc822"},
        data=raw, timeout=120,
    )
    if resp.status_code == 200:
        print(f"SENT id={resp.json().get('id')}")
        return 0
    print(f"FAIL: HTTP {resp.status_code}: {resp.text[:400]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
