#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent patch: make the gateway's provider-error reply SPECIFIC.

Problem (2026-06-13): `_gateway_provider_error_reply` in gateway/run.py checked the
AUTH regex BEFORE the rate-limit regex, and had no dedicated branch for a plan
usage limit. The codex transport reports a rate-limited/`not logged in` state with
text containing "authentication failed", so a plain 429 *usage limit* was shown to
the owner as «⚠️ Provider authentication failed. Check the configured credentials» —
misleading: it is NOT a credential problem, just an exhausted quota.

Fix: reorder + add a usage-limit branch so the user sees the real cause:
  • plan usage limit (usage_limit_reached / "usage limit") -> «⏳ Лимит … сброс через Xч Yм»
    (with reset time parsed from resets_in_seconds when present);
  • transient rate limit -> «⏱️ временный rate-limit, повторите»;
  • genuine auth / no account -> «🔑 нет рабочего аккаунта / невалидные креды».

Runs as ExecStartPre of hermes-gateway.service (same contract as the media rescue
patch): write is py_compile-validated on a temp copy and swapped in atomically;
always exits 0 so gateway startup is never blocked. Idempotent (MARKER guard).

Source of truth in git: hermes-brain scripts/hermes_provider_error_patch.py
"""
import pathlib
import py_compile

BASE = pathlib.Path("/usr/local/lib/hermes-agent/gateway/run.py")
MARKER = "PATCH clear-provider-errors"

OLD = '''    if _GATEWAY_AUTH_ERROR_RE.search(text):
        return (
            "⚠️ Provider authentication failed. Check the configured credentials; "
            "raw provider details are in the gateway logs."
        )
'''

NEW = '''    _low = (text or "").lower()  # PATCH clear-provider-errors: limit vs rate-limit vs auth
    if "usage_limit_reached" in _low or "usage limit" in _low:
        import re as _re_pe
        _m = _re_pe.search(r"resets_in_seconds['\\\"]?\\s*[:=]\\s*(\\d+)", text or "")
        if _m:
            _s = int(_m.group(1))
            return (
                "⏳ Лимит ChatGPT/Codex исчерпан (квота плана). "
                "Сброс примерно через %dч %dм. "
                "Это НЕ проблема с аккаунтом/ключом — просто закончилась квота."
                % (_s // 3600, (_s % 3600) // 60)
            )
        return (
            "⏳ Лимит ChatGPT/Codex исчерпан (квота плана). "
            "Дождитесь сброса — это НЕ проблема с кредами."
        )
    if _GATEWAY_RATE_LIMIT_RE.search(text):
        return "⏱️ Провайдер временно ограничивает запросы (rate limit). Подождите немного и повторите."
    if ("no codex credentials" in _low or "no credentials" in _low
            or "trying fallback" in _low or "provider auth failed" in _low):
        return (
            "\U0001f9e0 Мозг (codex) сейчас недоступен: в пуле нет рабочего аккаунта. "
            "Чаще всего это исчерпанный лимит единственного аккаунта (нет резерва) — реже слетевшая "
            "авторизация. Точную причину и время сброса покажут /accounts и /limits."
        )
    if _GATEWAY_AUTH_ERROR_RE.search(text) or "not logged in" in _low:
        return (
            "\U0001f511 Похоже на проблему авторизации провайдера (невалидные креды/нужен повторный вход). "
            "Но если аккаунт один — это может быть и исчерпанный лимит: сверься с /accounts и /limits."
        )
'''


def _safe_write(path: pathlib.Path, text: str) -> bool:
    tmp = pathlib.Path(str(path) + ".tmp.provider_err")
    tmp.write_text(text, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except Exception as exc:
        print("provider_error_patch: py_compile failed, leaving original:", exc)
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(path)
    return True


def main() -> None:
    try:
        text = BASE.read_text(encoding="utf-8")
    except Exception as exc:
        print("provider_error_patch: cannot read run.py:", exc)
        return
    if MARKER in text:
        print("provider_error_patch: already applied")
        return
    if OLD not in text:
        print("provider_error_patch: anchor not found, skipping (run.py changed)")
        return
    patched = text.replace(OLD, NEW, 1)
    if _safe_write(BASE, patched):
        print("provider_error_patch: applied")


if __name__ == "__main__":
    main()
