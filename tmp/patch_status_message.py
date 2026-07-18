"""One-off: live progress status message for the b24 bot (run on 186)."""
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


# --- 1. helpers + stage texts before _b24_app_process -----------------------------------------
splice(
    '''def _b24_app_process(client_endpoint: str, access_token: str, bot_id: Any, dialog_id: str,
                     user_text: str, message_id: Any = "", from_user_id: Any = "") -> None:''',
    '''# --- Live progress message: one bot message edited in place while the brain works ------------
# Toggled by B24_STATUS_MESSAGE=1. Every call is best-effort: a failed status update must never
# break the answer path.
_B24_STATUS_STAGES: list = [
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
    return text


def _b24_status_send(client_endpoint: str, access_token: str, bot_id: Any, dialog_id: str) -> Any:
    """Post the initial progress message; returns its message id (None = feature off or failed)."""
    if os.getenv("B24_STATUS_MESSAGE", "").strip() != "1":
        return None
    try:
        res = _b24_app_call(client_endpoint, access_token, "imbot.message.add", {
            "BOT_ID": bot_id, "DIALOG_ID": dialog_id, "MESSAGE": _b24_status_text(0),
        })
        return res.get("result")
    except Exception:  # noqa: BLE001
        logging.debug("b24 testbot: status message send failed", exc_info=True)
        return None


def _b24_status_update(client_endpoint: str, access_token: str, bot_id: Any,
                       message_id: Any, text: str) -> None:
    try:
        _b24_app_call(client_endpoint, access_token, "imbot.message.update", {
            "BOT_ID": bot_id, "MESSAGE_ID": message_id, "MESSAGE": text,
        })
    except Exception:  # noqa: BLE001
        logging.debug("b24 testbot: status message update failed", exc_info=True)


def _b24_status_finish(client_endpoint: str, access_token: str, bot_id: Any, message_id: Any) -> None:
    """Remove the progress message right before the real answer lands. If the portal refuses the
    delete, degrade to editing it into a short 'done' pointer instead of leaving a stale status."""
    try:
        _b24_app_call(client_endpoint, access_token, "imbot.message.delete", {
            "BOT_ID": bot_id, "MESSAGE_ID": message_id, "COMPLETE": "Y",
        })
    except Exception:  # noqa: BLE001
        logging.debug("b24 testbot: status delete failed — editing to done-pointer", exc_info=True)
        _b24_status_update(client_endpoint, access_token, bot_id, message_id, "✅ Готово — ответ ниже 👇")


def _b24_app_process(client_endpoint: str, access_token: str, bot_id: Any, dialog_id: str,
                     user_text: str, message_id: Any = "", from_user_id: Any = "") -> None:''',
    "status helpers",
)

# --- 2. start the status message + fold updates into the keepalive thread ---------------------
splice(
    '''    status, error = "ok", None
    # Keep the 'typing…' indicator alive while the brain works (turns can take 6–60s; the Bitrix
    # indicator otherwise fades after ~30s and the bot looks frozen).
    stop_typing = threading.Event()

    def _typing_keepalive() -> None:
        while not stop_typing.wait(20):
            _b24_app_typing(client_endpoint, access_token, bot_id, dialog_id)

    threading.Thread(target=_typing_keepalive, daemon=True).start()''',
    '''    status, error = "ok", None
    # Live progress: one status message edited in place while the brain works, plus the native
    # 'typing…' indicator (it fades after ~30s on its own and the bot would look frozen).
    stop_typing = threading.Event()
    status_message_id = _b24_status_send(client_endpoint, access_token, bot_id, dialog_id)

    def _typing_keepalive() -> None:
        keepalive_started = time.monotonic()
        shown_status = _b24_status_text(0)
        while not stop_typing.wait(20):
            _b24_app_typing(client_endpoint, access_token, bot_id, dialog_id)
            if status_message_id:
                stage_text = _b24_status_text(time.monotonic() - keepalive_started)
                if stage_text != shown_status:
                    shown_status = stage_text
                    _b24_status_update(client_endpoint, access_token, bot_id,
                                       status_message_id, stage_text)

    threading.Thread(target=_typing_keepalive, daemon=True).start()''',
    "status lifecycle in keepalive",
)

# --- 3. swap the status message for the final answer -------------------------------------------
splice(
    '''    _b24_app_reply(client_endpoint, access_token, bot_id, dialog_id, answer,
                   keyboard=_b24_keyboard())''',
    '''    if status_message_id:
        _b24_status_finish(client_endpoint, access_token, bot_id, status_message_id)
    _b24_app_reply(client_endpoint, access_token, bot_id, dialog_id, answer,
                   keyboard=_b24_keyboard())''',
    "swap status for answer",
)

path.write_text(src, encoding="utf-8")
print("PATCH OK")
