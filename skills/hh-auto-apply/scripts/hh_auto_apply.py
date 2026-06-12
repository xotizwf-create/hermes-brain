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
import urllib.parse
import urllib.request

import websocket

CDP = "http://127.0.0.1:9225"
STATE_DIR = "/root/.hermes/state"
CONFIG_PATH = STATE_DIR + "/hh_auto_config.json"
LEDGER_PATH = STATE_DIR + "/hh_applies.json"
ENV_PATH = "/root/.hermes/secure/hermes-gateway.env"
HH_ENV_PATH = "/root/.hermes/.env"
FAIL_SHOTS = "/opt/hh-browser/logs"

DEFAULT_CONFIG = {
    "paused": False,
    "max_applies_per_run": 8,
    "max_pages_per_query": 2,
    "delay_between_applies_sec": [25, 50],
    "queries": [
        "внедрение ИИ в бизнес",
        "внедрение искусственного интеллекта",
        "ИИ автоматизация бизнес-процессов",
        "AI автоматизация",
        "автоматизация бизнес-процессов нейросети",
        "интегратор ИИ",
        "AI-решения для бизнеса",
    ],
    "title_exclude": [
        "ml", "machine learning", "data scien", "deep learning",
        "computer vision", "nlp", "исследовател", "researcher",
        "devops", "backend", "frontend", "fullstack", "тестировщ",
        "qa", "1с", "1c", "бухгалт", "юрист", "аудит", "продаж",
        "дизайнер", "рекрутер", "hr ", "охран", "водител", "кладовщ",
    ],
    "profile": ("Я внедряю ИИ и автоматизации в бизнес-процессы: ИИ-агенты и "
                "ассистенты на LLM, Telegram-боты, интеграции с CRM и внутренними "
                "системами, no-code/low-code связки. Работаю от анализа процесса "
                "до запущенного решения. Бизнес-аналитик по бэкграунду."),
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
        if free_mb < 250:
            raise RuntimeError(f"мало памяти для браузера: {free_mb} МБ")
        subprocess.Popen(["bash", "/opt/hh-browser-start.sh", "https://hh.ru/"],
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

    def goto(self, url, wait=6.0):
        self._rpc("Page.navigate", url=url)
        time.sleep(wait)

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
                   + f"&page={page}&items_on_page=20")
            tab.goto(url, wait=6)
            items = tab.eval("""
(() => [...document.querySelectorAll('a[data-qa="serp-item__title"], a[data-qa*="vacancy-title"]')]
  .map(a => {
    const card = a.closest('[data-qa="vacancy-serp__vacancy"]') || a.closest('div');
    const emp = card && card.querySelector('[data-qa="vacancy-serp__vacancy-employer"]');
    const m = a.href.match(/vacancy\\/(\\d+)/);
    return m ? {id: m[1], title: a.textContent.trim(),
                employer: emp ? emp.textContent.trim() : "",
                url: "https://hh.ru/vacancy/" + m[1]} : null;
  }).filter(Boolean))()
""") or []
            for it in items:
                found.setdefault(it["id"], it)
            if len(items) < 15:
                break
        time.sleep(2)
    return list(found.values())


def title_ok(title, cfg):
    t = " " + title.lower() + " "
    return not any(x in t for x in cfg["title_exclude"])


def read_vacancy(tab, url):
    tab.goto(url, wait=6)
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
def llm_assess(cfg, vac):
    key = env_value(ENV_PATH, r"(?:export\s+)?GROQ_API_KEY\s*=\s*(.+)")
    if not key:
        raise RuntimeError("нет GROQ_API_KEY")
    system = (
        "Ты помогаешь Александру откликаться на вакансии. Его профиль: "
        + cfg["profile"]
        + " Ему интересно ТОЛЬКО внедрение ИИ/автоматизаций в бизнес и работа с "
        "бизнес-заказчиком. НЕ интересно: ML/DS-разработка, исследования, чистая "
        "разработка ПО, продажи, маркетинг, дизайн, поддержка.\n"
        "Верни строго JSON: {\"relevant\": true|false, \"reason\": \"кратко почему\", "
        "\"letter\": \"текст отклика\"}.\n"
        "Письмо: 2-4 коротких живых предложения по-русски, начни с «Здравствуйте!». "
        "Пиши как нормальный человек, простыми словами, без канцелярита и штампов "
        "(запрещено: «идеально подхожу», «рад возможности», «уникальный опыт», "
        "«не упущу шанс», длинные тире). Зацепись за одну конкретную деталь из "
        "описания вакансии. Коротко скажи, что делал похожее (из профиля). Без "
        "подписи и контактов. Если relevant=false — letter пустая строка."
    )
    user = (f"Вакансия: {vac['title']}\nКомпания: {vac['employer']}\n"
            f"Зарплата: {vac.get('salary','')}\n\nОписание:\n{vac['desc'][:3500]}")
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.4,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 # edge Groq режет дефолтный "Python-urllib" → 403; нужен обычный UA
                 "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) hermes-hh/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    data = json.loads(out["choices"][0]["message"]["content"])
    letter = (data.get("letter") or "").strip()
    # страховка от ИИ-маркеров
    letter = letter.replace("—", "-").replace("–", "-")
    return bool(data.get("relevant")), data.get("reason", ""), letter


# ── отклик ───────────────────────────────────────────────────────────────
APPLY_JS = r"""
async (letterText) => {
  const $ = s => document.querySelector(s);
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const btn = $('[data-qa="vacancy-response-link-top"]');
  if (!btn) return {ok: false, stage: "no-button"};
  btn.click();
  await sleep(2500);
  // предупреждение о другом городе/стране
  const reloc = $('[data-qa="relocation-warning-confirm"]');
  if (reloc) { reloc.click(); await sleep(2000); }
  // если открылась страница с опросом работодателя - не наш случай
  if (document.querySelector('[data-qa="task-body"], [data-qa="vacancy-response-questions"]'))
    return {ok: false, stage: "questionnaire"};
  // выбрать резюме, если предлагает (берём первое доступное)
  const resumeOpt = document.querySelector('[data-qa="resume-title"] input, input[name="resume_hash"]');
  // сопроводительное письмо
  let ta = document.querySelector('[data-qa="vacancy-response-popup-form-letter-input"]')
        || document.querySelector('textarea[data-qa*="letter"], textarea[name="letter"]');
  if (!ta) {
    const toggle = document.querySelector('[data-qa="add-cover-letter"], [data-qa="vacancy-response-letter-toggle"]');
    if (toggle) { toggle.click(); await sleep(1200); }
    ta = document.querySelector('[data-qa="vacancy-response-popup-form-letter-input"]')
      || document.querySelector('textarea[data-qa*="letter"], textarea[name="letter"]');
  }
  if (ta && letterText) {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
    setter.call(ta, letterText);
    ta.dispatchEvent(new Event("input", {bubbles: true}));
    await sleep(600);
  }
  const submit = document.querySelector('[data-qa="vacancy-response-submit-popup"]')
             || document.querySelector('form button[type="submit"][data-qa*="submit"]');
  if (!submit) return {ok: false, stage: "no-submit", hadLetter: !!ta};
  submit.click();
  await sleep(3500);
  const applied = !!document.querySelector('[data-qa="vacancy-response-link-view-topic"]')
              || !!document.querySelector('[data-qa="chatik-open-chatik"]')
              || !document.querySelector('[data-qa="vacancy-response-submit-popup"]');
  return {ok: applied, stage: applied ? "done" : "submit-no-confirm", hadLetter: !!ta};
}
"""


def apply_to(tab, vac_url, letter):
    tab.goto(vac_url, wait=6)
    expr = "(" + APPLY_JS + ")(" + json.dumps(letter, ensure_ascii=False) + ")"
    return tab.eval(expr) or {"ok": False, "stage": "eval-null"}


# ── main ─────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max", type=int, default=None)
    args = ap.parse_args()

    cfg = {**DEFAULT_CONFIG, **jload(CONFIG_PATH, {})}
    jsave(CONFIG_PATH, cfg)
    if cfg.get("paused"):
        log("paused в конфиге — выходим")
        return
    ledger = jload(LEDGER_PATH, {"applied": {}, "manual": {}, "skipped": {}})
    max_applies = args.max if args.max is not None else cfg["max_applies_per_run"]

    started = ensure_browser()
    tab = None
    applied, manual, errors = [], [], []
    try:
        tab = Tab("about:blank")
        if not check_login(tab):
            tg_send("⚠️ hh.ru: сессия разлогинилась. Зайди в браузер по ссылке "
                    "из `bash /opt/hh-browser-start.sh` и войди заново — "
                    "автоотклики на паузе.")
            return

        cands = search_vacancies(tab, cfg)
        log(f"найдено в выдаче: {len(cands)}")
        fresh = [c for c in cands
                 if c["id"] not in ledger["applied"]
                 and c["id"] not in ledger["manual"]
                 and c["id"] not in ledger["skipped"]
                 and title_ok(c["title"], cfg)]
        log(f"после журнала и префильтра: {len(fresh)}")

        consec_fail = 0
        llm_fail = 0
        for c in fresh:
            if len(applied) >= max_applies or consec_fail >= 3:
                break
            if llm_fail >= 4:
                tg_send("⚠️ hh.ru: LLM-оценка недоступна (Groq), прогон прерван.")
                log("aborting: 4 LLM failures in a row")
                break
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

            log("APPLY:", vac["title"][:60], "|", vac["employer"][:40])
            log("  letter:", letter[:200].replace("\n", " "))
            if args.dry_run:
                log("  [dry-run] отклик не отправлен")
                applied.append(vac["title"])     # учитываем к лимиту --max
                continue
            res = apply_to(tab, c["url"], letter)
            if res.get("ok"):
                consec_fail = 0
                ledger["applied"][c["id"]] = {
                    "title": vac["title"], "employer": vac["employer"],
                    "url": c["url"], "letter": letter,
                    "applied_at": time.strftime("%Y-%m-%d %H:%M")}
                applied.append(f"• {vac['title']} - {vac['employer']}\n{c['url']}")
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
            lines = []
            if applied:
                lines.append(f"✅ Откликнулся на {len(applied)} вакансий:\n"
                             + "\n".join(applied))
            if manual:
                lines.append(f"✍️ Требуют ручного отклика (опрос/тест), {len(manual)}:\n"
                             + "\n".join(manual))
            if errors:
                lines.append("⚠️ Ошибки: " + "; ".join(errors[:5]))
            if lines:
                tg_send("hh.ru — автоотклики\n\n" + "\n\n".join(lines))
            else:
                log("новых релевантных вакансий нет — отчёт не шлём")
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
