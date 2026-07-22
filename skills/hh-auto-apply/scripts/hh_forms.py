#!/usr/bin/env python3
"""hh_forms — заполнение анкет работодателей за владельца.

Умеет:
  --dump <url>                    показать вопросы формы (Google Forms или анкета hh)
  --fill <url> [--dry-run]        заполнить и отправить, ответы берутся из банка
  --chat-say <chat_id> <text>     написать сообщение в переписку hh.ru
  --list-unanswered <url>         вопросы, на которые в банке нет ответа

Банк ответов: /root/.hermes/state/hh_profile_answers.json — личные факты владельца
(ФИО, контакты, опыт, типовые формулировки). НЕ коммитится в git: это персданные.
Вопрос сопоставляется с банком по ключевым словам; если совпадения нет — вопрос
уходит в «неотвеченные», и его показывают владельцу, а не выдумывают.

Работает поверх залогиненного Chrome из hh-auto-apply (CDP :9225).
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hh_auto_apply as H  # noqa: E402

ANSWERS_PATH = H.STATE_DIR + "/hh_profile_answers.json"

# ── Google Forms: чтение и заполнение через DOM ────────────────────────────
# Возвращаем РЕАЛЬНЫЙ индекс блока (i), а не позицию в отфильтрованном списке:
# раньше чтение и заполнение фильтровали по-разному и ответы ложились не в те поля.
# Выбрасываем: (а) блоки-дубли, которыми Google рисует каждый чекбокс отдельно,
# (б) информационные блоки без единого поля ввода и без вариантов.
DUMP_JS = r"""
(() => [...document.querySelectorAll('[role="listitem"]')].map((li, i) => {
  const head = (li.querySelector('[role="heading"]') || li)
      .innerText.trim().split(String.fromCharCode(10))[0];
  const opts = [...li.querySelectorAll('[role="radio"],[role="checkbox"]')]
      .map(o => o.getAttribute('aria-label') || o.innerText.trim()).filter(Boolean);
  const free = !!li.querySelector('input[type="text"], textarea');
  const req = !!li.querySelector('[aria-required="true"]');
  return {i: i, q: head, options: opts, free: free, req: req};
}).filter(x => x.q
    && !(x.options.length === 1 && x.options[0] === x.q)
    && (x.free || x.options.length)))()
"""

FILL_JS = r"""
(plan => {
  const setVal = (el, v) => {
    const proto = el.tagName === 'TEXTAREA'
      ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, v);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
  };
  // index в плане — реальный индекс блока из DUMP_JS, фильтровать здесь нечего
  const items = [...document.querySelectorAll('[role="listitem"]')];
  const log = [];
  for (const step of plan) {
    const li = items[step.index];
    if (!li) { log.push('нет блока #' + step.index); continue; }
    if (step.kind === 'text') {
      const inp = li.querySelector('input[type="text"], textarea');
      if (!inp) { log.push('нет поля ввода #' + step.index); continue; }
      setVal(inp, step.value);
      log.push('текст #' + step.index);
    } else {
      // radio/checkbox: кликаем по совпадению aria-label
      for (const want of step.values) {
        const opt = [...li.querySelectorAll('[role="radio"],[role="checkbox"]')]
          .find(o => (o.getAttribute('aria-label') || o.innerText.trim()) === want);
        if (opt) { opt.click(); log.push('выбор #' + step.index + ': ' + want); }
        else log.push('НЕ НАЙДЕН вариант #' + step.index + ': ' + want);
      }
    }
  }
  return log.join('; ');
})
"""

SUBMIT_JS = r"""
(() => {
  const b = [...document.querySelectorAll('[role="button"],button')]
    .find(x => /^(отправить|saada ära|submit)$/i.test((x.innerText || '').trim()));
  if (!b) return 'КНОПКА ОТПРАВКИ НЕ НАЙДЕНА';
  b.click();
  return 'отправлено';
})()
"""

# ── анкета работодателя на самом hh (страница vacancy_response) ───────────
# Вопрос лежит текстом выше своей textarea, своего data-qa у него нет:
# поднимаемся по родителям до первого блока с осмысленным текстом.
HHQ_DUMP_JS = r"""
(() => [...document.querySelectorAll('textarea')].map(t => {
  let n = t, lab = '';
  for (let h = 0; h < 6 && n; h++) {
    n = n.parentElement;
    if (!n) break;
    const txt = (n.innerText || '').trim();
    if (txt.length > 15) { lab = txt.split(String.fromCharCode(10))[0]; break; }
  }
  // req=true всегда: на странице hh нет aria-required, а анкету работодатель
  // показывает только когда ответы ему нужны. Пустая анкета хуже неотправленной.
  return {q: lab, options: [], free: true, req: true};
}))()
"""

HHQ_FILL_JS = r"""
(plan => {
  const setVal = (el, v) => {
    Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')
      .set.call(el, v);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
  };
  const tas = document.querySelectorAll('textarea');
  const log = [];
  for (const step of plan) {
    const ta = tas[step.index];
    if (!ta) { log.push('нет поля #' + step.index); continue; }
    setVal(ta, step.value);
    ta.blur();
    log.push('ответ #' + step.index);
  }
  return log.join('; ');
})
"""

HHQ_SUBMIT_JS = r"""
(() => {
  const b = document.querySelector('[data-qa="vacancy-response-submit-popup"]');
  if (!b) return 'КНОПКА ОТКЛИКА НЕ НАЙДЕНА';
  if (b.disabled) return 'КНОПКА ЗАБЛОКИРОВАНА (не все обязательные поля заполнены)';
  b.click();
  return 'отправлено';
})()
"""


# ── переписка hh ──────────────────────────────────────────────────────────
# Точные хуки composer'а hh. Общие селекторы (любая textarea на странице) давали
# ложный успех: текст уходил в постороннее поле или оставался ЧЕРНОВИКОМ.
CHAT_JS = r"""
(text => {
  const box = document.querySelector('[data-qa="chatik-new-message-text"]');
  if (!box) {
    return /отключил переписку/i.test(document.body.innerText || '')
      ? 'ПЕРЕПИСКА ЗАКРЫТА: работодатель отключил чат по этой вакансии'
      : 'ПЕРЕПИСКА ЗАКРЫТА: поля ввода нет';
  }
  box.focus();
  Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')
    .set.call(box, text);
  box.dispatchEvent(new Event('input', {bubbles: true}));
  box.dispatchEvent(new Event('change', {bubbles: true}));
  return 'текст введён';
})
"""

CHAT_SEND_JS = r"""
(() => {
  const b = document.querySelector('[data-qa="chatik-do-send-message"]');
  if (!b) return 'НЕ ОТПРАВЛЕНО: кнопки отправки нет';
  if (b.disabled) return 'НЕ ОТПРАВЛЕНО: кнопка неактивна';
  b.click();
  return 'кнопка отправки нажата';
})()
"""


def _say_one(tab, text):
    """Одно сообщение: ввод, отправка, проверка появления в треде."""
    r = tab.eval("(" + CHAT_JS + ")(" + json.dumps(text, ensure_ascii=False) + ")")
    if not r or "ЗАКРЫТА" in r:
        return False, (r or "НЕ ОТПРАВЛЕНО: страница не ответила")
    time.sleep(1)
    tab.eval(CHAT_SEND_JS)
    time.sleep(3)
    probe = json.dumps(text[:120], ensure_ascii=False)
    seen = tab.eval(
        "(() => [...document.querySelectorAll('[data-qa^=\"chatik-chat-message-\"]')]"
        ".some(m => (m.innerText || '').includes(" + probe + ")))()")
    return bool(seen), ("ок" if seen else "НЕ ОТПРАВЛЕНО: в треде сообщения нет")


def chat_say(tab, text):
    """Пишет в переписку и ПРОВЕРЯЕТ, что сообщение реально появилось в треде.

    Многострочный текст composer hh не отправляет (кнопка активна, но сообщение
    не уходит и остаётся черновиком), поэтому шлём по абзацам отдельными
    сообщениями. Проверено 2026-07-22: однострочные уходят, многострочные нет.
    Успех — только если текст найден среди [data-qa^="chatik-chat-message-"].
    """
    paragraphs = [p.strip().replace("\n", " ") for p in text.split("\n\n")]
    paragraphs = [p for p in paragraphs if p]
    if not paragraphs:
        return "НЕ ОТПРАВЛЕНО: пустой текст"
    sent = 0
    for p in paragraphs:
        ok, msg = _say_one(tab, p)
        if not ok:
            return "%s (отправлено абзацев: %d из %d)" % (msg, sent, len(paragraphs))
        sent += 1
        time.sleep(1.5)
    return "отправлено и подтверждено в треде (абзацев: %d)" % sent


def match_answer(question, bank):
    """Ищет ответ в банке по ключевым словам. Возвращает (kind, value|values) или None."""
    q = question.lower()
    for entry in bank.get("rules", []):
        if all(kw.lower() in q for kw in entry["match_all"]):
            return entry
    return None


def build_plan(items, bank):
    """index в плане — «i» из дампа (реальный индекс блока в DOM), не порядковый номер.

    Возвращает (plan, blocking, optional): отправку блокируют только незакрытые
    ОБЯЗАТЕЛЬНЫЕ вопросы. Необязательные пропускаем — иначе любой информационный
    блок с полем «ваш ответ» намертво стопорит анкету.
    """
    plan, blocking, optional = [], [], []

    def miss(idx, text, required):
        (blocking if required else optional).append((idx, text))

    for pos, it in enumerate(items):
        idx = it.get("i", pos)
        req = bool(it.get("req"))
        entry = match_answer(it["q"], bank)
        if not entry:
            miss(idx, it["q"], req)
            continue
        if it["options"]:
            # берём только те варианты, что реально есть в форме
            wanted = [v for v in entry.get("choose", []) if v in it["options"]]
            if not wanted:
                miss(idx, it["q"] + "  [варианты: " + " | ".join(it["options"]) + "]", req)
                continue
            plan.append({"index": idx, "kind": "choice", "values": wanted})
        else:
            val = entry.get("text")
            if not val:
                miss(idx, it["q"], req)
                continue
            plan.append({"index": idx, "kind": "text", "value": val})
    return plan, blocking, optional


def open_form(url):
    H.ensure_browser()
    # hl=ru: под VPN Google отдаёт интерфейс на языке выходного узла, кнопки не совпадают
    if "docs.google.com" in url and "hl=" not in url:
        url += ("&" if "?" in url else "?") + "hl=ru"
    tab = H.Tab(url)
    time.sleep(10)
    here = tab.eval("location.href") or ""
    if "docs.google.com" in here and "hl=ru" not in here:
        tab.goto(here + ("&" if "?" in here else "?") + "hl=ru", wait=10, settle=2)
        time.sleep(6)
    return tab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--fill")
    ap.add_argument("--list-unanswered")
    ap.add_argument("--chat-say", nargs=2, metavar=("CHAT_ID", "TEXT"))
    ap.add_argument("--hh-vacancy", metavar="VACANCY_ID",
                    help="заполнить анкету работодателя на самом hh и откликнуться")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bank = H.jload(ANSWERS_PATH, {"rules": []})

    if args.hh_vacancy:
        H.ensure_browser()
        tab = H.Tab("https://hh.ru/applicant/vacancy_response?vacancyId=%s&hhtmFrom=vacancy"
                    % args.hh_vacancy)
        time.sleep(12)
        items = tab.eval(HHQ_DUMP_JS) or []
        if not items:
            print("анкеты нет — это обычный отклик, делать нечего")
            tab.close()
            return
        plan, blocking, optional = build_plan(items, bank)
        for i, q in optional:
            print("пропущен необязательный вопрос: #%d %s" % (i, q))
        for i, q in blocking:
            print("НЕТ ОТВЕТА В БАНКЕ (обязательный): #%d %s" % (i, q))
        if blocking:
            print("анкета НЕ отправлена — спросить владельца")
            tab.close()
            return
        print(tab.eval("(" + HHQ_FILL_JS + ")(" + json.dumps(plan, ensure_ascii=False) + ")"))
        if args.dry_run:
            print("[dry-run] не отправляю")
        else:
            time.sleep(2)
            print(tab.eval(HHQ_SUBMIT_JS))
            time.sleep(5)
            tab.goto("https://hh.ru/vacancy/" + args.hh_vacancy, wait=8)
            body = tab.eval("document.body.innerText") or ""
            print("ПОДТВЕРЖДЕНИЕ:",
                  "да" if ("Резюме доставлено" in body or "Вы откликнулись" in body)
                  else "НЕ НАЙДЕНО — проверить руками")
        tab.close()
        return

    if args.chat_say:
        chat_id, text = args.chat_say
        H.ensure_browser()
        tab = H.Tab("https://hh.ru/chat/" + chat_id)
        time.sleep(12)
        print(chat_say(tab, text))
        tab.close()
        return

    url = args.dump or args.fill or args.list_unanswered
    if not url:
        ap.error("нужен --dump, --fill, --list-unanswered или --chat-say")

    tab = open_form(url)
    items = tab.eval(DUMP_JS) or []
    if not items:
        print("вопросов не найдено — форма не прогрузилась или другая разметка")
        tab.close()
        return

    if args.dump:
        for i, it in enumerate(items):
            print("%2d. %s" % (i, it["q"]))
            if it["options"]:
                print("    варианты:", " | ".join(it["options"]))
        tab.close()
        return

    plan, blocking, optional = build_plan(items, bank)
    for i, q in optional:
        print("пропущен необязательный вопрос: #%d %s" % (i, q))
    if blocking:
        print("НЕТ ОТВЕТА В БАНКЕ (обязательные, спросить владельца):")
        for i, q in blocking:
            print("  #%d %s" % (i, q))
    if args.list_unanswered or blocking:
        # наполовину заполненная обязательная анкета хуже незаполненной — не отправляем
        print("форма НЕ отправлена")
        tab.close()
        return

    print(tab.eval("(" + FILL_JS + ")(" + json.dumps(plan, ensure_ascii=False) + ")"))
    if args.dry_run:
        print("[dry-run] не отправляю")
    else:
        time.sleep(2)
        print(tab.eval(SUBMIT_JS))
        time.sleep(4)
        body = tab.eval("document.body.innerText") or ""
        ok = any(s in body for s in ("Ответ записан", "Ваш ответ", "Vastus on salvestatud",
                                     "Your response has been recorded"))
        print("ПОДТВЕРЖДЕНИЕ ОТПРАВКИ:", "да" if ok else "НЕ НАЙДЕНО — проверить руками")
    tab.close()


if __name__ == "__main__":
    main()
