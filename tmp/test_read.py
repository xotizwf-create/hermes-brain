"""Test what the bot actually sees NOW: fetch every watchlist channel via t.me/s/ preview."""
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/var/www/albery")
import tg_agent  # noqa: E402
import tg_digest  # noqa: E402

tg_agent._load_env_file()
names = tg_agent.channels()
since = datetime.now(timezone.utc) - timedelta(days=7)

ok, empty, blocked = [], [], []
total_posts = 0
for name in names:
    posts, err = tg_digest.fetch_channel_posts(name, since)
    if err:
        blocked.append((name, err))
    elif posts:
        ok.append((name, len(posts)))
        total_posts += len(posts)
    else:
        empty.append(name)

print(f"=== ЧИТАЕТСЯ ({len(ok)} каналов, {total_posts} постов за 7 дней) ===")
for name, n in sorted(ok, key=lambda x: -x[1]):
    print(f"  ✅ t.me/{name}: {n} постов")
print(f"\n=== ПУСТО за 7 дней ({len(empty)}) ===")
print("  " + ", ".join(empty))
print(f"\n=== НЕ ПРОЧИТАЛ ({len(blocked)}) ===")
for name, err in blocked:
    print(f"  ⚠️ t.me/{name}: {err}")

# sample of real content from the top channel, to prove it's real
if ok:
    top = sorted(ok, key=lambda x: -x[1])[0][0]
    posts, _ = tg_digest.fetch_channel_posts(top, since)
    print(f"\n=== ПРИМЕР контента из t.me/{top} ===")
    print(posts[-1][:300] if posts else "(нет)")
