#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent patch: full-markdown replies via Bot API 10.1 Rich Messages.

Bot API 10.1 (2026-06-11) lets bots send `rich_message: {"markdown": ...}`
(sendRichMessage / editMessageText) — native tables, headings, quotes,
collapsible details, math, 32768-char messages. The installed PTB (22.7)
predates it, so the adapter gets two raw-HTTPS hooks (stdlib urllib, no new
deps), each falling back to the legacy MarkdownV2 path on ANY failure:

  1. ``send()``      → try sendRichMessage before format/chunk;
  2. ``edit_message`` finalize → try rich editMessageText BEFORE the 4096
     overflow split, so long finals stay one message instead of N chunks.

A 404/401 from the API disables rich sends for the process lifetime;
``HERMES_TELEGRAM_RICH_DISABLE=1`` is the operator kill-switch.

Same contract as the other ExecStartPre patches: py_compile-validated tmp
copy, atomic swap, always exits 0.

Source of truth in git: hermes-brain scripts/hermes_rich_messages_patch.py
"""
import pathlib
import py_compile

LEGACY_TG = pathlib.Path("/usr/local/lib/hermes-agent/gateway/platforms/telegram.py")
NATIVE_TG = pathlib.Path("/usr/local/lib/hermes-agent/plugins/platforms/telegram/adapter.py")
TG = LEGACY_TG

MARKER = "_try_send_rich"
NATIVE_MARKER = "_rich_messages_enabled"

HELPERS_ANCHOR = '''    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SendResult:
        """Send a message to a Telegram chat."""
'''

HELPERS = '''    # ── Rich Messages (Bot API 10.1) — local patch 2026-06-11 ──────────────
    # sendRichMessage caps markdown at 32768 chars; keep headroom.
    _RICH_MAX_CHARS = 30000

    async def _rich_api_post(self, method: str, payload: dict):
        """POST to the Bot API; returns (ok_result_dict|None, description)."""
        import asyncio
        import os

        if os.environ.get("HERMES_TELEGRAM_RICH_DISABLE") == "1":
            return None, "disabled"
        if getattr(self, "_rich_send_disabled", False):
            return None, "disabled"
        token = getattr(self._bot, "token", None)
        if not token:
            return None, "no token"
        url = "https://api.telegram.org/bot%s/%s" % (token, method)

        def _post():
            import json as _json
            import urllib.error
            import urllib.request
            req = urllib.request.Request(
                url, data=_json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.status, _json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                try:
                    return e.code, _json.loads(e.read().decode("utf-8"))
                except Exception:
                    return e.code, {"ok": False, "description": str(e)}

        try:
            status, data = await asyncio.to_thread(_post)
        except Exception as exc:
            logger.info("[%s] %s transport failed, legacy fallback: %s",
                        self.name, method, str(exc)[:120])
            return None, str(exc)
        if data.get("ok"):
            return data, ""
        desc = str(data.get("description", ""))
        if status in (404, 401):
            # The Bot API server doesn't know rich messages — stop trying.
            self._rich_send_disabled = True
        logger.info("[%s] %s rejected (HTTP %s): %s — legacy fallback",
                    self.name, method, status, desc[:160])
        return None, desc

    async def _try_send_rich(self, chat_id, content, reply_to=None, metadata=None):
        """Best-effort Bot API 10.1 rich send; None means use the legacy path."""
        try:
            if not content or len(content) > self._RICH_MAX_CHARS:
                return None
            cid = str(chat_id)
            payload = {
                "chat_id": int(cid) if cid.lstrip("-").isdigit() else cid,
                "rich_message": {"markdown": content},
            }
            thread_id = self._metadata_thread_id(metadata)
            requested = self._message_thread_id_for_send(thread_id)
            if requested is not None:
                payload["message_thread_id"] = requested
            if reply_to:
                try:
                    payload["reply_parameters"] = {
                        "message_id": int(reply_to),
                        "allow_sending_without_reply": True,
                    }
                except (TypeError, ValueError):
                    pass
            data, _ = await self._rich_api_post("sendRichMessage", payload)
            if data:
                return str(data["result"]["message_id"])
            return None
        except Exception as exc:
            logger.info("[%s] rich send failed, legacy fallback: %s",
                        self.name, str(exc)[:120])
            return None

    async def _try_edit_rich(self, chat_id, message_id, content) -> bool:
        """Best-effort rich finalize-edit (editMessageText + rich_message)."""
        try:
            if not content or len(content) > self._RICH_MAX_CHARS:
                return False
            payload = {
                "chat_id": int(chat_id),
                "message_id": int(message_id),
                "rich_message": {"markdown": content},
            }
            data, desc = await self._rich_api_post("editMessageText", payload)
            if data:
                return True
            return "not modified" in desc.lower()
        except Exception as exc:
            logger.info("[%s] rich edit failed, legacy fallback: %s",
                        self.name, str(exc)[:120])
            return False

'''

SEND_OLD = '''        # Skip whitespace-only text to prevent Telegram 400 empty-text errors.
        if not content or not content.strip():
            return SendResult(success=True, message_id=None)
'''

SEND_NEW = '''        # Skip whitespace-only text to prevent Telegram 400 empty-text errors.
        if not content or not content.strip():
            return SendResult(success=True, message_id=None)

        # Rich Messages (Bot API 10.1): full markdown incl. tables/headings.
        rich_mid = await self._try_send_rich(chat_id, content, reply_to, metadata)
        if rich_mid is not None:
            return SendResult(success=True, message_id=rich_mid)
'''

EDIT_OLD = '''        # Pre-flight: if content already exceeds the limit, split-and-deliver
        # without round-tripping a doomed edit.
        if utf16_len(content) > self.MAX_MESSAGE_LENGTH:
'''

EDIT_NEW = '''        # Rich finalize-edit (Bot API 10.1) BEFORE the overflow split: a rich
        # message holds up to 32768 chars, so long finals stay one message.
        if finalize and await self._try_edit_rich(chat_id, message_id, content):
            return SendResult(success=True, message_id=message_id)

        # Pre-flight: if content already exceeds the limit, split-and-deliver
        # without round-tripping a doomed edit.
        if utf16_len(content) > self.MAX_MESSAGE_LENGTH:
'''


def _safe_write(path: pathlib.Path, text: str) -> bool:
    tmp = pathlib.Path(str(path) + ".tmp.rich_messages")
    tmp.write_text(text, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except Exception as exc:
        print("rich_messages_patch: py_compile failed, leaving original:", exc)
        tmp.unlink()
        return False
    tmp.replace(path)
    return True


def main() -> None:
    # Hermes 2026+ moved Telegram into plugins/platforms/telegram/adapter.py
    # and ships native rich_messages support behind telegram.extra.rich_messages.
    # In that layout there is nothing to monkey-patch; config enables it.
    try:
        native_text = NATIVE_TG.read_text(encoding="utf-8")
        if NATIVE_MARKER in native_text:
            print("rich_messages_patch: native adapter supports rich_messages; no patch needed")
            return
    except Exception:
        pass
    try:
        text = TG.read_text(encoding="utf-8")
    except Exception as exc:
        print("rich_messages_patch: cannot read legacy telegram.py:", exc)
        return
    if MARKER in text:
        print("rich_messages_patch: already applied")
        return
    missing = [name for name, frag in
               (("helpers-anchor", HELPERS_ANCHOR),
                ("send", SEND_OLD),
                ("edit", EDIT_OLD))
               if frag not in text]
    if missing:
        print("rich_messages_patch: anchors not found, skipping:", missing)
        return
    patched = text.replace(HELPERS_ANCHOR, HELPERS + HELPERS_ANCHOR, 1)
    patched = patched.replace(SEND_OLD, SEND_NEW, 1)
    patched = patched.replace(EDIT_OLD, EDIT_NEW, 1)
    if _safe_write(TG, patched):
        print("rich_messages_patch: applied")


if __name__ == "__main__":
    main()
