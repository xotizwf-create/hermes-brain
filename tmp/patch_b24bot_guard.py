"""One-off: add concurrency cap + retry + TG alerts to the b24 bot brain runs (run on 186)."""
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


# --- 1. module-level guard rails before hermes_brain_answer ---------------------------------
splice(
    '''def hermes_brain_answer(user_text: str, dialog_id: str, tier: str = "faq", from_user_id: Any = "") -> str:''',
    '''# --- Brain-run guard rails: concurrency cap, one retry, owner alerts ------------------------
# Each turn spawns a separate `hermes` CLI process (~250MB) on a 2GB box, so an unbounded burst
# of simultaneous users would swap/OOM the whole server.
_HERMES_MAX_CONCURRENCY = max(1, int(os.getenv("B24_HERMES_MAX_CONCURRENCY", "3")))
_HERMES_QUEUE_WAIT_S = int(os.getenv("B24_HERMES_QUEUE_WAIT_S", "180"))
_HERMES_RUN_SLOTS = threading.BoundedSemaphore(_HERMES_MAX_CONCURRENCY)
_OPS_ALERT_COOLDOWN_S = 600
_ops_alert_last_sent: dict[str, float] = {}
_ops_alert_lock = threading.Lock()


def _b24_ops_alert(kind: str, dialog_id: Any, tier: str, from_user_id: Any, detail: str) -> None:
    """Fire-and-forget Telegram alert to the Albery notifications group about a failed bot turn.
    Per-kind cooldown so one incident hitting many users does not flood the group."""
    now = time.monotonic()
    with _ops_alert_lock:
        if now - _ops_alert_last_sent.get(kind, -_OPS_ALERT_COOLDOWN_S) < _OPS_ALERT_COOLDOWN_S:
            return
        _ops_alert_last_sent[kind] = now
    text = (
        f"🚨 ИИ-агент (Bitrix): {kind}\\n"
        f"Диалог {dialog_id}, tier={tier}, user={from_user_id}\\n{detail}\\n"
        f"(повторы этого типа ближайшие {_OPS_ALERT_COOLDOWN_S // 60} мин не дублируются; "
        f"детали: journalctl -u albery)"
    )

    def _do() -> None:
        ok, err = _albery_tg_notify(text)
        if not ok:
            logging.error("b24 testbot: ops alert delivery failed: %s", err)

    threading.Thread(target=_do, daemon=True).start()


def _hermes_run_guarded(cmd: list, timeout_s: int, dialog_id: Any, tier: str,
                        from_user_id: Any, prompt_chars: int):
    """Run the hermes CLI under the concurrency semaphore, retrying once on a quick failure
    (non-zero rc / empty stdout). Returns (proc, None), (None, 'busy') or (None, 'timeout')."""
    if not _HERMES_RUN_SLOTS.acquire(timeout=_HERMES_QUEUE_WAIT_S):
        logging.warning("b24 testbot: hermes slot wait exceeded %ss dialog_id=%s tier=%s user_id=%s",
                        _HERMES_QUEUE_WAIT_S, dialog_id, tier, from_user_id)
        _b24_ops_alert(
            "очередь переполнена", dialog_id, tier, from_user_id,
            f"Свободный слот не появился за {_HERMES_QUEUE_WAIT_S}с "
            f"(лимит {_HERMES_MAX_CONCURRENCY} одновременных прогонов).",
        )
        return None, "busy"
    try:
        proc = None
        for attempt in (1, 2):
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout_s,
                    cwd="/root", env={**os.environ, "HOME": "/root"},
                )
            except subprocess.TimeoutExpired:
                logging.warning(
                    "b24 testbot: hermes timed out after %ss dialog_id=%s tier=%s user_id=%s prompt_chars=%s",
                    timeout_s, dialog_id, tier, from_user_id, prompt_chars,
                )
                _b24_ops_alert("таймаут хода", dialog_id, tier, from_user_id,
                               f"Мозг не ответил за {timeout_s}с; пользователь получил вежливый отказ.")
                return None, "timeout"
            if proc.returncode == 0 and (proc.stdout or "").strip():
                return proc, None
            logging.error("b24 testbot: hermes run failed (attempt %s/2): rc=%s err=%s",
                          attempt, proc.returncode, (proc.stderr or "")[:300])
        return proc, None  # both attempts bad -> caller reports the empty answer
    finally:
        _HERMES_RUN_SLOTS.release()


def hermes_brain_answer(user_text: str, dialog_id: str, tier: str = "faq", from_user_id: Any = "") -> str:''',
    "module-level guard rails",
)

# --- 2. run through the guard instead of a bare subprocess ----------------------------------
splice(
    '''    cmd = ["hermes", "-z", prompt, "--continue", session, "-t", toolset, "--yolo"]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s,
            cwd="/root", env={**os.environ, "HOME": "/root"},
        )
    except subprocess.TimeoutExpired:
        logging.warning(
            "b24 testbot: hermes timed out after %ss dialog_id=%s tier=%s user_id=%s prompt_chars=%s",
            timeout_s, dialog_id, tier, from_user_id, len(prompt),
        )''',
    '''    cmd = ["hermes", "-z", prompt, "--continue", session, "-t", toolset, "--yolo"]
    proc, run_fail = _hermes_run_guarded(cmd, timeout_s, dialog_id, tier, from_user_id, len(prompt))
    if run_fail == "busy":
        return ("Сейчас я обрабатываю много запросов одновременно 🙏 Подожди минуту-другую и "
                "отправь сообщение ещё раз — я отвечу.")
    if run_fail == "timeout":''',
    "guarded subprocess run",
)

# --- 3. empty answer: alert after the built-in retry ----------------------------------------
splice(
    '''    answer = (proc.stdout or "").strip()
    if not answer:
        logging.error("hermes brain empty: rc=%s err=%s", proc.returncode, (proc.stderr or "")[:300])
        return "Мозг временно недоступен, попробуй ещё раз чуть позже."
    return answer''',
    '''    answer = (proc.stdout or "").strip()
    if not answer:
        logging.error("hermes brain empty after retry: rc=%s err=%s",
                      proc.returncode, (proc.stderr or "")[:300])
        _b24_ops_alert("пустой ответ мозга", dialog_id, tier, from_user_id,
                       f"Два прогона подряд без ответа (rc={proc.returncode}).")
        return "Мозг временно недоступен, попробуй ещё раз чуть позже."
    return answer''',
    "empty answer alert",
)

# --- 4. turn exception: friendly reply + alert instead of a raw error ------------------------
splice(
    '''    except Exception as exc:  # noqa: BLE001
        logging.exception("b24 testbot: hermes brain failed")
        status, error = "error", str(exc)[:500]
        answer = f"Ошибка: {str(exc)[:200]}"''',
    '''    except Exception as exc:  # noqa: BLE001
        logging.exception("b24 testbot: hermes brain failed")
        status, error = "error", str(exc)[:500]
        _b24_ops_alert("исключение в ходе", dialog_id, tier, from_user_id, str(exc)[:300])
        answer = ("Что-то пошло не так на моей стороне 😔 Я уже отправил отчёт разработчикам. "
                  "Попробуй повторить запрос через пару минут.")''',
    "turn exception handling",
)

path.write_text(src, encoding="utf-8")
print("PATCH OK")
