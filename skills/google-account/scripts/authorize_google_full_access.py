#!/usr/bin/env python3
"""Run ONCE on the owner's PC to authorize FULL Google access (Drive/Sheets/Docs WRITE + Apps
Script) for the ALBERY agent's own Google account.

Why on the PC: Google blocks the OAuth consent screen from datacenter IPs, so the browser login
must happen on a residential machine. This produces a refresh token we then install on the ALBERY
box; after that the bot works headless with no further logins.

Steps:
    pip install google-auth-oauthlib
    python authorize_google_full_access.py <client_secret.json> [token.json]

- <client_secret.json> = OAuth client of type "Desktop app", downloaded from the Google Cloud
  project of ALBERY's Google account (APIs enabled: Drive, Sheets, Docs, Apps Script).
- In the browser, log in with ALBERY's Google account, click through the "Google hasn't verified
  this app" warning (Advanced → Go to … (unsafe)) → Allow.
- It writes token.json (refresh token + client id/secret). That file is a SECRET — send it to the
  agent as a FILE, never paste its contents. It will be installed on the albery box at
  /root/.hermes/secure/google_oauth_token.json and /root/.hermes/google_token.json (chmod 600).

Prerequisite: enable the Apps Script API toggle once at
https://script.google.com/home/usersettings (and script.googleapis.com in the Cloud project).
"""
import sys

for _s in (sys.stdout, sys.stderr):  # Windows console may be cp125x; keep emoji/Cyrillic safe
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python authorize_google_full_access.py <client_secret.json> [token.json]")
        return 2
    client = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "token.json"
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except Exception:
        print("Нужен пакет: pip install google-auth-oauthlib")
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(client, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    if not creds.refresh_token:
        print("⚠️ Не получили refresh-токен. Убедись, что это первый вход этого клиента "
              "(prompt=consent уже выставлен).")
        return 1
    with open(out, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"✅ Токен сохранён: {out}. Пришли этот файл агенту (как файл, не текстом) — "
          "поставлю его на albery-бокс.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
