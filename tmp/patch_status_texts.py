"""One-off: livelier, varied status-message texts for the b24 bot (run on 186)."""
from pathlib import Path

path = Path("/var/www/albery/b24bot.py")
src = path.read_text(encoding="utf-8")


def norm(s: str) -> str:
    return s.replace("\r\n", "\n")


def splice(old: str, new: str, label: str) -> None:
    global src
    old, new = norm(old), norm(new)
    if src.count(old) != 1:
        raise SystemExit(f"PATCH FAILED at {label}: anchor found {src.count(old)} times")
    src = src.replace(old, new, 1)


splice(
    '''_B24_STATUS_STAGES: list = [
    (0, "⏳ Принял запрос — делаю вашу задачу..."),
    (20, "🔍 Уже в процессе: разбираюсь в вопросе..."),
    (60, "⚙️ Работаю: собираю данные инструментами..."),
    (150, "📝 Завершаю: формирую ответ..."),
    (300, "⏳ Задача объёмная — всё ещё работаю над ней, спасибо за терпение 🙏"),
]


def _b24_status_text(elapsed_s: float) -> str:
    text = _B24_STATUS_STAGES[0][1]
    for threshold, candidate in _B24_STATUS_STAGES:
        if elapsed_s >= threshold:
            text = candidate
    return text''',
    '''import random

# Each stage has several phrasings; one is picked at random when the stage begins, so the bot
# does not sound like a parrot across turns. Texts are universal (a question, a table, a report
# — not only "задача").
_B24_STATUS_STAGES: list = [
    (0, [
        "👋 Принял! Уже смотрю...",
        "👌 Взял в работу, секунду...",
        "🫡 Есть! Уже разбираюсь...",
        "⚡ Поймал запрос, приступаю...",
    ]),
    (20, [
        "🔍 Вникаю в суть, собираю нужное...",
        "🤔 Разбираюсь — уже есть за что зацепиться...",
        "🔎 Ищу данные по вашему запросу...",
    ]),
    (60, [
        "⚙️ В самом разгаре: сверяю данные...",
        "📊 Собираю картинку из данных...",
        "🛠 Проверяю детали, чтобы ответить точно...",
    ]),
    (150, [
        "✍️ Финишная прямая — собираю всё в понятный ответ...",
        "📝 Почти готово, оформляю ответ...",
    ]),
    (300, [
        "⏳ Запрос объёмный — досчитываю, спасибо за терпение 🙏",
        "🐢 Тут много данных — ещё чуть-чуть, хочу ответить точно 🙏",
    ]),
]


def _b24_status_stage(elapsed_s: float) -> int:
    stage = 0
    for i, (threshold, _variants) in enumerate(_B24_STATUS_STAGES):
        if elapsed_s >= threshold:
            stage = i
    return stage


def _b24_status_text(elapsed_s: float) -> str:
    return random.choice(_B24_STATUS_STAGES[_b24_status_stage(elapsed_s)][1])''',
    "stage variants",
)

splice(
    '''    def _typing_keepalive() -> None:
        keepalive_started = time.monotonic()
        shown_status = _b24_status_text(0)
        while not stop_typing.wait(20):
            _b24_app_typing(client_endpoint, access_token, bot_id, dialog_id)
            if status_message_id:
                stage_text = _b24_status_text(time.monotonic() - keepalive_started)
                if stage_text != shown_status:
                    shown_status = stage_text
                    _b24_status_update(client_endpoint, access_token, bot_id,
                                       status_message_id, stage_text)''',
    '''    def _typing_keepalive() -> None:
        keepalive_started = time.monotonic()
        shown_stage = 0
        while not stop_typing.wait(20):
            _b24_app_typing(client_endpoint, access_token, bot_id, dialog_id)
            if status_message_id:
                stage = _b24_status_stage(time.monotonic() - keepalive_started)
                if stage != shown_stage:
                    shown_stage = stage
                    _b24_status_update(client_endpoint, access_token, bot_id,
                                       status_message_id, _b24_status_text(
                                           time.monotonic() - keepalive_started))''',
    "stage-change updates",
)

path.write_text(src, encoding="utf-8")
print("PATCH OK")
