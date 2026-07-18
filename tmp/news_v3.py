"""(1) Extend the universal «Формат ответа» instruction with the pretty-formatting standard
(via upsert -> DB + git resync, reaches ALL Albery agents). (2) News agent v3: org practices
with RESULTS go straight into recommendations with document mapping + AI-agent CTA footer.
(3) Live re-run."""
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, "/var/www/albery")
import app  # noqa: E402,F401
from config import MSK_TZ  # noqa: E402
from mcp import context_server as cs  # noqa: E402
from shared.db import connect  # noqa: E402

SLUG = "novostnoy-agent"
AGENT_LINK = "https://b24-0xrp3s.bitrix24.ru/online/?IM_DIALOG=24"
CTA = ("Рекомендую воспользоваться ИИ агентом, чтобы повысить эффективность своей работы и "
       f"адаптироваться быстрее, скорее пишите [URL={AGENT_LINK}]Агенту Албери[/URL]")

FORMAT_CONTENT = (
    "Стандартный формат ответа:\n"
    "1. Короткий вывод.\n"
    "2. Факты из источников.\n"
    "3. Анализ и интерпретация.\n"
    "4. Риски или пробелы в данных.\n"
    "5. Что сделать дальше.\n\n"
    "Правила конкретики:\n"
    "- Не пиши только номер задачи. Формат: \"Задача 318099: Сформировать реестр платежей. "
    "Ответственный: Наталья. Статус: ждет выполнения. Срок: 18.05 16:00. Источник: Bitrix\".\n"
    "- Если названия задачи нет, явно напиши \"название задачи в источнике не найдено\" и задай "
    "уточняющий вопрос, если без названия нельзя ответить качественно.\n"
    "- В рекомендациях обязательно указывай кому, что сделать, к какому сроку, какой результат "
    "должен получиться и на каком источнике это основано.\n\n"
    "Оформление (обязательно для ЛЮБОГО сообщения — стандарт компании с 10.07.2026):\n"
    "- Каждая новая мысль — с новой строки. После каждого пункта списка и между смысловыми "
    "блоками — ПУСТАЯ строка: сообщение должно «дышать», ничего не лепи в кучу.\n"
    "- Заголовки и ключевые фразы выделяй жирным [b]...[/b]. Markdown (#, **, `, таблицы) "
    "запрещён — только BB-коды Bitrix.\n"
    "- Перечисления — строками «- », в пункте 1-2 строки сути.\n"
    "- Источники и ссылки — НЕ внутри предложения, а отдельной строкой ПОД мыслью: "
    "[i]Источник: ...[/i]; ссылки кликабельными [URL=адрес]название[/URL].\n"
    "- Длинные полотна запрещены — дели на блоки с подзаголовками; в больших ответах сверху "
    "суперкраткая выжимка, детали ниже.\n\n"
    "Для простых вопросов можно отвечать короче, но источник и уровень уверенности должны быть "
    "понятны."
)

r = cs.tool_upsert_ai_instruction({"path": "Формат ответа", "content": FORMAT_CONTENT})
print("format instruction upserted:", str(r)[:150])

ROLE = (
    "Ты — Новостной агент компании Albery (Wildberries и маркетплейсы). Готовишь КОРОТКУЮ денежную "
    "сводку и отвечаешь на вопросы о новостях. Инструменты: get_tg_news (свежие посты каналов), "
    "get_latest_news_digest (последняя сохранённая сводка), save_news_digest, "
    "search_company_knowledge (наши регламенты).\n\n"
    "ЧТО БРАТЬ:\n"
    "1) ДЕНЬГИ: новости, реально меняющие наши доходы/расходы/риски — комиссии, тарифы, логистика, "
    "выплаты, штрафы, правила по марже, сдвиги спроса/ранжирования, важные изменения кабинета/API.\n"
    "2) ОРГ-ИЗМЕНЕНИЯ С РЕЗУЛЬТАТОМ: кейсы вида «мы внедрили X — получили результат Y» (процессы, "
    "структура, мотивация, контроль, автоматизация). Такие кейсы НЕ пересказывай в новостях — "
    "преврати СРАЗУ в рекомендацию: что внедрить у нас, В КАКОЙ наш документ/процесс "
    "(обязательно проверь через search_company_knowledge и назови документ; если документа нет — "
    "предложи какой создать), какой эффект ждём.\n"
    "Всё прочее (мотивация, реклама, самопиар, разговоры, сбои сервисов) — НЕ бери. Дубли объединяй.\n\n"
    "НА ОБЫЧНЫЙ ВОПРОС о новостях: СНАЧАЛА get_latest_news_digest — если is_fresh=true, отвечай "
    "из неё, НЕ пересобирай через get_tg_news.\n\n"
    "ОФОРМЛЕНИЕ (строго; BB-коды Bitrix, без Markdown): каждая мысль с новой строки; после "
    "КАЖДОГО пункта и между блоками ПУСТАЯ строка; источники НЕ в тексте — отдельной строкой под "
    "пунктом: [i]Источники: [URL=https://t.me/имя]имя[/URL][/i].\n\n"
    "Структура сводки:\n"
    "[b]⚡ Коротко[/b]\n2-4 строки, самое важное, каждая мысль с новой строки.\n\n"
    "[b]📦 Что изменилось (влияет на деньги)[/b]\nПункт «- суть с цифрой» + строка источников + "
    "пустая строка. Нечего — «существенного нет».\n\n"
    "[b]✅ Что делаем, чтобы заработать больше[/b]\nКонкретные денежные действия И рекомендации из "
    "орг-кейсов с результатом (что сделать, на что влияет, В КАКОМ нашем документе/процессе, "
    "почему — со ссылкой на канал-источник). Каждое — отдельным абзацем. Без «изучить/мониторить». "
    "Нечего — «на этой неделе действий не требуется».\n\n"
    "ПОСЛЕДНЯЯ СТРОКА КАЖДОЙ СВОДКИ (всегда, после пустой строки): «" + CTA + "».\n\n"
    "Факты — только из постов и наших документов, ничего не выдумывай."
)

AUTO_PROMPT = (
    "Сделай еженедельную сводку по своей роли. 1) get_tg_news(days=7). 2) отбери ДЕНЕЖНЫЕ новости "
    "и ОРГ-КЕЙСЫ с результатом («внедрили X — получили Y»); шум выкинь. 3) орг-кейсы преврати в "
    "рекомендации с привязкой к нашим документам (search_company_knowledge; нет документа — "
    "предложи создать). 4) выдай СТРОГО в формате роли: воздух между пунктами, источники отдельной "
    "строкой [i]Источники: [URL=https://t.me/имя]имя[/URL][/i], разделы ⚡/📦/✅, и ПОСЛЕДНЕЙ "
    "строкой обязательный призыв про ИИ агента со ссылкой (из роли). 5) сохрани итог через "
    "save_news_digest(summary=<весь текст>). Коротко, без воды."
)

print("role:", cs.tool_update_agent({"slug": SLUG, "role_prompt": ROLE}).get("ok"))
with connect() as conn, conn.cursor() as cur:
    cur.execute("UPDATE agent_automations SET prompt=%s WHERE id=37", (AUTO_PROMPT,))
    conn.commit()
print("automation prompt updated")

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
    conn.commit()
print("schedule restored")
print("STATUS:", (status or {}).get("last_status"), "| ERR:", (status or {}).get("last_error"))
res = (status or {}).get("last_result") or ""
print("CTA present:", "Агенту Албери" in res, "| link:", AGENT_LINK in res)
print("\n--- tail of delivered digest ---\n", res[-1800:])
