"""Create «Новостной агент»: Bitrix bot + narrow toolset + Sunday automation (10:00 МСК)."""
import json
import sys

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401  (import order: app first)
import agent_center  # noqa: E402
from mcp import context_server as cs  # noqa: E402
from shared.db import connect  # noqa: E402

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
    "один раз (источники перечисли через запятую).\n\n"
    "ФОРМАТ (без Markdown, жирный только [b]...[/b]): разделы [b]Маркетплейсы[/b], [b]Оргпрактики[/b], "
    "[b]ИИ и автоматизация[/b]; пункт = суть в 1-2 строки + источник (имя канала). Пустой раздел = "
    "строка «ничего важного».\n\n"
    "ГЛАВНЫЙ раздел — [b]Что предлагаю сделать нам[/b] (до 5 пунктов, только реально стоящие): "
    "по значимой оргпрактике СНАЧАЛА проверь наши регламенты через search_company_knowledge — если "
    "такого у нас нет, предложи «внедрить в \"<название нашего документа>\"» или создать новый "
    "регламент; по изменению комиссий/логистики WB — конкретное действие с ценами, маржой, "
    "стратегией; по ИИ-кейсу — где у нас это применимо. Каждый пункт: что сделать, где "
    "(документ/процесс), почему (какая новость). Факты — только из постов и наших документов, "
    "ничего не выдумывай."
)

TOOLSET = ["start_here_always_read_ai_instructions", "get_tg_news", "search_company_knowledge",
           "list_company_files", "get_company_file", "fetch_url"]

AUTO_PROMPT = (
    "Подготовь еженедельную новостную выжимку по своей роли. Шаги: 1) get_tg_news(days=7) — свежие "
    "посты всех отслеживаемых каналов; 2) отбери только значимое (маркетплейсы / оргпрактики / ИИ), "
    "отфильтруй весь шум по своим правилам; 3) для лучших оргпрактик проверь через "
    "search_company_knowledge, есть ли такое в наших регламентах; 4) выдай сообщение строго в своём "
    "формате, обязательно с разделом [b]Что предлагаю сделать нам[/b]. Если неделя пустая — скажи "
    "это коротко, без воды."
)

res = cs.tool_create_agent({"name": "Новостной агент",
                            "position": "Аналитик новостей маркетплейсов",
                            "role_prompt": ROLE, "members": []})
print("create_agent:", json.dumps(res, ensure_ascii=False)[:400])
slug = res.get("slug") or (res.get("agent") or {}).get("slug")
if not slug:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT slug FROM agents WHERE name = %s", ("Новостной агент",))
        row = cur.fetchone()
        slug = row["slug"] if row else None
print("slug:", slug)
assert slug, "agent slug not resolved"

cfg = cs._mgmt_endpoint("GET", f"/api/agent-center/agents/{slug}/config",
                        agent_center.agent_center_agent_config, slug)
valid = {t["name"] for t in cfg["tools"]}
missing = [t for t in TOOLSET if t not in valid]
print("missing from valid registry:", missing)
save = cs._mgmt_endpoint("PUT", f"/api/agent-center/agents/{slug}/config",
                         agent_center.agent_center_agent_config_save, slug,
                         json_body={"tools": [t for t in TOOLSET if t in valid],
                                    "instructions": [i["id"] for i in cfg["instructions"] if i.get("selected")],
                                    "skills": []})
print("tools saved:", json.dumps(save, ensure_ascii=False)[:200])

with connect() as conn, conn.cursor() as cur:
    cur.execute(
        "INSERT INTO agent_automations (agent_slug, name, description, schedule, prompt, "
        "deliver_to, kind, created_by, creator_label) "
        "VALUES (%s, %s, %s, %s, %s, %s, 'agent', 'owner', %s) "
        "ON CONFLICT (agent_slug, name) DO NOTHING RETURNING id",
        (slug, "Воскресная выжимка новостей",
         "Еженедельный обзор отраслевых TG-каналов: маркетплейсы, оргпрактики, ИИ + предложения для нас",
         "0 10 * * 0", AUTO_PROMPT, "", "владелец (через Claude)"))
    created = cur.fetchone()
    conn.commit()
print("automation id:", created["id"] if created else "(already existed)")

cfg2 = cs._mgmt_endpoint("GET", f"/api/agent-center/agents/{slug}/config",
                         agent_center.agent_center_agent_config, slug)
enabled = sorted(t["name"] for t in cfg2["tools"] if t["enabled"])
print("enabled tools now:", enabled)
