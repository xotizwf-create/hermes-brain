#!/usr/bin/env python3
"""hh-forms-watch — сам закрывает анкеты работодателей.

Каждый прогон:
  1. сканирует переписки hh.ru на ссылки анкет (forms.gle / docs.google.com/forms);
  2. новую ссылку читает и пробует заполнить из банка ответов;
  3. если все вопросы закрыты — отправляет и пишет в чат «Анкету заполнил…»
     (если работодатель не отключил переписку);
  4. если хоть один вопрос новый — НИЧЕГО не отправляет, а присылает владельцу
     в Telegram список вопросов. Врать в анкете работодателя нельзя.

Молчит, когда новых анкет нет. Запускается кроном hh-forms-watch.
"""
import re
import sys
import time

sys.path.insert(0, "/root/.hermes/agent-knowledge/skills/hh-auto-apply/scripts")
import hh_auto_apply as H  # noqa: E402
import hh_forms as F  # noqa: E402

SEEN_PATH = H.STATE_DIR + "/hh_forms_seen.json"
FORM_RE = re.compile(r"https?://(?:forms\.gle/\S+|docs\.google\.com/forms/\S+)")
REPLY = "Анкету заполнил, жду обратной связи)"

CHATS_JS = r"""
(() => [...document.querySelectorAll('[data-qa^="chatik-open-chat-"]')].map(c => {
  const m = (c.getAttribute('data-qa') || '').match(/(\d+)$/);
  return m ? {id: m[1], text: (c.innerText || '')} : null;
}).filter(Boolean))()
"""


def main():
    seen = H.jload(SEEN_PATH, {})
    H.ensure_browser()
    tab = H.Tab("about:blank")
    if not H.check_login(tab):
        tab.close()
        print("сессия hh слетела — анкеты не трогаю")
        return

    tab.goto("https://hh.ru/chat", wait=12,
             ready_sel='[data-qa^="chatik-open-chat-"]', settle=2)
    rows = tab.eval(CHATS_JS) or []
    tab.close()

    # ссылка на анкету обычно в превью последнего сообщения; если обрезана —
    # открываем сам чат и ищем в полном тексте
    todo = []
    for r in rows:
        m = FORM_RE.search(r["text"])
        if m:
            todo.append((r["id"], m.group(0)))
            continue
        if "анкет" in r["text"].lower() or "форм" in r["text"].lower():
            t = H.Tab("https://hh.ru/chat/" + r["id"])
            time.sleep(8)
            body = t.eval("document.body.innerText") or ""
            t.close()
            m = FORM_RE.search(body)
            if m:
                todo.append((r["id"], m.group(0)))

    report = []
    for chat_id, url in todo:
        if seen.get(url, {}).get("done"):
            continue
        try:
            tab = F.open_form(url)
            items = tab.eval(F.DUMP_JS) or []
            if not items:
                tab.close()
                report.append("⚠️ анкета не прочиталась: " + url)
                seen[url] = {"done": False, "why": "не прочиталась"}
                continue
            bank = H.jload(F.ANSWERS_PATH, {"rules": []})
            plan, unanswered = F.build_plan(items, bank)
            if unanswered:
                tab.close()
                qs = "\n".join("• " + q for _, q in unanswered)
                report.append("📋 Анкета работодателя, нужны твои ответы:\n%s\n\nВопросы:\n%s"
                              % (url, qs))
                seen[url] = {"done": False, "why": "новые вопросы"}
                continue
            tab.eval("(" + F.FILL_JS + ")(" + H.json.dumps(plan, ensure_ascii=False) + ")")
            time.sleep(2)
            tab.eval(F.SUBMIT_JS)
            time.sleep(4)
            body = tab.eval("document.body.innerText") or ""
            ok = any(s in body for s in ("Ответ записан", "Ваш ответ",
                                         "Your response has been recorded"))
            tab.close()
            if not ok:
                report.append("⚠️ анкета заполнена, но подтверждения нет: " + url)
                seen[url] = {"done": False, "why": "нет подтверждения"}
                continue
            seen[url] = {"done": True, "at": time.strftime("%Y-%m-%d %H:%M")}

            # отписаться в переписке, если работодатель её не закрыл
            t = H.Tab("https://hh.ru/chat/" + chat_id)
            time.sleep(10)
            say = F.chat_say(t, REPLY)
            t.close()
            said = "подтверждено" in say
            report.append("✅ Анкета заполнена и отправлена: %s%s"
                          % (url, "" if said else " (в чат не написал: " + say + ")"))
        except Exception as e:
            report.append("⚠️ ошибка на анкете %s: %s" % (url, e))

    H.jsave(SEEN_PATH, seen)
    if report:
        H.tg_send("🗂 hh.ru: анкеты\n\n" + "\n\n".join(report))
        print("\n\n".join(report))


if __name__ == "__main__":
    main()
