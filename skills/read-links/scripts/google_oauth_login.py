#!/usr/bin/env python3
"""Run ONCE on the owner's PC to authorize the agent to read their Google Drive (read-only).

Why on the PC: Google blocks the OAuth consent screen from datacenter IPs (same issue as Codex), so
the browser login must happen on a residential machine. This produces a refresh token we then copy to
the server; after that the agent works headless with no further logins.

Needs the OAuth client JSON (type "Desktop app") downloaded from Google Cloud Console, and the
`google-auth-oauthlib` package:
    pip install google-auth-oauthlib
    python google_oauth_login.py <client_secret.json> [token.json]

Opens the browser, you consent, and it writes token.json (refresh token + client id/secret). That
file is a secret — it is gitignored; deliver it to the server as
/root/.hermes/secure/google_oauth_token.json (chmod 600). Never commit or paste it.
"""
import sys

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python google_oauth_login.py <client_secret.json> [token.json]")
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
        print("⚠️ Не получили refresh-токен. Повтори с prompt=consent (уже выставлен) и убедись, "
              "что это первый вход этого клиента.")
        return 1
    with open(out, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"✅ Токен сохранён: {out}. Дальше его кладём на сервер (secure store).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
