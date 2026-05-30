---
id: hermes-gateway-ux
type: engineering
tags: [hermes, gateway, telegram, ux, config, display, reasoning, progress]
updated: 2026-05-30
secret_refs: []
---

# Hermes gateway UX — indicator, live progress, tone

How the owner-facing behaviour ("Думаю…", live step updates, language, honesty) is controlled.
**It's config, not code** — these are built-in gateway features toggled in `~/.hermes/config.yaml`
(`gateway/run.py`), so never patch `run.py` for them. Config is server-only (600); the brain just
documents what's set.

## What was wrong (2026-05-30)
- "Странные/обрывистые сообщения" on "обнови" = the gateway restarting itself **mid-turn** (the MCP
  refresh ran `systemctl restart` in-process). Fixed in `skills/connect-mcp` — restart is now
  detached (`detached_restart()` via `systemd-run --on-active`). See `connectors/mcp-servers.md`.
- No visible "what is it doing": on Telegram **tool progress was off**
  (`display.platforms.telegram.tool_progress: false`).

## The knobs (in `config.yaml` → `display:` unless noted)
| Want | Knob | Set to |
|---|---|---|
| "Печатает…" indicator | native Telegram `send_chat_action("typing")` — always on, auto-resumes during a reply | (built-in, nothing to set) |
| Raw tool-call bubbles (`📚 skill_view`, `💻 terminal: "git …"`) | `platforms.telegram.tool_progress` | **`off`** — these dump tool names + commands/args = exactly the technical noise the owner rejects. Keep OFF. (`new`/`all` turn them on; `off` is bare-`off`→`False`→normalised to "off".) |
| Natural mid-turn updates in RU ("Проверяю токен…") | `interim_assistant_messages` | `true` (already) — **this is the real "live progress"**: the *model* narrates in plain Russian, driven by the system prompt. Content-aware, no tool internals. This carries the whole indicator story. |
| Busy ack when a msg arrives mid-work | `busy_ack_detail` / env `HERMES_GATEWAY_BUSY_ACK_ENABLED` | on (already) |
| Generic "⏳ Working — N min" heartbeat | `long_running_notifications` | **`false`** — OFF: the text is hardcoded **English** and appends the current **tool name** (`_status_detail`), so it leaks technical noise and breaks Russian-only. The model's `interim_assistant_messages` are the Russian substitute. (Interval would be `agent.gateway_notify_interval`, default 180s, but it's off now.) |
| Show raw model reasoning | `show_reasoning` | **`false`** — deliberately OFF: it prepends an English `💭 Reasoning:` block (raw chain-of-thought, EN + technical), which fights Russian-only. |
| UI language of gateway strings | `language` | `en` — **no `ru` locale ships**, so leave it; don't expect RU from this knob. RU comes from the system prompt, not here. |

**Design rule:** the "Думаю…/что делаю" signal is the native typing indicator + the **model's own
Russian narration** (`interim_assistant_messages` + system_prompt). Every gateway-generated
status string is English and often leaks tool names, so they stay OFF. Don't "turn on tool progress"
to make work visible — that brings back the `💻 terminal: "…"` noise. If a hard, guaranteed Russian
heartbeat every N seconds is ever needed (model goes silent inside one long tool call), it requires a
small `run.py` patch to translate `_heartbeat_text` + drop `_status_detail` — not a config toggle.

## Tone / behaviour
- The hard rules (only Russian; narrate steps briefly; honest "не нашёл" instead of made-up answers;
  no technical/English system strings in chat) live in **`config.yaml` `agent.system_prompt`** (read
  every turn) *and* in `profile/communication.md` (loaded via `INDEX.md`). The system_prompt is the
  reliable lever; the profile is the canonical long form.
- `display.personality` was `kawaii` (a cutesy persona). If the tone ever feels off / сюсюкающим,
  switch it to a neutral persona (e.g. `concise`) or empty. Left as-is 2026-05-30 — the system_prompt
  "деловой тон, без сюсюканья" line should dominate.

## Applying changes
Edit `config.yaml` (back it up first), then restart the gateway **from outside it** (SSH / systemd),
never from a chat turn: `systemctl restart hermes-gateway`. Most `display.*` settings are re-read per
turn; `system_prompt` and a few init-time ones need the restart. Verify: `systemctl is-active
hermes-gateway` + check the new process PID is fresh in `systemctl status`.
