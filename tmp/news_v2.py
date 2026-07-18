"""News agent v2: money-only role, private delivery to Nikitenko(16), leave notify group,
add digest tools, re-run live and verify delivery + storage."""
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
NIKITENKO = 16

ROLE = (
    "Ты — Новостной агент компании Albery (Wildberries и маркетплейсы). Готовишь КОРОТКУЮ денежную "
    "сводку и отвечаешь на вопросы о новостях. Инструменты: get_tg_news (свежие посты каналов), "
    "get_latest_news_digest (последняя сохранённая сводка), save_news_digest, "
    "search_company_knowledge (наши регламенты).\n\n"
    "ГЛАВНЫЙ ПРИНЦИП — ТОЛЬКО ДЕНЬГИ. Бери новость, только если она реально меняет наши "
    "доходы/расходы/риски: комиссии, тарифы, стоимость логистики, выплаты, штрафы, правила по "
    "марже, сдвиги спроса/ранжирования, важные изменения кабинета/API. Всё прочее — общие "
    "рассуждения, мотивация, реклама курсов, самопиар, разговоры, сбои сервисов, «полезные "
    "практики вообще» — НЕ бери. Лучше 3 денежные новости, чем 15 общих. Дубли объединяй.\n\n"
    "НА ОБЫЧНЫЙ ВОПРОС о новостях (не автоматизация): СНАЧАЛА get_latest_news_digest — если "
    "is_fresh=true, отвечай из неё, НЕ пересобирай через get_tg_news.\n\n"
    "ФОРМАТ (BB-коды Bitrix, без Markdown), коротко:\n"
    "[b]⚡ Коротко[/b] — 2-4 строки, самое денежное за неделю.\n\n"
    "[b]📦 Что изменилось (влияет на деньги)[/b] — «- » пункт: что + цифра/суть + источник "
    "[URL=https://t.me/имя]имя[/URL]. Только денежное. Нечего — строка «существенного нет».\n\n"
    "[b]✅ Что делаем, чтобы заработать больше[/b] — ТОЛЬКО конкретные денежные действия (0-4): что "
    "сделать, на что влияет (цена/маржа/расход/оборот) и где (наш документ/процесс — проверь через "
    "search_company_knowledge). НИКАКИХ «изучить/мониторить/обратить внимание» без денежного "
    "результата. Нечего — честно «на этой неделе действий не требуется».\n\n"
    "Факты — только из постов и наших документов, ничего не выдумывай."
)

AUTO_PROMPT = (
    "Сделай еженедельную ДЕНЕЖНУЮ сводку новостей. 1) get_tg_news(days=7). 2) оставь ТОЛЬКО "
    "новости, влияющие на деньги (комиссии/тарифы/логистика/выплаты/штрафы/правила по марже/"
    "спрос/кабинет), остальное выкинь. 3) для предложений проверь наши регламенты через "
    "search_company_knowledge. 4) выдай СТРОГО в формате: [b]⚡ Коротко[/b] (2-4 строки), "
    "[b]📦 Что изменилось (влияет на деньги)[/b] с кликабельными ссылками "
    "[URL=https://t.me/имя]имя[/URL], [b]✅ Что делаем, чтобы заработать больше[/b] — только "
    "конкретные денежные действия (если нечего — «на этой неделе действий не требуется»). "
    "5) ОБЯЗАТЕЛЬНО сохрани итоговый текст через save_news_digest(summary=<весь текст сводки>). "
    "Коротко, без воды."
)

TOOLSET = ["start_here_always_read_ai_instructions", "get_tg_news", "get_latest_news_digest",
           "save_news_digest", "search_company_knowledge", "list_company_files",
           "get_company_file", "fetch_url"]

# 1) role
print("role:", cs.tool_update_agent({"slug": SLUG, "role_prompt": ROLE}).get("ok"))

# 2) toolset (add digest tools)
cfg = cs._mgmt_endpoint("GET", f"/api/agent-center/agents/{SLUG}/config",
                        agent_center.agent_center_agent_config, SLUG)
valid = {t["name"] for t in cfg["tools"]}
print("missing:", [t for t in TOOLSET if t not in valid])
cs._mgmt_endpoint("PUT", f"/api/agent-center/agents/{SLUG}/config",
                  agent_center.agent_center_agent_config_save, SLUG,
                  json_body={"tools": [t for t in TOOLSET if t in valid],
                             "instructions": [i["id"] for i in cfg["instructions"] if i.get("selected")],
                             "skills": []})
print("toolset saved")

# 3) automation: prompt + deliver_to = Nikitenko private
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET prompt = %s, deliver_to = %s WHERE id = 37",
                (AUTO_PROMPT, str(NIKITENKO)))
    conn.commit()
print("automation updated: deliver_to =", NIKITENKO)

# 4) remove the news bot (80) from the notifications group
endpoint, token = b24bot._b24_app_access_token()
notify_chat = (load_env_value("ALBERY_BITRIX_NOTIFY_CHAT") or "chat728").strip()
notify_id = int(notify_chat.replace("chat", ""))
# verify Nikitenko identity on this portal
try:
    u = b24bot._b24_app_call(endpoint, token, "user.get", {"ID": NIKITENKO}).get("result") or []
    if u:
        print("recipient 16 =", " ".join(x for x in (u[0].get("NAME"), u[0].get("LAST_NAME")) if x))
except Exception as exc:  # noqa: BLE001
    print("user.get failed:", str(exc)[:150])
try:
    r = b24bot._b24_app_call(endpoint, token, "im.chat.user.delete",
                             {"CHAT_ID": notify_id, "USER_ID": 80})
    print("removed bot 80 from notify group:", r.get("result"))
except Exception as exc:  # noqa: BLE001
    print("chat.user.delete note:", str(exc)[:150])

# 5) re-run live
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
        cur.execute("SELECT last_status, last_error, result_text FROM agent_automations WHERE id=37")
        row = dict(cur.fetchone())
    if row["last_status"] not in (None, "running"):
        status = row
        break
    if i % 4 == 3:
        print(f"  waiting... {(i+1)*15}s status={row['last_status']}", flush=True)
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET schedule=%s WHERE id=37", ("0 10 * * 0",))
    conn.commit()
print("schedule restored. status:", status["last_status"] if status else "NOT FINISHED",
      "| err:", (status or {}).get("last_error"))

# 6) verify a digest was stored
with connect() as conn, conn.cursor() as cur:
    cur.execute("SELECT id, created_at, length(summary) AS len FROM tg_news_digests ORDER BY created_at DESC LIMIT 1")
    d = cur.fetchone()
print("stored digest:", dict(d) if d else "NONE")
if status:
    print("\n--- delivered text ---\n", (status.get("result_text") or "")[:3000])
