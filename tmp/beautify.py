"""(1) deliver_to=16,22; (2) news format: sources on their own line + blank lines between items;
(3) TG Hermes persona: pretty formatting rules; (4) re-run automation 37 live."""
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from config import MSK_TZ  # noqa: E402
from mcp import context_server as cs  # noqa: E402
from shared.db import connect  # noqa: E402

SLUG = "novostnoy-agent"

ROLE = (
    "Ты — Новостной агент компании Albery (Wildberries и маркетплейсы). Готовишь КОРОТКУЮ денежную "
    "сводку и отвечаешь на вопросы о новостях. Инструменты: get_tg_news (свежие посты каналов), "
    "get_latest_news_digest (последняя сохранённая сводка), save_news_digest, "
    "search_company_knowledge (наши регламенты).\n\n"
    "ГЛАВНЫЙ ПРИНЦИП — ТОЛЬКО ДЕНЬГИ. Бери новость, только если она реально меняет наши "
    "доходы/расходы/риски: комиссии, тарифы, стоимость логистики, выплаты, штрафы, правила по "
    "марже, сдвиги спроса/ранжирования, важные изменения кабинета/API. Всё прочее — общие "
    "рассуждения, мотивация, реклама, самопиар, разговоры, сбои сервисов — НЕ бери. Лучше 3 "
    "денежные новости, чем 15 общих. Дубли объединяй.\n\n"
    "НА ОБЫЧНЫЙ ВОПРОС о новостях: СНАЧАЛА get_latest_news_digest — если is_fresh=true, отвечай "
    "из неё, НЕ пересобирай через get_tg_news.\n\n"
    "ОФОРМЛЕНИЕ (строго; BB-коды Bitrix, без Markdown). Правила читабельности: каждая новая мысль "
    "— с новой строки; после КАЖДОГО пункта и между блоками — ПУСТАЯ строка; ничего не лепи в "
    "кучу. Источники НЕ в тексте пункта: отдельной строкой ПОД пунктом, курсивом-неброско: "
    "«Источники: [URL=https://t.me/имя]имя[/URL], [URL=...]имя2[/URL]».\n\n"
    "Структура сводки:\n"
    "[b]⚡ Коротко[/b]\n2-4 строки, самое денежное, каждая мысль с новой строки.\n\n"
    "[b]📦 Что изменилось (влияет на деньги)[/b]\nКаждый пункт: строка «- суть с цифрой», затем "
    "строка «Источники: …», затем пустая строка. Нечего — «существенного нет».\n\n"
    "[b]✅ Что делаем, чтобы заработать больше[/b]\n0-4 конкретных денежных действия: что сделать, "
    "на что влияет (цена/маржа/расход/оборот), где (наш документ/процесс — проверь через "
    "search_company_knowledge). Каждое действие — отдельным абзацем с пустой строкой после. "
    "НИКАКИХ «изучить/мониторить» без денежного результата. Нечего — «на этой неделе действий не "
    "требуется».\n\nФакты — только из постов и наших документов, ничего не выдумывай."
)

AUTO_PROMPT = (
    "Сделай еженедельную ДЕНЕЖНУЮ сводку новостей. 1) get_tg_news(days=7). 2) оставь ТОЛЬКО "
    "новости, влияющие на деньги, остальное выкинь. 3) для предложений проверь наши регламенты "
    "через search_company_knowledge. 4) выдай СТРОГО в формате своей роли: каждая мысль с новой "
    "строки, ПУСТАЯ строка после каждого пункта и между блоками, источники ОТДЕЛЬНОЙ строкой под "
    "пунктом ([URL=https://t.me/имя]имя[/URL]), разделы ⚡ Коротко / 📦 Что изменилось / ✅ Что "
    "делаем чтобы заработать больше. 5) ОБЯЗАТЕЛЬНО сохрани итог через save_news_digest(summary="
    "<весь текст>). Коротко, без воды."
)

print("role:", cs.tool_update_agent({"slug": SLUG, "role_prompt": ROLE}).get("ok"))
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET prompt=%s, deliver_to=%s WHERE id=37",
                (AUTO_PROMPT, "16,22"))
    conn.commit()
print("automation: prompt updated, deliver_to=16,22")

# --- TG Hermes persona: readable formatting rules -----------------------------------------
CFG = Path("/root/.hermes/config.yaml")
ts = time.strftime("%Y%m%d_%H%M%S")
shutil.copy2(CFG, CFG.with_name(f"config.yaml.bak-persona-fmt-{ts}"))
text = CFG.read_text(encoding="utf-8")
ADD = (
    " ОФОРМЛЕНИЕ ОТВЕТОВ (строго): каждая новая мысль — с новой строки; между пунктами списка и "
    "смысловыми блоками — ПУСТАЯ строка (двойной перенос), ничего не лепи в кучу; заголовок или "
    "ключевую фразу выделяй жирным; перечисления — строками с «— »; длинные полотна дели на "
    "блоки; источники и ссылки — отдельной строкой под мыслью, не внутри предложения. Если "
    "конкретная задача задаёт свой формат — он важнее."
)
m = re.search(r'(    albery: ")(.*?)(")', text, re.DOTALL)
assert m, "albery personality anchor not found"
if "ОФОРМЛЕНИЕ ОТВЕТОВ" not in m.group(2):
    text = text.replace(m.group(0), m.group(1) + m.group(2) + ADD + m.group(3), 1)
    CFG.write_text(text, encoding="utf-8")
    import yaml
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    assert "ОФОРМЛЕНИЕ ОТВЕТОВ" in cfg["agent"]["personalities"]["albery"]
    subprocess.run(["systemctl", "restart", "hermes-gateway"], check=True)
    time.sleep(8)
    state = subprocess.run(["systemctl", "is-active", "hermes-gateway"], capture_output=True, text=True)
    print("hermes-gateway:", state.stdout.strip())
else:
    print("persona already has formatting rules")

# --- re-run automation 37 live --------------------------------------------------------------
fire = datetime.now(MSK_TZ) + timedelta(minutes=2)
once = f"{fire.minute} {fire.hour} {fire.day} {fire.month} *"
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule=%s, last_status=NULL, last_error=NULL WHERE id=37", (once,))
    conn.commit()
print("re-firing at", fire.strftime("%H:%M"))
status = None
for i in range(64):
    time.sleep(15)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT last_status, last_error, last_result FROM agent_automations WHERE id=37")
        row = dict(cur.fetchone())
    if row["last_status"] not in (None, "running"):
        status = row
        break
    if i % 4 == 3:
        print(f"  waiting... {(i+1)*15}s status={row['last_status']}", flush=True)
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule=%s WHERE id=37", ("0 10 * * 0",))
    cur.execute("SELECT count(*) AS n FROM tg_news_digests")
    n = cur.fetchone()["n"]
    conn.commit()
print("schedule restored; digests stored:", n)
print("STATUS:", (status or {}).get("last_status"), "| ERR:", (status or {}).get("last_error"))
print("\n--- delivered (16 и 22) ---\n", ((status or {}).get("last_result") or "")[:2500])
