"""Fetch a t.me/addlist/<hash> folder page and extract channel usernames/titles (read-only)."""
import re
import urllib.request

URL = "https://t.me/addlist/VkuxSZiKJvA4MTli"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

req = urllib.request.Request(URL, headers={"User-Agent": UA})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    print("HTTP OK, length:", len(html))
except Exception as exc:  # noqa: BLE001
    print("FETCH ERROR:", str(exc)[:200])
    raise SystemExit(1)

# folder title
mt = re.search(r'<div class="tgme_page_title"[^>]*>\s*<span[^>]*>(.*?)</span>', html, re.DOTALL)
print("folder title:", (mt.group(1).strip() if mt else "?"))

# channel usernames (t.me/<name>) and any visible titles
usernames = sorted(set(re.findall(r'https://t\.me/([A-Za-z0-9_]{4,32})(?![/\w])', html)))
usernames = [u for u in usernames if u.lower() not in {"addlist", "share", "joinchat"}]
print("usernames found:", usernames)

titles = re.findall(r'<div class="tgme_page_title"[^>]*>(.*?)</div>', html, re.DOTALL)
clean = [re.sub(r"<[^>]+>", "", t).strip() for t in titles]
print("titles:", [t for t in clean if t][:40])

# raw peers block sample for manual inspection
peers = re.findall(r'tgme_widget_[a-z]+|data-[a-z-]+="[^"]+"', html)
print("markers sample:", peers[:20])
print("\n--- first 1500 chars ---\n", html[:1500])
