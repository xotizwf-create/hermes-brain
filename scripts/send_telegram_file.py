#!/usr/bin/env python3
"""Send a file to the owner's Telegram chat via the @GoogleDeck_Bot Bot API.

Token is read from the secure store (never printed/committed).
Usage: send_tg.py <file> [--caption "text"] [--chat <id>]
"""
import sys, json, mimetypes, urllib.request, urllib.error, uuid, os

TOKEN_PATH = "/root/.hermes/secure/claude_code/bot_token"
DEFAULT_CHAT = "1451982360"  # owner DM (Александр Никитенко)

def main():
    args = sys.argv[1:]
    if not args:
        print("usage: send_tg.py <file> [--caption TEXT] [--chat ID]"); sys.exit(2)
    path = args[0]
    caption, chat = "", DEFAULT_CHAT
    i = 1
    while i < len(args):
        if args[i] == "--caption": caption = args[i+1]; i += 2
        elif args[i] == "--chat": chat = args[i+1]; i += 2
        else: i += 1
    if not os.path.isfile(path):
        print(f"no such file: {path}"); sys.exit(1)
    token = open(TOKEN_PATH).read().strip()

    fname = os.path.basename(path)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        data = f.read()

    parts = []
    def field(name, val):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{val}\r\n".encode())
    field("chat_id", chat)
    if caption: field("caption", caption)
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{fname}\"\r\n"
        f"Content-Type: {ctype}\r\n\r\n".encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        out = json.load(resp)
        print("OK" if out.get("ok") else f"FAIL: {out}")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}"); sys.exit(1)

if __name__ == "__main__":
    main()
