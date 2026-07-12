# -*- coding: utf-8 -*-
"""Leadgen-мониторинг ПРОЕКТОВ для Александра — внедрение ИИ/автоматизаций в бизнес.

Обходит публичные источники заказов (не вакансий): FL.ru (RSS/HTML),
freelance.ru, публичные Telegram-каналы (через t.me/s/ превью).
Kwork выключен до появления аккаунта продавца; Workspace выключен —
анти-бот с капчей (даже через reader), включим через email-дайджесты
после регистрации профиля подрядчика. Habr Freelance закрылся (410 Gone).

Новые заказы → дедуп по журналу → префильтр по ключам → LLM (Groq) решает
релевантность и пишет черновик отклика → кандидаты владельцу в Telegram.
Автооткликов НЕТ (v1 = review): владелец откликается руками по черновику.

Запуск: leadgen_watch.py [--dry-run] [--list] [--source NAME] [--max N]
  --dry-run  полный цикл с LLM, печать в stdout, без TG и без записи журнала
  --list     быстрый список новых прошедших префильтр (без LLM и журнала)

Файлы состояния (только на сервере):
  /root/.hermes/state/leadgen_config.json    — настройки
  /root/.hermes/state/leadgen_seen.json      — журнал (никаких повторов)
  /root/.hermes/state/leadgen_feedback.json  — фидбек владельца для LLM
"""
from __future__ import annotations

import argparse
import gzip
import html as htmllib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

STATE_DIR = os.environ.get("LEADGEN_STATE_DIR", "/root/.hermes/state")
CONFIG_PATH = STATE_DIR + "/leadgen_config.json"
SEEN_PATH = STATE_DIR + "/leadgen_seen.json"
FEEDBACK_PATH = STATE_DIR + "/leadgen_feedback.json"
ENV_PATH = "/root/.hermes/secure/hermes-gateway.env"
TG_ENV_PATH = "/root/.hermes/.env"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

DEFAULT_CONFIG = {
    "paused": False,
    "max_candidates_per_run": 8,   # сколько кандидатов слать в TG за прогон
    "max_llm_per_run": 20,         # защита лимитов Groq; лишнее ждёт след. прогона
    "llm_min_interval_sec": 6,
    "llm_model": "openai/gpt-oss-120b",
    "active_hours_msk": [8, 23],   # вне окна кандидаты копятся (pending), не шлются
    "sources": {
        "flru": {"enabled": True,
                 "rss": "https://www.fl.ru/rss/all.xml",
                 "html": "https://www.fl.ru/projects/"},
        "frl": {"enabled": True, "url": "https://freelance.ru/projects/"},
        # workspace.ru: анти-бот с капчей (проверено 2026-07-12, в т.ч. через
        # r.jina.ai) — включим через email-дайджесты после регистрации (Фаза 2)
        "workspace": {"enabled": False, "pages": 2,
                      "url": "https://workspace.ru/tenders/"},
        # биржа проектов Kwork видна только залогиненному продавцу
        "kwork": {"enabled": False,
                  "note": "включить после регистрации аккаунта владельца"},
        "telegram": {"enabled": True,
                     # публичные каналы с заказами/вакансиями; имя без @,
                     # превью https://t.me/s/<имя> проверено 2026-07-12
                     "channels": ["normrabota", "freelancetaverna",
                                  "freelance_zakaz", "vdhl_good",
                                  "zapwork", "workasap"]},
    },
    # префильтр: хотя бы одно вхождение include и ни одного exclude (по названию+тексту)
    "include_re": (r"(?:\bии\b|\bai\b|нейросет|искусствен\w+\s+интеллект|"
                   r"chat\W?gpt|\bgpt[-\s\d]|\bllm\b|langchain|openai|deepseek|"
                   r"чат[-\s]?бот|телеграм[-\s]?бот|telegram[-\s]?бот|\bбот(?:а|ов|ы)?\b|"
                   r"ассистент|автоматизаци|автоматизир|"
                   r"n8n|make\.com|zapier|no[-\s]?code|"
                   r"амосрм|amocrm|битрикс|bitrix|\bcrm\b|интеграци|"
                   r"голосов\w+\s+(?:бот|робот|помощник|ассистент)|"
                   r"распознаван|транскриб|парсинг|парсер)"),
    "exclude_re": (r"(?:курсов(?:ая|ой|ую)|дипломн|лабораторн|реферат|"
                   r"контрольн(?:ая|ую)\s+работ|казино|букмекер|ставк\w+\s+на\s+спорт|"
                   r"порно|adult|даркнет|накрутк)"),
    "profile": (
        "Александр внедряет ИИ и автоматизации в бизнес: ИИ-агенты и ассистенты "
        "на LLM, чат-боты, интеграции с CRM/ERP и внутренними системами, "
        "no-code/low-code связки, автоматизация процессов и отчётности. Реальные "
        "кейсы: бухгалтерия, склад, закупки, видео-процессы, мульти-агентная "
        "система в Битрикс24 (боты, задачи, документы, зум-саммари). "
        "Бизнес-аналитик по бэкграунду: разбирает процесс, собирает требования "
        "у заказчика, внедряет и доводит до результата. Сильная сторона — связка "
        "бизнеса и ИИ-инструментов, а не глубокая разработка (не ML-инженер)."),
}

_LAST_LLM_CALL = [0.0]


# ── мелочи ───────────────────────────────────────────────────────────────
def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def jload(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def jsave(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def env_value(path, pattern):
    try:
        for line in open(path, encoding="utf-8"):
            m = re.match(pattern, line.strip())
            if m:
                return m.group(1).strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def msk_hour():
    return (time.gmtime().tm_hour + 3) % 24


def tg_send(text):
    tok = env_value(TG_ENV_PATH, r"(?:export\s+)?TELEGRAM[A-Z_]*TOKEN\s*=\s*(.+)")
    chat = None
    try:
        import yaml
        cfg = yaml.safe_load(open("/root/.hermes/config.yaml"))
        chat = str(cfg["telegram"]["allowed_chats"])
    except Exception:
        pass
    if not (tok and chat):
        log("tg_send: no token/chat")
        return
    # телеграм режет на 4096; шлём кусками по границе кандидатов
    for chunk in _split_chunks(text, 3900):
        try:
            data = urllib.parse.urlencode(
                {"chat_id": chat, "text": chunk,
                 "disable_web_page_preview": "true"}).encode()
            urllib.request.urlopen(
                f"https://api.telegram.org/bot{tok}/sendMessage",
                data=data, timeout=20)
            time.sleep(1)
        except Exception as e:
            log("tg_send failed:", e)


def _split_chunks(text, limit):
    if len(text) <= limit:
        return [text]
    out, cur = [], ""
    for block in text.split("\n\n"):
        if cur and len(cur) + len(block) + 2 > limit:
            out.append(cur)
            cur = block
        else:
            cur = cur + "\n\n" + block if cur else block
    if cur:
        out.append(cur)
    return out


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", r.headers.get("Content-Type", ""))
        if m:
            charset = m.group(1)
        try:
            return raw.decode(charset, "replace")
        except LookupError:
            return raw.decode("utf-8", "replace")


def strip_tags(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return htmllib.unescape(re.sub(r"[ \t]+", " ", s)).strip()


# ── источники: каждый возвращает [{id, title, url, budget, desc, source}] ──
def fetch_flru(src):
    items = []
    try:
        xml = fetch(src["rss"])
        for m in re.finditer(r"<item>(.*?)</item>", xml, re.S):
            block = m.group(1)
            t = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
            l = re.search(r"<link>(.*?)</link>", block, re.S)
            d = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>",
                          block, re.S)
            if not (t and l):
                continue
            url = htmllib.unescape(l.group(1).strip())
            pid = re.search(r"/projects/(\d+)", url)
            if not pid:
                continue
            title = strip_tags(t.group(1))
            budget = ""
            mb = re.search(r"[Бб]юджет:?\s*([^)<\n]+)", title + " " +
                           (d.group(1) if d else ""))
            if mb:
                budget = strip_tags(mb.group(1))[:60]
            items.append({"id": "fl:" + pid.group(1), "title": title, "url": url,
                          "budget": budget,
                          "desc": strip_tags(d.group(1))[:2500] if d else "",
                          "source": "FL.ru"})
    except Exception as e:
        log("flru rss fail:", e)
    if items:
        return items
    # fallback: HTML-листинг
    page = fetch(src["html"])
    seen_ids = set()
    for m in re.finditer(
            r'href="(?:https://www\.fl\.ru)?(/projects/(\d+)/[^"]*)"[^>]*>(.*?)</a>',
            page, re.S):
        pid = m.group(2)
        title = strip_tags(m.group(3))
        if pid in seen_ids or len(title) < 8:
            continue
        seen_ids.add(pid)
        items.append({"id": "fl:" + pid, "title": title,
                      "url": "https://www.fl.ru" + m.group(1),
                      "budget": "", "desc": "", "source": "FL.ru"})
    return items


def fetch_frl(src):
    html = fetch(src["url"])
    items = []
    # карточки: <article class="task-card"> … title-link /task/view/NNNN … desc … budget
    for m in re.finditer(r'<article class="task-card">(.*?)</article>', html, re.S):
        block = m.group(1)
        mt = re.search(
            r'class="task-card__title-link"\s+href="/task/view/(\d+)"[^>]*>(.*?)</a>',
            block, re.S)
        if not mt:
            continue
        tid, title = mt.group(1), strip_tags(mt.group(2))
        md = re.search(r'class="task-card__desc"[^>]*>(.*?)</p>', block, re.S)
        mb = re.search(r'class="task-card__budget"[^>]*>(.*?)</div>', block, re.S)
        items.append({"id": "frl:" + tid, "title": title,
                      "url": "https://freelance.ru/task/view/" + tid,
                      "budget": strip_tags(mb.group(1))[:60] if mb else "",
                      "desc": strip_tags(md.group(1))[:2500] if md else "",
                      "source": "freelance.ru"})
    return items


def fetch_workspace(src):
    items = []
    for page in range(1, src.get("pages", 2) + 1):
        url = src["url"] + (f"?page={page}" if page > 1 else "")
        html = fetch(url)
        for m in re.finditer(
                r'href="(?:https://workspace\.ru)?(/tenders/([a-z0-9\-]+?-(\d+))/)"'
                r'[^>]*>(.*?)</a>', html, re.S):
            tid = m.group(3)
            title = strip_tags(m.group(4))
            if len(title) < 8:
                continue
            items.append({"id": "ws:" + tid, "title": title,
                          "url": "https://workspace.ru" + m.group(1),
                          "budget": "", "desc": "", "source": "Workspace"})
        time.sleep(1)
    uniq = {}
    for it in items:
        uniq.setdefault(it["id"], it)
    return list(uniq.values())


def fetch_telegram(src):
    items = []
    for ch in src.get("channels", []):
        try:
            html = fetch(f"https://t.me/s/{ch}")
        except Exception as e:
            log(f"tg {ch} fail:", e)
            continue
        if 'tgme_widget_message_wrap' not in html:
            log(f"tg {ch}: нет превью (канал закрыт/не существует)")
            continue
        for m in re.finditer(
                r'data-post="([\w/]+/(\d+))"(.*?)(?=data-post="|\Z)', html, re.S):
            post, mid, block = m.group(1), m.group(2), m.group(3)
            mt = re.search(
                r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', block, re.S)
            if not mt:
                continue
            text = strip_tags(mt.group(1))
            if len(text) < 40:
                continue
            title = text[:120].split("\n")[0]
            items.append({"id": f"tg:{ch}:{mid}", "title": title,
                          "url": f"https://t.me/{post}",
                          "budget": "", "desc": text[:2500],
                          "source": f"TG @{ch}"})
        time.sleep(1)
    return items


FETCHERS = {"flru": fetch_flru, "frl": fetch_frl,
            "workspace": fetch_workspace, "telegram": fetch_telegram}


# ── LLM-оценка ───────────────────────────────────────────────────────────
def llm_assess(cfg, item):
    key = (env_value(ENV_PATH, r"(?:export\s+)?GROQ_API_KEY\s*=\s*(.+)")
           or os.environ.get("GROQ_API_KEY"))
    if not key:
        raise RuntimeError("нет GROQ_API_KEY")
    gap = cfg.get("llm_min_interval_sec", 6) - (time.time() - _LAST_LLM_CALL[0])
    if gap > 0:
        time.sleep(gap)
    system = (
        "Ты помогаешь Александру отбирать ЗАКАЗЫ (проекты) на фриланс-биржах и в "
        "Telegram-каналах. Его профиль: " + cfg["profile"] +
        "\n\nПРАВИЛА ОТБОРА (relevant=true ТОЛЬКО если выполнены ВСЕ):\n"
        "1. Проект про внедрение ИИ/автоматизацию в бизнес: ИИ-агенты, LLM-ассистенты, "
        "чат-боты, интеграции нейросетей с CRM/системами, n8n/Make/Zapier, "
        "автоматизация процессов и отчётности, парсинг+автоматизация. Если ИИ/"
        "автоматизации в сути задачи нет — relevant=false.\n"
        "2. ОТКЛОНЯЙ: чистую ML/DS-разработку и обучение моделей, чистую разработку "
        "ПО/сайтов без ИИ, дизайн, контент/копирайтинг/SMM, учебные работы, "
        "казино/беттинг/накрутки/серые схемы.\n"
        "3. Если это пост из Telegram-канала — он должен быть ЗАКАЗОМ или вакансией "
        "под профиль, а не новостью, рекламой курса или резюме исполнителя.\n"
        "4. Явный бюджет меньше 3000 ₽ за разовую мелочь — relevant=false; "
        "если бюджет не указан или договорной — это НЕ причина отклонять.\n\n"
        "Верни строго JSON: {\"relevant\": true|false, \"reason\": \"кратко почему\", "
        "\"reply\": \"черновик отклика\"}.\n")
    fb = jload(FEEDBACK_PATH, {"bad": [], "good": []})
    if fb.get("bad") or fb.get("good"):
        system += ("\nФИДБЕК ВЛАДЕЛЬЦА — реальные решения по прошлым проектам, "
                   "они ВАЖНЕЕ общих правил, обобщай их на похожие случаи:\n")
        for x in fb.get("bad", [])[-20:]:
            system += f"- НЕ подходит: {x}\n"
        for x in fb.get("good", [])[-20:]:
            system += f"- Подходит: {x}\n"
    system += (
        "Черновик отклика: 2-5 коротких живых предложений по-русски, начни с "
        "«Здравствуйте!». Пиши как нормальный человек, без канцелярита и штампов "
        "(запрещено: «идеально подхожу», «рад возможности», «уникальный опыт», "
        "длинные тире). Зацепись за конкретную деталь задачи, коротко свяжи с "
        "реальным опытом Александра, задай ОДИН уточняющий вопрос по делу. "
        "Без подписи и контактов. Если relevant=false — reply пустой.")
    user = (f"Источник: {item['source']}\nЗаголовок: {item['title']}\n"
            f"Бюджет: {item.get('budget') or 'не указан'}\n\n"
            f"Описание:\n{(item.get('desc') or item['title'])[:3000]}")
    payload = {
        "model": cfg.get("llm_model", "openai/gpt-oss-120b"),
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.4,
        "max_tokens": 700,
        "reasoning_effort": "low",
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 # edge Groq режет дефолтный "Python-urllib" → 403
                 "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) hermes-leadgen/1.0"})
    out = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                wait = 35 * (attempt + 1)
                log(f"Groq 429, ждём {wait}с")
                time.sleep(wait)
                continue
            raise
        finally:
            _LAST_LLM_CALL[0] = time.time()
    data = json.loads(out["choices"][0]["message"]["content"])
    reply = (data.get("reply") or "").strip()
    reply = reply.replace("—", "-").replace("–", "-")
    return bool(data.get("relevant")), data.get("reason", ""), reply


# ── основной цикл ────────────────────────────────────────────────────────
def collect(cfg, only_source=None):
    all_items, statuses = [], {}
    for name, src in cfg["sources"].items():
        if only_source and name != only_source:
            continue
        if not src.get("enabled"):
            statuses[name] = "выключен"
            continue
        fetcher = FETCHERS.get(name)
        if not fetcher:
            statuses[name] = "нет фетчера"
            continue
        try:
            got = fetcher(src)
            statuses[name] = f"{len(got)} шт."
            all_items.extend(got)
        except Exception as e:
            statuses[name] = f"ОШИБКА: {e}"
            log(f"{name} fail:", e)
    return all_items, statuses


def prefilter(cfg, items, seen):
    inc = re.compile(cfg["include_re"], re.I | re.U)
    exc = re.compile(cfg["exclude_re"], re.I | re.U)
    fresh, cut = [], []
    for it in items:
        if it["id"] in seen:
            continue
        text = it["title"] + " " + (it.get("desc") or "")
        if exc.search(text) or not inc.search(text):
            cut.append(it)
        else:
            fresh.append(it)
    return fresh, cut


def fmt_candidate(n, it, reason, reply):
    parts = [f"{n}. [{it['source']}] {it['title']}"]
    if it.get("budget"):
        parts.append(f"   💰 {it['budget']}")
    parts.append(f"   почему: {reason}")
    parts.append(f"   id {it['id']}")
    parts.append(f"   {it['url']}")
    if reply:
        parts.append(f"   ✍️ {reply}")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--source", default=None)
    ap.add_argument("--max", type=int, default=None)
    args = ap.parse_args()

    cfg = {**DEFAULT_CONFIG, **jload(CONFIG_PATH, {})}
    if not os.path.exists(CONFIG_PATH) and not args.dry_run and not args.list:
        jsave(CONFIG_PATH, DEFAULT_CONFIG)
        log("создан конфиг по умолчанию:", CONFIG_PATH)
    if cfg.get("paused") and not (args.dry_run or args.list):
        log("paused=true — выходим")
        return

    seen = jload(SEEN_PATH, {})
    items, statuses = collect(cfg, args.source)
    log("источники:", json.dumps(statuses, ensure_ascii=False))
    fresh, cut = prefilter(cfg, items, seen)
    log(f"новых после префильтра: {len(fresh)} (срезано {len(cut)}, всего {len(items)})")

    if args.list:
        for i, it in enumerate(fresh, 1):
            b = f" | {it['budget']}" if it.get("budget") else ""
            print(f"{i}. [{it['source']}] {it['title']}{b}\n   {it['url']}")
        return

    now = int(time.time())
    # префильтрованный мусор помечаем сразу, чтобы не гонять по нему регэкспы вечно
    if not args.dry_run:
        for it in cut:
            seen[it["id"]] = {"t": now, "st": "pre"}

    # ночью найденное копим как pending; утром первый прогон доставит
    in_hours = cfg["active_hours_msk"][0] <= msk_hour() < cfg["active_hours_msk"][1]

    max_llm = args.max or cfg.get("max_llm_per_run", 20)
    max_out = cfg.get("max_candidates_per_run", 8)
    candidates = []

    # сперва поднимаем ночные pending (LLM по ним уже прошёл)
    if in_hours:
        for pid, rec in list(seen.items()):
            if rec.get("st") == "pending" and rec.get("cand"):
                candidates.append(rec["cand"])
                rec["st"] = "proposed"
                rec.pop("cand", None)

    llm_done = 0
    for it in fresh:
        if llm_done >= max_llm or len(candidates) >= max_out * 2:
            break  # остальное не трогаем — дойдёт в следующем прогоне
        try:
            ok, reason, reply = llm_assess(cfg, it)
        except Exception as e:
            log("llm fail:", e)
            break
        llm_done += 1
        if not ok:
            log(f"skip [{it['source']}] {it['title'][:60]} — {reason}")
            if not args.dry_run:
                seen[it["id"]] = {"t": now, "st": "skipped"}
            continue
        cand = {**it, "reason": reason, "reply": reply}
        if args.dry_run:
            candidates.append(cand)
        elif in_hours:
            candidates.append(cand)
            seen[it["id"]] = {"t": now, "st": "proposed"}
        else:
            seen[it["id"]] = {"t": now, "st": "pending", "cand": cand}
            log(f"ночь — pending: {it['title'][:60]}")

    if candidates:
        candidates = candidates[:max_out]
        body = "\n\n".join(
            fmt_candidate(i, c, c.get("reason", ""), c.get("reply", ""))
            for i, c in enumerate(candidates, 1))
        msg = (f"🎯 Проекты-кандидаты ({len(candidates)}):\n\n{body}\n\n"
               "Ответь «N норм» (я подскажу как откликнуться) или "
               "«N не норм, потому что …» — учту в фильтре.")
        if args.dry_run:
            print("\n" + msg)
        else:
            tg_send(msg)
            log(f"отправлено кандидатов: {len(candidates)}")
    else:
        log("кандидатов нет — молчим")

    if not args.dry_run:
        jsave(SEEN_PATH, seen)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # алерт наружу (stdout обёртки → TG только при ненулевом выходе)
        print(f"🔴 leadgen-watch упал: {e}", file=sys.stderr)
        raise
