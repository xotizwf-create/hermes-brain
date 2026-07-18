"""Fix the news agent: (1) members only Никитенко(16) + ИИ Агент(22); (2) beautiful format
with a TL;DR on top and clickable channel links; (3) re-run the automation to verify."""
import json
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
import agent_center  # noqa: E402
import b24bot  # noqa: E402
from config import MSK_TZ  # noqa: E402
from mcp import context_server as cs  # noqa: E402
from shared.db import connect, load_env_value  # noqa: E402

SLUG = "novostnoy-agent"

ROLE = (
    "Ты — Новостной агент компании Albery (продажи на Wildberries и маркетплейсах). Твоя работа — "
    "готовить короткую еженедельную выжимку из отраслевых Telegram-каналов и отвечать на вопросы о "
    "новостях. Источник — инструмент get_tg_news (один вызов = свежие посты всех отслеживаемых "
    "каналов; channels=['имя'] — детали конкретного канала).\n\n"
    "БЕРИ ТОЛЬКО: (1) изменения на маркетплейсах — комиссии, тарифы, логистика, правила, штрафы, "
    "выплаты, кабинет/API; (2) организационные и управленческие практики, которые стоит перенять; "
    "(3) внедрения ИИ и автоматизации в e-commerce.\n\n"
    "ЖЁСТКО ПРОПУСКАЙ: рекламу курсов и сервисов, самопиар и продажи, разговорные и мотивационные "
    "посты, мемы, розыгрыши, сбои/проблемы локальных сервисов, воду без фактов. Одну новость бери "
    "один раз (все источники перечисли).\n\n"
    "ОФОРМЛЕНИЕ (строго; без Markdown — только BB-коды Bitrix):\n"
    "1. Первый блок — [b]⚡ Главное за неделю[/b]: 3-5 самых важных пунктов одной строкой каждый — "
    "суперкратко, только суть (это читают за 20 секунд).\n"
    "2. Затем пустая строка и детальные разделы: [b]📦 Маркетплейсы[/b], [b]🏢 Оргпрактики[/b], "
    "[b]🤖 ИИ и автоматизация[/b]. Каждый пункт: «- » + суть в 1-2 строки + источники. Пустой "
    "раздел = одна строка «ничего важного». Между разделами пустая строка.\n"
    "3. ИСТОЧНИКИ ВСЕГДА кликабельными ссылками: [URL=https://t.me/имя]имя[/URL] (url каналов "
    "отдаёт get_tg_news). Несколько источников — через запятую.\n"
    "4. Финальный, ГЛАВНЫЙ раздел — [b]✅ Что предлагаю сделать нам[/b] (до 5 пунктов, только "
    "реально стоящие): по значимой оргпрактике СНАЧАЛА проверь наши регламенты через "
    "search_company_knowledge — если такого у нас нет, предложи «внедрить в \"<название нашего "
    "документа>\"» или создать новый регламент; по изменению комиссий/логистики WB — конкретное "
    "действие с ценами, маржой, стратегией; по ИИ-кейсу — где у нас это применимо. Каждый пункт: "
    "что сделать, где (документ/процесс), почему (какая новость, со ссылкой на канал).\n"
    "Факты — только из постов и наших документов, ничего не выдумывай."
)

AUTO_PROMPT = (
    "Подготовь еженедельную новостную выжимку по своей роли. Шаги: 1) get_tg_news(days=7) — свежие "
    "посты всех отслеживаемых каналов; 2) отбери только значимое (маркетплейсы / оргпрактики / ИИ), "
    "отфильтруй весь шум по своим правилам; 3) для лучших оргпрактик проверь через "
    "search_company_knowledge, есть ли такое в наших регламентах; 4) выдай сообщение СТРОГО в своём "
    "формате: сначала [b]⚡ Главное за неделю[/b] (3-5 суперкратких строк), потом детальные разделы "
    "с кликабельными ссылками на каналы ([URL=https://t.me/имя]имя[/URL]), в конце "
    "[b]✅ Что предлагаю сделать нам[/b]. Если неделя пустая — скажи это коротко."
)

# 1) role prompt
r = cs.tool_update_agent({"slug": SLUG, "role_prompt": ROLE})
print("role updated:", r.get("ok", r))

# 2) members: ТОЛЬКО Александр Никитенко (16) + ИИ Агент (22)
r = cs._mgmt_endpoint("PATCH", f"/api/agent-center/agents/{SLUG}",
                      agent_center.agent_center_agent_update, SLUG,
                      json_body={"members": [16, 22]})
print("members set:", json.dumps(r, ensure_ascii=False)[:200])

# 3) automation prompt
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET prompt = %s WHERE id = 37", (AUTO_PROMPT,))
    conn.commit()
print("automation prompt updated")

# 4) re-run once through the live scheduler
fire = datetime.now(MSK_TZ) + timedelta(minutes=2)
once = f"{fire.minute} {fire.hour} {fire.day} {fire.month} *"
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule = %s, last_status = NULL, last_error = NULL "
                "WHERE id = 37", (once,))
    conn.commit()
print("re-firing at", fire.strftime("%H:%M"))
status = None
for i in range(60):
    time.sleep(15)
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT last_status, last_error FROM agent_automations WHERE id = 37")
        row = dict(cur.fetchone())
    if row["last_status"] not in (None, "running"):
        status = row
        break
    if i % 4 == 3:
        print(f"  waiting... {(i + 1) * 15}s status={row['last_status']}", flush=True)
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule = %s WHERE id = 37", ("0 10 * * 0",))
    conn.commit()
print("schedule restored; run:", json.dumps(status, ensure_ascii=False) if status else "NOT FINISHED")

endpoint, token = b24bot._b24_app_access_token()
chat = (load_env_value("ALBERY_BITRIX_NOTIFY_CHAT") or "chat728").strip()
data = b24bot._b24_app_call(endpoint, token, "im.dialog.messages.get", {"DIALOG_ID": chat, "LIMIT": 1})
for m in (data.get("result") or {}).get("messages") or []:
    print(f"\n--- delivered msg [{m.get('id')}] author={m.get('author_id')} ---")
    print(str(m.get("text") or "")[:3500])
