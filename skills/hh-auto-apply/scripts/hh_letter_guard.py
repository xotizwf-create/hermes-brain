#!/usr/bin/env python3
"""hh_letter_guard — гарантия, что сопроводительное реально доехало.

Зачем: `apply_to()` возвращает `letter: true` по факту «поле найдено и текст записан»,
а не по факту доставки. Аудит 2026-07-22 показал 5 откликов из 13, где hh пишет
«Без сопроводительного письма». Этот модуль проверяет переписки и досылает письмо.

Использование как библиотеки (после пачки откликов):
    import hh_letter_guard as G
    G.guard(letters_by_vacancy_id)   # {"134744130": "текст письма", ...}

Как скрипт — аудит без правок:
    python hh_letter_guard.py --audit
"""
import sys
import time

sys.path.insert(0, "/root/.hermes/agent-knowledge/skills/hh-auto-apply/scripts")
import hh_auto_apply as H  # noqa: E402
import hh_forms as F  # noqa: E402

NO_LETTER = "Без сопроводительного письма"

CHATS_JS = r"""
(() => [...document.querySelectorAll('[data-qa^="chatik-open-chat-"]')].map(c => {
  const m = (c.getAttribute('data-qa') || '').match(/(\d+)$/);
  const lines = (c.innerText || '').split(String.fromCharCode(10)).filter(Boolean);
  return m ? {id: m[1], title: (lines[0] || '').slice(0, 50)} : null;
}).filter(Boolean))()
"""

# в шапке чата — ссылка на вакансию, по ней сопоставляем чат с id вакансии
CHAT_INFO_JS = r"""
(() => {
  const a = document.querySelector('[data-qa="chatik-header-vacancy-link"]');
  const href = a ? (a.getAttribute('href') || '') : '';
  const m = href.match(/vacancy\/(\d+)/);
  const body = [...document.querySelectorAll('[data-qa^="chatik-chat-message-"]')]
      .map(x => x.innerText).join(' | ');
  return {vacancy: m ? m[1] : '', body: body.slice(0, 4000)};
})()
"""


def scan(limit=25):
    """Возвращает список чатов: {chat_id, vacancy_id, has_letter}."""
    H.ensure_browser()
    tab = H.Tab("https://hh.ru/chat")
    time.sleep(12)
    rows = tab.eval(CHATS_JS) or []
    tab.close()

    out = []
    for r in rows[:limit]:
        t = H.Tab("https://hh.ru/chat/" + r["id"])
        time.sleep(8)
        info = t.eval(CHAT_INFO_JS) or {}
        t.close()
        body = info.get("body") or ""
        out.append({
            "chat_id": r["id"],
            "title": r["title"],
            "vacancy_id": info.get("vacancy") or "",
            "has_letter": NO_LETTER not in body,
            "body": body,
        })
    return out


def guard(letters, limit=25):
    """letters: {vacancy_id: текст письма}. Досылает письмо там, где его нет.

    Идемпотентно: пометка «Без сопроводительного письма» относится к самому отклику
    и остаётся в треде навсегда, даже если письмо потом дослали сообщением. Поэтому
    перед отправкой сверяем, нет ли уже текста письма среди сообщений, — иначе
    работодатель получит дубль.
    """
    report = []
    for row in scan(limit):
        if row["has_letter"]:
            continue
        letter = letters.get(row["vacancy_id"])
        if not letter:
            report.append("⚠️ без письма, текста нет под рукой: %s (вакансия %s)"
                          % (row["title"], row["vacancy_id"] or "?"))
            continue
        probe = letter.strip().split("\n\n")[0].strip().replace("\n", " ")[:60]
        if probe and probe in (row.get("body") or ""):
            report.append("уже дослано ранее: %s" % row["title"])
            continue
        tab = H.Tab("https://hh.ru/chat/" + row["chat_id"])
        time.sleep(10)
        res = F.chat_say(tab, letter)
        tab.close()
        report.append("%s → %s" % (row["title"], res))
        time.sleep(6)
    return report


if __name__ == "__main__":
    rows = scan()
    bad = [r for r in rows if not r["has_letter"]]
    print("проверено чатов:", len(rows), "| без письма:", len(bad))
    for r in bad:
        print("  %s  вакансия=%s  %s" % (r["chat_id"], r["vacancy_id"] or "?", r["title"]))
