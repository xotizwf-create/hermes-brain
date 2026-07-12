# -*- coding: utf-8 -*-
"""Автоотклики на hh.ru для Александра — внедрение ИИ/автоматизаций в бизнес.

Полный цикл без участия владельца (standing approval 2026-06-12):
поиск по кластерам запросов → префильтр по названию → чтение описания →
LLM (Groq) решает релевантность и пишет короткий человечный отклик →
отклик через залогиненный Chrome (CDP 9225, профиль /opt/hh-browser) →
журнал откликов (никаких повторов) → отчёт в Telegram.

Запуск:  hh_auto_apply.py [--dry-run] [--max N]
  --dry-run  всё, кроме клика «Откликнуться» (письма печатаются в stdout)

Файлы состояния (только на сервере):
  /root/.hermes/state/hh_auto_config.json  — настройки (запросы, лимиты, профиль)
  /root/.hermes/state/hh_applies.json      — журнал: applied / manual / skipped

API соискателя hh.ru отключён (2025-12-15) — всё через обычные страницы.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import websocket

CDP = "http://127.0.0.1:9225"
STATE_DIR = "/root/.hermes/state"
CONFIG_PATH = STATE_DIR + "/hh_auto_config.json"
LEDGER_PATH = STATE_DIR + "/hh_applies.json"
MSGS_SEEN_PATH = STATE_DIR + "/hh_msgs_seen.json"
FEEDBACK_PATH = STATE_DIR + "/hh_feedback.json"   # {"bad": [...], "good": [...]}
ENV_PATH = "/root/.hermes/secure/hermes-gateway.env"
HH_ENV_PATH = "/root/.hermes/.env"
FAIL_SHOTS = "/opt/hh-browser/logs"

DEFAULT_CONFIG = {
    "paused": False,
    # review = кандидаты владельцу в TG (без откликов), apply = автоотклики
    "mode": "review",
    "max_proposals_per_run": 10,
    "max_applies_per_run": 8,
    "max_pages_per_query": 2,
    "attach_cover_letters": True,
    "delay_between_applies_sec": [25, 50],
    "area": 113,             # 113 = вся Россия
    "salary_from": 100000,   # фильтр hh: ЗП >= 100к ИЛИ не указана
    "active_hours_msk": [8, 23],  # отклики только в это окно (не как бот в 4 утра)
    "queries": [
        "внедрение ИИ",
        "ИИ-агенты",
        "внедрение искусственного интеллекта",
        "AI автоматизация бизнес-процессов",
        "ИИ-ассистент для бизнеса",
        "нейросети автоматизация процессов",
        "автоматизация отчетности",
        "LLM интеграция",
        "чат-бот автоматизация бизнеса",
    ],
    # стоп-слова в НАЗВАНИИ вакансии (грубый префильтр; точную оценку делает LLM)
    "title_exclude": [
        "ml ", "machine learning", "data scien", "deep learning",
        "computer vision", "nlp", "исследовател", "researcher",
        "devops", "backend", "frontend", "fullstack", "разработчик",
        "программист", "тестировщ", " qa", "юрист", "продаж", "менеджер по прод",
        "дизайнер", "рекрутер", " hr", "охран", "водител", "грузчик",
        "контент", "копирайт", "smm", "маркетолог", "таргетолог", "редактор",
        "монтажёр", "монтажер", "оператор", "видеограф",
        "бизнес-ассистент", "бизнес ассистент", "личный ассистент",
        "помощник руководител", "офис-менеджер",
    ],
    # части названий гос-компаний и бигтехов — такие работодатели пропускаются
    "employer_exclude": [
        "сбер", "яндекс", "yandex", "vk ", "вконтакте", "ozon", "озон",
        "wildberries", "вайлдберриз", "тинькофф", "т-банк", "t-bank", "втб",
        "альфа-банк", "газпром", "роснефт", "ржд", "ростех", "росатом",
        "мтс", "megafon", "мегафон", "билайн", "ростелеком", "почта россии",
        "министерств", "администрац", "госуслуг", "государствен", "фгуп",
        "гбу", "мбу", "гку", "казённое", "казенное", "департамент",
        "пфр", "фнс", "налогов", "муниципальн", "авито", "avito", "касперск",
    ],
    "profile": (
        "Александр внедряет ИИ и автоматизации в бизнес: ИИ-агенты и ассистенты "
        "на LLM, чат-боты, интеграции с CRM/ERP и внутренними системами, "
        "no-code/low-code связки, автоматизация процессов и отчётности. Реальные "
        "кейсы: бухгалтерия, склад, закупки, видео-процессы. Бизнес-аналитик по "
        "бэкграунду: разбирает процесс, собирает требования у заказчика, внедряет "
        "и доводит до результата. Сильная сторона — связка бизнеса и ИИ-инструментов, "
        "а не глубокая разработка (не ML-инженер)."),
    "resume_hint": "внедрение автоматизаций",
}


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


def tg_send(text):
    tok = env_value(HH_ENV_PATH, r"(?:export\s+)?TELEGRAM[A-Z_]*TOKEN\s*=\s*(.+)")
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
    try:
        data = urllib.parse.urlencode({"chat_id": chat, "text": text[:4000]}).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{tok}/sendMessage", data=data, timeout=20)
    except Exception as e:
        log("tg_send failed:", e)


# ── браузер / CDP ────────────────────────────────────────────────────────
def browser_alive():
    try:
        urllib.request.urlopen(CDP + "/json/version", timeout=3)
        return True
    except Exception:
        return False


def ensure_browser():
    started = False
    if not browser_alive():
        free_mb = int(subprocess.check_output(
            "free -m | awk 'NR==2{print $7}'", shell=True).strip())
        # start.sh на время сессии останавливает meshcentral — его память
        # фактически достанется браузеру, учитываем её в preflight
        mesh_mb = 0
        try:
            out = subprocess.check_output(
                ["systemctl", "show", "meshcentral", "-p", "MemoryCurrent"],
                text=True).strip().partition("=")[2]
            if out.isdigit():
                mesh_mb = int(out) // (1024 * 1024)
        except Exception:
            pass
        if free_mb + mesh_mb < 250:
            raise RuntimeError(
                f"мало памяти для браузера: {free_mb} МБ (+{mesh_mb} МБ meshcentral)")
        # HH_NOVNC=1: автоматическим прогонам VNC/noVNC не нужен (~30-40 МБ);
        # владелец логинится через ручной запуск start.sh без этой переменной
        subprocess.Popen(["bash", "/opt/hh-browser-start.sh", "https://hh.ru/"],
                         env={**os.environ, "HH_NOVNC": "1"},
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            time.sleep(2)
            if browser_alive():
                break
        else:
            raise RuntimeError("браузер не поднялся")
        started = True
        time.sleep(4)
    return started


def stop_browser():
    try:
        subprocess.run(["bash", "/opt/hh-browser-stop.sh"], timeout=30,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class Tab:
    def __init__(self, url):
        req = urllib.request.Request(
            CDP + "/json/new?" + urllib.parse.quote(url, safe=""), method="PUT")
        info = json.load(urllib.request.urlopen(req, timeout=15))
        self.id = info["id"]
        self.ws = websocket.create_connection(info["webSocketDebuggerUrl"],
                                              timeout=40)
        self._mid = 0
        self._rpc("Page.enable")   # события загрузки для умного ожидания в goto

    def _rpc(self, method, **params):
        self._mid += 1
        self.ws.send(json.dumps({"id": self._mid, "method": method,
                                 "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self._mid:
                return msg.get("result", {})

    def eval(self, expr):
        res = self._rpc("Runtime.evaluate", expression=expr,
                        returnByValue=True, awaitPromise=True)
        return res.get("result", {}).get("value")

    def goto(self, url, wait=6.0, ready_sel=None, settle=0.7):
        """Переход с умным ожиданием: событие загрузки страницы + (опционально)
        появление селектора ready_sel. wait — верхний предел, а не фиксированный
        сон: обычная страница hh готова за 1.5-3с вместо прежних 6-10с."""
        self._rpc("Page.navigate", url=url)
        deadline = time.time() + wait
        self.ws.settimeout(0.5)
        try:
            while time.time() < deadline:
                try:
                    msg = json.loads(self.ws.recv())
                except Exception:
                    continue      # квант таймаута — проверяем дедлайн и ждём дальше
                if msg.get("method") in ("Page.loadEventFired",
                                         "Page.frameStoppedLoading"):
                    break
        finally:
            self.ws.settimeout(40)
        if ready_sel:
            probe = "!!document.querySelector(" + json.dumps(ready_sel) + ")"
            while time.time() < deadline:
                try:
                    if self.eval(probe):
                        break
                except Exception:
                    pass
                time.sleep(0.3)
        time.sleep(settle)        # короткая пауза на дорисовку React-контента

    def screenshot(self, path):
        try:
            res = self._rpc("Page.captureScreenshot", format="png")
            import base64
            open(path, "wb").write(base64.b64decode(res["data"]))
        except Exception:
            pass

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
        try:
            urllib.request.urlopen(CDP + "/json/close/" + self.id, timeout=10)
        except Exception:
            pass


def check_login(tab):
    tab.goto("https://hh.ru/applicant/resumes", wait=7)
    return bool(tab.eval(
        "(function(){var f=document.querySelector('[data-qa=\"login\"],"
        "[data-qa=\"account-login-form\"]');"
        "return !f && /applicant\\/resumes/.test(location.href);})()"))


# ── поиск ────────────────────────────────────────────────────────────────
def search_vacancies(tab, cfg):
    found = {}
    for q in cfg["queries"]:
        for page in range(cfg["max_pages_per_query"]):
            url = ("https://hh.ru/search/vacancy?text=" + urllib.parse.quote(q)
                   + f"&area={cfg['area']}&salary={cfg['salary_from']}"
                   + "&order_by=publication_time"
                   + f"&page={page}&items_on_page=20")
            tab.goto(url, wait=8,
                     ready_sel='a[data-qa="serp-item__title"], a[data-qa*="vacancy-title"]')
            items = tab.eval("""
(() => [...document.querySelectorAll('a[data-qa="serp-item__title"], a[data-qa*="vacancy-title"]')]
  .map(a => {
    const card = a.closest('[data-qa="vacancy-serp__vacancy"]') || a.closest('div');
    const emp = card && card.querySelector('[data-qa="vacancy-serp__vacancy-employer"]');
    const sal = card && card.querySelector('[data-qa="vacancy-serp__vacancy-compensation"]');
    const m = a.href.match(/vacancy\\/(\\d+)/);
    return m ? {id: m[1], title: a.textContent.trim(),
                employer: emp ? emp.textContent.trim() : "",
                salary: sal ? sal.textContent.trim() : "",
                url: "https://hh.ru/vacancy/" + m[1]} : null;
  }).filter(Boolean))()
""") or []
            for it in items:
                found.setdefault(it["id"], it)
            if len(items) < 15:
                break
        time.sleep(1)
    return list(found.values())


def title_ok(title, cfg):
    t = " " + title.lower() + " "
    return not any(x in t for x in cfg["title_exclude"])


def employer_ok(employer, cfg):
    e = " " + (employer or "").lower() + " "
    return not any(x in e for x in cfg.get("employer_exclude", []))


def salary_ok(salary_text, cfg):
    """ЗП не указана / не в рублях → пропускаем дальше (решит LLM по описанию).
    Указана в рублях и максимум вилки ниже порога → отсев."""
    s = (salary_text or "").strip()
    if not s:
        return True
    if "₽" not in s and "руб" not in s.lower():
        return True
    nums = [int(re.sub(r"\D", "", n))
            for n in re.findall(r"\d[\d\s \xa0]*", s)]
    nums = [n for n in nums if n >= 10000]
    if not nums:
        return True
    return max(nums) >= cfg.get("salary_from", 100000)


def read_vacancy(tab, url):
    tab.goto(url, wait=8, ready_sel='[data-qa="vacancy-title"]')
    return tab.eval("""
(() => ({
  title: (document.querySelector('[data-qa="vacancy-title"]')||{textContent:""}).textContent.trim(),
  employer: (document.querySelector('[data-qa="vacancy-company-name"]')||{textContent:""}).textContent.trim(),
  salary: (document.querySelector('[data-qa="vacancy-salary"]')||{textContent:""}).textContent.trim(),
  desc: (document.querySelector('[data-qa="vacancy-description"]')||{innerText:""}).innerText.slice(0, 5000),
  canApply: !!document.querySelector('[data-qa="vacancy-response-link-top"]'),
  alreadyApplied: !!document.querySelector('[data-qa="vacancy-response-link-view-topic"]'),
  hasTest: /тестовое задание|опросом|вопросы работодателя/i.test(
      (document.querySelector('[data-qa="vacancy-response-link-top"]')||{textContent:""}).textContent + " " +
      ((document.querySelector('[data-qa="vacancy-response-test-required"]')||{textContent:""}).textContent || "")),
}))()
""") or {}


# ── LLM: релевантность + письмо ─────────────────────────────────────────
_LAST_LLM_CALL = [0.0]


def llm_assess(cfg, vac):
    key = env_value(ENV_PATH, r"(?:export\s+)?GROQ_API_KEY\s*=\s*(.+)")
    if not key:
        raise RuntimeError("нет GROQ_API_KEY")
    # лимиты Groq — токены/минуту: короткая пауза между вызовами; при 429
    # ниже есть retry с backoff, поэтому большой превентивный gap не нужен
    gap = cfg.get("llm_min_interval_sec", 6) - (time.time() - _LAST_LLM_CALL[0])
    if gap > 0:
        time.sleep(gap)
    system = (
        "Ты помогаешь Александру откликаться на вакансии на hh.ru. Его профиль: "
        + cfg["profile"]
        + "\n\nПРАВИЛА ОТБОРА (relevant=true ТОЛЬКО если выполнены ВСЕ):\n"
        "1. ИИ ОБЯЗАТЕЛЕН В СУТИ РОЛИ: вакансия про внедрение ИИ-агентов, "
        "LLM-ассистентов, чат-ботов, нейросетей в бизнес-процессы, ИИ-автоматизацию "
        "процессов и отчётности. Если в описании нет явного ИИ-компонента (чистый "
        "Битрикс24/1С/BI/ERP/системный анализ без ИИ) — relevant=false. Суть работы — "
        "внедрить ИИ в деятельность компании, а не разработать модель.\n"
        "1а. Если в тексте явно указана зарплата и её максимум ниже 100 000 ₽ в месяц "
        "— relevant=false. Если зарплата НЕ указана — это НЕ причина отклонять.\n"
        "1б. Требуемый опыт 5+ лет, уровень Senior/Ведущий с жёсткими требованиями "
        "к стажу — relevant=false (у Александра нет формального стажа такого уровня).\n"
        "1в. Если суть роли — отраслевой менеджмент (управление недвижимостью, "
        "клиникой, объектом, командой курьеров и т.п.), а ИИ лишь упомянут как "
        "инструмент или модное слово — relevant=false.\n"
        "2. Работодатель — ЧАСТНАЯ компания. ОТКЛОНЯЙ государственные/бюджетные "
        "организации, госкорпорации и крупные бигтехи (Сбер, Яндекс, VK, Ozon, "
        "Wildberries, Avito, Тинькофф, МТС, Газпром, банки-гиганты, министерства, "
        "ГБУ/ФГУП и т.п.).\n"
        "3. ОТКЛОНЯЙ: ML/Data Science-разработку и исследования, чистую разработку "
        "ПО (backend/frontend/программист), продажи, маркетинг, дизайн, поддержку, "
        "а также «контент-завод» — роли, где суть в потоковом производстве контента "
        "(контент-менеджер, SMM, копирайтинг, монтаж видео на конвейере). Если ИИ/"
        "автоматизация в вакансии — лишь модное слово, а суть в контенте/продажах — "
        "relevant=false.\n"
        "4. Подходит по уровню: не требуется профильное IT-высшее или глубокий "
        "Computer Science; ценится практический опыт внедрений.\n\n"
        "Верни строго JSON: {\"relevant\": true|false, \"reason\": \"кратко почему\", "
        "\"letter\": \"текст отклика\"}.\n"
    )
    fb = jload(FEEDBACK_PATH, {"bad": [], "good": []})
    if fb.get("bad") or fb.get("good"):
        system += ("\nФИДБЕК ВЛАДЕЛЬЦА — реальные решения по прошлым вакансиям, "
                   "они ВАЖНЕЕ общих правил, обобщай их на похожие случаи:\n")
        for x in fb.get("bad", [])[-20:]:
            system += f"- НЕ подходит: {x}\n"
        for x in fb.get("good", [])[-20:]:
            system += f"- Подходит: {x}\n"
    system += (
        "Письмо: 2-4 коротких живых предложения по-русски, начни с «Здравствуйте!». "
        "Пиши как нормальный человек, простыми словами, без канцелярита и штампов "
        "(запрещено: «идеально подхожу», «рад возможности», «уникальный опыт», "
        "«не упущу шанс», длинные тире). Зацепись за одну конкретную деталь из "
        "описания. Коротко свяжи с его реальным опытом (бухгалтерия/склад/закупки/"
        "видео/внедрение). Без подписи и контактов. Если relevant=false — letter пустая."
    )
    user = (f"Вакансия: {vac['title']}\nКомпания: {vac['employer']}\n"
            f"Зарплата: {vac.get('salary','')}\n\nОписание:\n{vac['desc'][:3500]}")
    payload = {
        # gpt-oss-120b: отдельный от моделей гейтвея бакет лимитов Groq
        "model": cfg.get("llm_model", "openai/gpt-oss-120b"),
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.4,
        "max_tokens": 900,
        "reasoning_effort": "low",
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 # edge Groq режет дефолтный "Python-urllib" → 403; нужен обычный UA
                 "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) hermes-hh/1.0"})
    out = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:   # rate limit → подождать и повторить
                wait = 35 * (attempt + 1)
                log(f"Groq 429, ждём {wait}с")
                time.sleep(wait)
                continue
            raise
        finally:
            _LAST_LLM_CALL[0] = time.time()
    data = json.loads(out["choices"][0]["message"]["content"])
    letter = (data.get("letter") or "").strip()
    # страховка от ИИ-маркеров
    letter = letter.replace("—", "-").replace("–", "-")
    return bool(data.get("relevant")), data.get("reason", ""), letter


# ── отклик ───────────────────────────────────────────────────────────────
APPLY_JS = r"""
async (letterText) => {
  const $ = s => document.querySelector(s);
  const vis = e => e && e.offsetParent !== null;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const applied = () => !!$('[data-qa="vacancy-response-link-view-topic"]')
                     || /вы откликнулись/i.test(document.body.innerText);
  const setVal = (el, v) => {
    const s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
    s.call(el, v); el.dispatchEvent(new Event("input", {bubbles: true}));
  };
  const clickText = re => {
    const e = [...document.querySelectorAll("button, a")].find(b => vis(b) && re.test(b.textContent.trim()));
    if (e) { e.click(); return true; } return false;
  };
  const findLetter = () => $('[data-qa="vacancy-response-popup-form-letter-input"]')
        || $('textarea[data-qa*="letter"]') || $('textarea[name="letter"]')
        || [...document.querySelectorAll("textarea")].find(vis);

  if (applied()) return {ok: true, stage: "already"};
  const btn = $('[data-qa="vacancy-response-link-top"]');
  if (!btn) return {ok: false, stage: "no-button"};
  btn.click();
  await sleep(2800);

  // 1) предупреждение о городе → «Все равно откликнуться»
  if ($('[data-qa="relocation-warning-confirm"]')) {
    $('[data-qa="relocation-warning-confirm"]').click();
    await sleep(2800);
  }
  // 2) опрос/тест работодателя → отдаём на ручной отклик
  if ($('[data-qa="task-body"]') || $('[data-qa="vacancy-response-popup-question-list"]')
      || /ответьте на вопрос|пройдите тест/i.test((($('[role="dialog"]')||{}).innerText||"")))
    return {ok: false, stage: "questionnaire"};

  // 3) попап с письмом (если показался) → заполнить и отправить
  let ta = findLetter();
  if (ta && letterText && vis(ta)) {
    // раскрыть поле письма, если свёрнуто
    if (!ta.value && /добавить сопроводительное/i.test(document.body.innerText))
      clickText(/добавить сопроводительное/i), await sleep(800), ta = findLetter();
    setVal(ta, letterText); await sleep(700);
    const sub = $('[data-qa="vacancy-response-submit-popup"]')
             || $('[data-qa="vacancy-response-popup-submit-button"]')
             || [...document.querySelectorAll('button')].find(b => vis(b) && /^отправить/i.test(b.textContent.trim()));
    if (sub) { sub.click(); await sleep(3200); }
  }

  // 4) закрыть посторонние апселл-модалки (гео и т.п.)
  for (let i = 0; i < 2; i++) {
    clickText(/^(сохранить и продолжить|не сейчас|закрыть|пропустить|позже)$/i);
    const x = $('[data-qa="bloko-modal-close"], [data-qa="magritte-modal-close"]');
    if (x && vis(x)) x.click();
    await sleep(1200);
  }

  // 5) если откликнулись напрямую без письма — дослать письмо через «Сопроводительное»
  let stage = applied() ? "direct" : "post-click";
  let letterDone = !!(ta && letterText);
  if (applied() && letterText && !letterDone) {
    if (clickText(/сопроводительное письмо/i)) {
      await sleep(1500);
      const ta2 = findLetter();
      if (ta2 && vis(ta2)) {
        setVal(ta2, letterText); await sleep(600);
        if (clickText(/^(отправить|сохранить)/i)) { letterDone = true; await sleep(2000); }
      }
    }
  }
  return {ok: applied(), stage: stage, letter: letterDone};
}
"""


def apply_to(tab, vac_url, letter):
    tab.goto(vac_url, wait=8, ready_sel='[data-qa="vacancy-title"]', settle=1.2)
    expr = "(" + APPLY_JS + ")(" + json.dumps(letter, ensure_ascii=False) + ")"
    return tab.eval(expr) or {"ok": False, "stage": "eval-null"}


# ── ЛС: новые сообщения от работодателей (список чатов hh.ru/chat) ──────
# Каждая ячейка чата: data-qa="chatik-open-chat-<id>", innerText построчно:
# [0] вакансия, [1] время, [2] компания, [3+] превью последнего сообщения.
CHATS_JS = r"""
(() => [...document.querySelectorAll('[data-qa^="chatik-open-chat-"]')].map(c => {
  const m = (c.getAttribute('data-qa') || '').match(/(\d+)$/);
  const lines = (c.innerText || '').split('\n').map(s => s.trim()).filter(Boolean);
  return m ? {id: m[1], lines: lines.slice(0, 8)} : null;
}).filter(Boolean))()
"""


def check_messages(tab):
    """Сканирует список чатов; возвращает новые входящие, об отказах молчит."""
    seen = jload(MSGS_SEEN_PATH, {})
    first_seed = not seen
    tab.goto("https://hh.ru/chat", wait=10,
             ready_sel='[data-qa^="chatik-open-chat-"]', settle=1.0)
    rows = tab.eval(CHATS_JS) or []
    log(f"ЛС: чатов в списке: {len(rows)}")
    news = []
    for r in rows:
        lines = r.get("lines") or []
        digest = " | ".join(lines)[:300]
        if seen.get(r["id"]) == digest:
            continue
        seen[r["id"]] = digest
        if first_seed:
            continue          # первый запуск — только запоминаем, без спама
        if "отказ" in digest.lower():
            continue          # отказы — молча (правило владельца)
        preview = " ".join(lines[3:]) if len(lines) > 3 else ""
        if not preview or preview.lower().startswith("отклик на вакансию"):
            continue          # это наш собственный отклик, не входящее сообщение
        title = lines[0] if lines else "чат"
        comp = lines[2] if len(lines) > 2 else ""
        news.append({"text": f"{title} — {comp}: «{preview[:160]}»",
                     "url": "https://hh.ru/chat/" + r["id"]})
    jsave(MSGS_SEEN_PATH, seen)
    return news


# ── main ─────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=None)
    ap.add_argument("--apply-ids", default=None,
                    help="id,id из раздела proposed журнала — откликнуться на одобренные")
    ap.add_argument("--list", action="store_true",
                    help="быстрый разовый список: поиск + префильтр, без LLM и откликов")
    args = ap.parse_args()

    cfg = {**DEFAULT_CONFIG, **jload(CONFIG_PATH, {})}
    jsave(CONFIG_PATH, cfg)
    if cfg.get("paused") and not args.list:
        # пауза останавливает автоцикл, но не разовый список по просьбе владельца
        log("paused в конфиге — выходим")
        return
    ledger = jload(LEDGER_PATH, {"applied": {}, "manual": {}, "skipped": {}})
    max_applies = args.max if args.max is not None else cfg["max_applies_per_run"]

    hour_msk = (time.gmtime().tm_hour + 3) % 24
    lo, hi = cfg.get("active_hours_msk", [8, 23])
    night = not (lo <= hour_msk < hi)
    if night and not browser_alive():
        log(f"ночь ({hour_msk}:00 МСК) и браузер не поднят — спим до утра")
        return

    started = False
    tab = None
    mode = cfg.get("mode", "review")
    applied, manual, errors, letters_fyi, proposed = [], [], [], [], []

    def send_report():
        lines = []
        if applied:
            lines.append(f"✅ Откликнулся на {len(applied)} вакансий:\n"
                         + "\n".join(applied))
        if letters_fyi:
            lines.append("📩 Тут просили сопроводительное — тексты писем:\n"
                         + "\n\n".join(letters_fyi))
        # кандидаты (proposed) уже отправлены по одному прямо из цикла
        if manual:
            lines.append(f"✍️ Требуют ручного отклика (опрос/тест), {len(manual)}:\n"
                         + "\n".join(manual))
        if errors:
            lines.append("⚠️ Ошибки: " + "; ".join(errors[:5]))
        if lines:
            tg_send("hh.ru — поиск вакансий\n\n" + "\n\n".join(lines))
        else:
            log("новых релевантных вакансий/событий нет — отчёт не шлём")

    try:
        # внутри try, чтобы отказ (например, «мало памяти») ушёл алертом в TG,
        # а не умер молча в логе крона
        started = ensure_browser()
        tab = Tab("about:blank")
        if not check_login(tab):
            if not args.list:
                tg_send("⚠️ hh.ru: сессия разлогинилась. Зайди в браузер по ссылке "
                        "из `bash /opt/hh-browser-start.sh` и войди заново — "
                        "автоотклики на паузе.")
                return
            log("сессия разлогинена — для --list не критично, ищем без логина")

        # ── одобренные владельцем отклики (--apply-ids) ──────────────────
        if args.apply_ids:
            props = ledger.get("proposed", {})
            for vid in [v.strip() for v in args.apply_ids.split(",") if v.strip()]:
                p = props.get(vid)
                if not p:
                    errors.append(f"id {vid}: не найден в proposed")
                    continue
                res = apply_to(tab, p["url"], p["letter"])
                if res.get("ok"):
                    ledger["applied"][vid] = {
                        **p, "letter_attached": bool(res.get("letter")),
                        "applied_at": time.strftime("%Y-%m-%d %H:%M")}
                    props.pop(vid, None)
                    applied.append(f"• {p['title']} - {p['employer']}\n{p['url']}")
                elif res.get("stage") == "questionnaire":
                    ledger["manual"][vid] = {**p, "reason": "вакансия с опросом/тестом"}
                    props.pop(vid, None)
                    manual.append(f"• {p['title']} - {p['employer']}\n{p['url']}")
                else:
                    errors.append(f"{p['title'][:40]}: {res.get('stage')}")
                    tab.screenshot(f"{FAIL_SHOTS}/fail_{vid}.png")
                jsave(LEDGER_PATH, ledger)
                time.sleep(random.uniform(*cfg["delay_between_applies_sec"]))
            send_report()
            return

        # ── быстрый разовый список для владельца (--list): без LLM/откликов ──
        if args.list:
            cands = search_vacancies(tab, cfg)
            rows = [c for c in cands
                    if title_ok(c["title"], cfg)
                    and employer_ok(c.get("employer", ""), cfg)
                    and salary_ok(c.get("salary", ""), cfg)]
            log(f"выдача: {len(cands)}, после префильтра: {len(rows)}")
            for c in rows:
                mark = " [уже откликался]" if c["id"] in ledger["applied"] else ""
                print(f"• {c['title']} — {c.get('employer', '')} | "
                      f"{c.get('salary') or 'ЗП не указана'}{mark}\n  {c['url']}")
            return

        # ЛС проверяем каждый прогон (отказы фильтруются внутри)
        try:
            msgs = check_messages(tab)
        except Exception as e:
            msgs = []
            log("ЛС-проверка упала:", e)
        if msgs and not args.dry_run:
            tg_send("💬 hh.ru: новые сообщения в ЛС\n\n" + "\n\n".join(
                f"• {m['text'][:200]}\n{m['url']}" for m in msgs[:8]))

        # ночь блокирует только автоотклики; поиск кандидатов (review) — круглосуточно
        if night and mode != "review":
            log(f"ночь ({hour_msk}:00 МСК) — отклики не шлём, только ЛС")
            return

        cands = search_vacancies(tab, cfg)
        log(f"найдено в выдаче: {len(cands)}")
        fresh = [c for c in cands
                 if c["id"] not in ledger["applied"]
                 and c["id"] not in ledger["manual"]
                 and c["id"] not in ledger["skipped"]
                 and c["id"] not in ledger.get("proposed", {})
                 and title_ok(c["title"], cfg)
                 and employer_ok(c.get("employer", ""), cfg)]
        log(f"после журнала и префильтра: {len(fresh)}")

        consec_fail = 0
        llm_fail = 0
        seen_pairs = set()   # (название, работодатель) — клоны вакансии по городам
        for c in fresh:
            if len(applied) >= max_applies or consec_fail >= 3:
                break
            if mode == "review" and len(proposed) >= cfg.get("max_proposals_per_run", 10):
                break
            if llm_fail >= 4:
                tg_send("⚠️ hh.ru: LLM-оценка недоступна (Groq), прогон прерван.")
                log("aborting: 4 LLM failures in a row")
                break
            pair = (c["title"].strip().lower(), c.get("employer", "").strip().lower())
            if pair in seen_pairs:
                ledger["skipped"][c["id"]] = "дубль вакансии (другой город)"
                continue
            seen_pairs.add(pair)
            vac = read_vacancy(tab, c["url"])
            if not vac.get("title"):
                continue
            vac["url"] = c["url"]
            if vac.get("alreadyApplied"):
                ledger["applied"].setdefault(c["id"], {
                    "title": vac["title"], "employer": vac["employer"],
                    "url": c["url"], "applied_at": "ранее (вручную)"})
                continue
            if not vac.get("canApply"):
                ledger["skipped"][c["id"]] = "нет кнопки отклика"
                continue
            if not employer_ok(vac.get("employer", ""), cfg):
                ledger["skipped"][c["id"]] = "гос/бигтех работодатель"
                continue
            if not salary_ok(vac.get("salary", ""), cfg):
                ledger["skipped"][c["id"]] = "ЗП ниже порога: " + vac.get("salary", "")[:60]
                log("skip (зп):", vac["title"][:50], "|", vac.get("salary", "")[:40])
                continue
            try:
                relevant, reason, letter = llm_assess(cfg, vac)
                llm_fail = 0
            except Exception as e:
                llm_fail += 1
                log("LLM fail:", e)
                time.sleep(5)
                continue
            if not relevant or len(letter) < 30:
                ledger["skipped"][c["id"]] = "нерелевантно: " + reason[:100]
                log("skip:", vac["title"][:50], "|", reason[:60])
                continue

            if mode == "review":
                ledger.setdefault("proposed", {})[c["id"]] = {
                    "title": vac["title"], "employer": vac["employer"],
                    "salary": vac.get("salary", ""), "url": c["url"],
                    "letter": letter, "reason": reason,
                    "proposed_at": time.strftime("%Y-%m-%d %H:%M")}
                hint = ("\n\nОтветь: «норм — откликнись» или «не норм, потому что …»"
                        if not proposed else "")
                msg = (f"🔎 Вакансия-кандидат\n"
                       f"{vac['title']} — {vac['employer']}\n"
                       f"{vac.get('salary') or 'ЗП не указана'}\n"
                       f"Почему: {reason[:160]}\n"
                       f"id {c['id']}\n{c['url']}{hint}")
                proposed.append(vac["title"])
                log("PROPOSE:", vac["title"][:60], "|", vac["employer"][:40])
                jsave(LEDGER_PATH, ledger)
                if not args.dry_run:
                    tg_send(msg)          # сразу владельцу, не ждём конца прогона
                continue

            attach_letter = bool(cfg.get("attach_cover_letters", True))
            letter_to_send = letter if attach_letter else ""
            log("APPLY:", vac["title"][:60], "|", vac["employer"][:40])
            if attach_letter:
                log("  letter:", letter[:200].replace("\n", " "))
            else:
                log("  letter: disabled by config")
            if args.dry_run:
                log("  [dry-run] отклик не отправлен")
                applied.append(vac["title"])     # учитываем к лимиту --max
                continue
            asks_letter = bool(re.search(r"сопроводительн", vac.get("desc", ""), re.I))
            res = apply_to(tab, c["url"], letter_to_send)
            if res.get("ok"):
                consec_fail = 0
                ledger["applied"][c["id"]] = {
                    "title": vac["title"], "employer": vac["employer"],
                    "url": c["url"], "letter": letter_to_send,
                    "letter_attached": bool(res.get("letter")),
                    "asks_letter": asks_letter,
                    "applied_at": time.strftime("%Y-%m-%d %H:%M")}
                mark = "" if res.get("letter") else " (без письма)"
                applied.append(f"• {vac['title']} - {vac['employer']}{mark}\n{c['url']}")
                if asks_letter:
                    note = ("отправил с этим письмом" if res.get("letter")
                            else "письмо прикрепить НЕ вышло — отправь его в чате отклика")
                    letters_fyi.append(
                        f"• {vac['title']} - {vac['employer']} ({note}):\n"
                        f"«{letter}»\n{c['url']}")
            elif res.get("stage") == "questionnaire":
                ledger["manual"][c["id"]] = {
                    "title": vac["title"], "employer": vac["employer"],
                    "url": c["url"], "letter": letter,
                    "reason": "вакансия с опросом/тестом"}
                manual.append(f"• {vac['title']} - {vac['employer']}\n{c['url']}")
            else:
                consec_fail += 1
                errors.append(f"{vac['title'][:40]}: {res.get('stage')}")
                tab.screenshot(f"{FAIL_SHOTS}/fail_{c['id']}.png")
                log("  FAIL stage:", res.get("stage"))
            jsave(LEDGER_PATH, ledger)
            time.sleep(random.uniform(*cfg["delay_between_applies_sec"]))

        jsave(LEDGER_PATH, ledger)
        if not args.dry_run:
            send_report()
    except Exception as e:
        tg_send(f"⚠️ hh.ru автоотклики упали: {str(e)[:300]}")
        raise
    finally:
        if tab:
            tab.close()
        if started:
            stop_browser()


if __name__ == "__main__":
    main()
