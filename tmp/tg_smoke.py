"""Smoke: t.me/s/ preview scraper on a real public channel + a hermes turn from this box."""
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/var/www/albery")
import tg_agent  # noqa: E402
import tg_digest  # noqa: E402

tg_agent._load_env_file()

posts, err = tg_digest.fetch_channel_posts("durov", datetime.now(timezone.utc) - timedelta(days=60))
print("scraper t.me/s/durov:", ("ERR " + err) if err else f"OK {len(posts)} posts")
if posts:
    print("  sample:", posts[-1][:140].replace("\n", " "))

answer = tg_agent.hermes_answer("Ответь ровно одним словом: работаю", "tg-smoke",
                                toolsets="web", timeout_s=180)
print("hermes turn:", answer[:100])
