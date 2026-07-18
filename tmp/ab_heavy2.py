"""Repeat the heavy digest turn 2x per model and score COVERAGE of the week's key money facts.
Single samples lie; this checks whether Terra consistently drops big items on huge inputs."""
import re
import subprocess
import time

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}
PROMPT = (
    "Сделай еженедельную сводку новостей: get_tg_news(days=7), отбери ДЕНЕЖНЫЕ новости, выдай "
    "разделы [b]⚡ Коротко[/b], [b]📦 Что изменилось[/b] (источники отдельной строкой), "
    "[b]✅ Что делаем[/b]. НЕ вызывай save_news_digest — тестовый прогон."
)
# key money facts of this week (from the real digests we already validated)
FACTS = {
    "ИРП (отмена 13.07)": r"ИРП",
    "рост комиссий": r"комисси",
    "перераспределение остатков": r"перераспредел|перемещен",
    "реклама/кластеры": r"кластер|поисковых фраз|реклам",
}


def score(text: str) -> tuple[int, list[str]]:
    hit = [name for name, rx in FACTS.items() if re.search(rx, text, re.IGNORECASE)]
    return len(hit), hit


for model in ("gpt-5.5", "gpt-5.6-terra", "gpt-5.6-terra"):
    t0 = time.time()
    try:
        r = subprocess.run(["hermes", "-z", PROMPT, "--provider", "openai-codex", "-m", model,
                            "-t", "agent-novostnoy-agent,web", "--yolo"],
                           capture_output=True, text=True, timeout=600, cwd="/root", env=ENV)
        dt = time.time() - t0
        out = (r.stdout or "").strip()
        n, hits = score(out)
        items = len(re.findall(r"^\s*[-•]\s", out, re.MULTILINE))
        print(f"[{model}] {dt:.0f}s len={len(out)} пунктов={items} фактов={n}/4 {hits}")
    except subprocess.TimeoutExpired:
        print(f"[{model}] TIMEOUT >600s")
