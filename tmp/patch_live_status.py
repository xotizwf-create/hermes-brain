"""One-off: real-time activity status (Claude-style) for the b24 bot (run on 186).

The MCP server lives in the same Flask process as the bot bridge, so every tools/call on the
core connectors can feed a live activity ring; the status message then shows what the agent is
actually doing right now, with rotating 'thinking' fillers + a minute counter in between.
"""
from pathlib import Path

FILES = {
    "cs": Path("/var/www/albery/mcp/context_server.py"),
    "bot": Path("/var/www/albery/b24bot.py"),
}
SRC = {key: path.read_text(encoding="utf-8") for key, path in FILES.items()}


def norm(s: str) -> str:
    return s.replace("\r\n", "\n")


def splice(key: str, old: str, new: str, label: str) -> None:
    old, new = norm(old), norm(new)
    if SRC[key].count(old) != 1:
        raise SystemExit(f"PATCH FAILED at {label}: anchor found {SRC[key].count(old)} times")
    SRC[key] = SRC[key].replace(old, new, 1)


# ============================== context_server.py: activity feed =============================
splice(
    "cs",
    '''def _find_tool_matches(query: Any, tool_names: set[str] | None, limit: int) -> list[dict[str, Any]]:''',
    '''# Live activity feed for the chat bot's status message: every tools/call on the CORE
# connectors (the bot's own) is recorded here, so the bridge can show what the agent is doing
# right now. Cron agents use the full connectors (core=False) and never pollute this feed.
import collections as _collections

_RECENT_CORE_TOOL_CALLS: "_collections.deque" = _collections.deque(maxlen=64)


def record_core_tool_call(name: str) -> None:
    _RECENT_CORE_TOOL_CALLS.append((time.time(), str(name)))


def recent_core_tool_calls(since_ts: float) -> list:
    return [(ts, name) for ts, name in list(_RECENT_CORE_TOOL_CALLS) if ts >= since_ts]


def _find_tool_matches(query: Any, tool_names: set[str] | None, limit: int) -> list[dict[str, Any]]:''',
    "activity feed",
)
splice(
    "cs",
    '''            if core and name == "find_tool":
                matches = _find_tool_matches(args.get("query"), tool_names, int(args.get("limit") or 5))''',
    '''            if core and name == "find_tool":
                record_core_tool_call("find_tool")
                matches = _find_tool_matches(args.get("query"), tool_names, int(args.get("limit") or 5))''',
    "record find_tool",
)
splice(
    "cs",
    '''            if name in OWNER_ONLY_TOOL_NAMES and tool_names is not None:
                raise McpError(-32601, f"Unknown or unavailable tool: {name}")
            if name in ("start_here_always_read_ai_instructions", "get_ai_capabilities"):''',
    '''            if name in OWNER_ONLY_TOOL_NAMES and tool_names is not None:
                raise McpError(-32601, f"Unknown or unavailable tool: {name}")
            if core:
                record_core_tool_call(name)
            if name in ("start_here_always_read_ai_instructions", "get_ai_capabilities"):''',
    "record tool calls",
)

# ============================== b24bot.py: live status engine ================================
splice(
    "bot",
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
    '''import random

_B24_STATUS_GREETING = [
    "👋 Принял! Уже смотрю...",
    "👌 Взял в работу, секунду...",
    "🫡 Есть! Уже разбираюсь...",
    "⚡ Поймал запрос, приступаю...",
]

# What the agent is ACTUALLY doing right now: canonical MCP tool name -> human phrase.
# Fed live by mcp.context_server.recent_core_tool_calls (same Flask process).
_B24_TOOL_STATUS = {
    "search_tasks": "🔍 Ищу по задачам в Bitrix...",
    "get_task_comments": "💬 Читаю комментарии к задаче...",
    "create_bitrix_task": "🎯 Ставлю задачу в Bitrix...",
    "delete_bitrix_task": "🗑 Удаляю задачу...",
    "search_company_knowledge": "📚 Ищу в базе знаний компании...",
    "list_company_files": "🗂 Просматриваю документы компании...",
    "get_company_file": "📖 Читаю документ из базы знаний...",
    "get_org_structure": "🧑‍🤝‍🧑 Сверяюсь с оргструктурой...",
    "get_employee_absences": "🏖 Проверяю график отсутствий...",
    "list_zoom_calls": "🎥 Просматриваю список созвонов...",
    "get_zoom_call_transcript": "🎧 Читаю транскрипт созвона...",
    "search_zoom_transcripts": "🎥 Ищу по транскриптам созвонов...",
    "get_bitrix_bot_chat": "🧠 Вспоминаю нашу переписку...",
    "list_bitrix_bot_sessions": "🧠 Поднимаю историю диалога...",
    "send_bitrix_message": "✉️ Отправляю сообщение...",
    "fetch_url": "🌐 Открываю ссылку...",
    "create_google_sheet": "📊 Создаю Google-таблицу...",
    "get_google_sheet_meta": "📊 Открываю таблицу, смотрю листы...",
    "write_google_sheet_values": "✏️ Вношу данные в таблицу...",
    "write_company_sheet": "✏️ Вношу данные в таблицу...",
    "format_google_sheet": "🎨 Навожу красоту в таблице...",
    "share_drive_item_for_everyone": "🔗 Открываю доступ по ссылке...",
    "move_drive_file_to_folder": "🗂 Раскладываю файлы по папкам...",
    "list_drive_folder_items": "🗂 Просматриваю папку на Диске...",
    "create_drive_folder": "🗂 Создаю папку на Диске...",
    "organize_drive_folder": "🗂 Навожу порядок в папке...",
    "manage_apps_script": "🛠 Пишу код автоматизации...",
    "get_webapp_template": "🧩 Собираю веб-приложение...",
    "make_sheet_applet": "🧩 Подключаю таблицу к приложению...",
    "find_tool": "🧰 Подбираю подходящий инструмент...",
    "start_here_always_read_ai_instructions": "📋 Сверяюсь со своими инструкциями...",
    "get_ai_instructions": "📋 Сверяюсь со своими инструкциями...",
    "get_ai_capabilities": "📋 Уточняю свои возможности...",
    "get_context_guide": "🗺 Смотрю карту данных...",
    "search_messages": "💬 Ищу по сообщениям...",
    "get_chat_transcript": "💬 Читаю переписку чата...",
    "process_chat_ocr": "🖼 Распознаю изображения из чата...",
    "get_compact_export": "📦 Готовлю выгрузку данных...",
}

_B24_TOOL_STATUS_DEFAULT = "⚙️ Работаю с данными..."

# Fillers between real tool events — rotate every tick so the message never looks frozen.
_B24_STATUS_THINKING = [
    "🧠 Обдумываю, что с этим делать...",
    "🤔 Прикидываю варианты...",
    "🧩 Складываю всё воедино...",
    "✍️ Формулирую мысль...",
    "🔎 Перепроверяю детали...",
    "📐 Сверяю цифры и факты...",
    "☕ Минутку, довожу до ума...",
]


def _b24_status_text(_elapsed_s: float = 0) -> str:
    return random.choice(_B24_STATUS_GREETING)


def _b24_status_for_tool(tool_name: str) -> str:
    return _B24_TOOL_STATUS.get(str(tool_name), _B24_TOOL_STATUS_DEFAULT)


def _b24_status_thinking(previous: str) -> str:
    pool = [p for p in _B24_STATUS_THINKING if not str(previous).startswith(p)]
    return random.choice(pool or _B24_STATUS_THINKING)''',
    "status engine",
)

splice(
    "bot",
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
    '''    def _typing_keepalive() -> None:
        keepalive_started = time.monotonic()
        turn_started_ts = time.time()
        last_shown = ""
        last_tool_ts = 0.0
        while not stop_typing.wait(12):
            _b24_app_typing(client_endpoint, access_token, bot_id, dialog_id)
            if not status_message_id:
                continue
            text = None
            try:
                # Same process as the MCP server: show what the agent is REALLY doing right now.
                # With several concurrent turns the attribution is approximate — acceptable for
                # a cosmetic status line.
                from mcp.context_server import recent_core_tool_calls
                calls = recent_core_tool_calls(turn_started_ts)
                if calls and calls[-1][0] > last_tool_ts:
                    last_tool_ts = calls[-1][0]
                    text = _b24_status_for_tool(calls[-1][1])
            except Exception:  # noqa: BLE001
                pass
            if text is None:
                text = _b24_status_thinking(last_shown)
            minutes = int((time.monotonic() - keepalive_started) // 60)
            if minutes >= 1:
                text = f"{text} · {minutes} мин"
            if text != last_shown:
                last_shown = text
                _b24_status_update(client_endpoint, access_token, bot_id,
                                   status_message_id, text)''',
    "live keepalive",
)

for key, path in FILES.items():
    path.write_text(SRC[key], encoding="utf-8")
print("PATCH OK")
