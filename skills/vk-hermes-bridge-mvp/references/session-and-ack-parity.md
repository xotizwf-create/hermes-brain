# VK bridge session/ack parity with Telegram

Use this reference when the owner asks for Telegram-like behavior in the VK Hermes bridge.

Durable pattern learned from the 2026-06 VK bridge fix:

- Treat VK as a chat surface with the same session ergonomics as Telegram: if a sender has been idle for 30 minutes, start a fresh Hermes CLI session; otherwise continue the active one.
- Persist the per-sender session/last-activity state so service restarts do not accidentally merge old context or reset active work unexpectedly.
- On every accepted inbound message, give immediate user feedback before invoking Hermes:
  - mark the message/read peer as read when possible;
  - send/refresh the VK `typing` activity;
  - attempt a VK reaction to show the bot took the item into work;
  - send a short intermediate phrase such as `Принял, уже смотрю…`.
- Keep `typing` refreshed while Hermes is still producing the final answer; a one-shot typing event expires too quickly during slow model/tool runs.
- Guard against VK echo loops: ignore outbound echo events and any event whose sender is the community/bot itself before queuing work for Hermes.
- Verification checklist after changing this logic:
  - `python3 -m py_compile vk_bridge.py` passes;
  - service restarts and `/health` returns `ok`;
  - synthetic outbound echo is ignored;
  - synthetic/real inbound allowlisted message gets immediate ack and one final reply;
  - logs show no second self-triggered processing after the final answer.
