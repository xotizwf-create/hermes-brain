"""Heavy A/B: the full news-digest turn (huge tool input + long structured output) — the exact
shape of turn that used to break the connection on gpt-5.5. Read-only-ish; any test digest row
is deleted afterwards."""
import subprocess
import sys
import time

sys.path.insert(0, "/var/www/albery")
from shared.db import connect  # noqa: E402

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}

PROMPT = (
    "Сделай еженедельную сводку новостей: вызови get_tg_news(days=7), отбери денежные новости и "
    "орг-кейсы с результатом, проверь наши регламенты через search_company_knowledge и выдай "
    "структурированную сводку с разделами [b]⚡ Коротко[/b], [b]📦 Что изменилось[/b] "
    "(источники отдельной строкой), [b]✅ Что делаем[/b]. НЕ сохраняй через save_news_digest — "
    "это тестовый прогон, просто верни текст."
)

with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT max(id) AS m FROM tg_news_digests")
    before = cur.fetchone()["m"] or 0

for model in ("gpt-5.5", "gpt-5.6-terra"):
    t0 = time.time()
    try:
        r = subprocess.run(["hermes", "-z", PROMPT, "--provider", "openai-codex", "-m", model,
                            "-t", "agent-novostnoy-agent,web", "--yolo"],
                           capture_output=True, text=True, timeout=600, cwd="/root", env=ENV)
        dt = time.time() - t0
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        ok = r.returncode == 0 and len(out) > 500
        print(f"\n[{model}] {'OK ' if ok else 'FAIL'} {dt:.0f}s rc={r.returncode} len={len(out)}")
        # quality markers
        print("  разделы:", all(k in out for k in ("Коротко", "изменилось", "делаем")),
              "| источники-ссылки:", out.count("t.me/"),
              "| цифры(комиссии/ИРП):", ("ИРП" in out), ("43,5" in out or "9%" in out))
        if err and not ok:
            print("  stderr:", err[:300])
        print("  head:", out[:260].replace("\n", " / "))
    except subprocess.TimeoutExpired:
        print(f"\n[{model}] TIMEOUT >600s (это и есть срыв тяжёлого хода)")

with connect() as conn, conn.cursor() as cur:
    cur.execute("DELETE FROM tg_news_digests WHERE id > %s", (before,))
    n = cur.rowcount
    conn.commit()
print(f"\ncleanup: удалено тестовых сводок {n}")
