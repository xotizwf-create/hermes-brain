---
name: vk-hermes-bridge-mvp
description: "Use when connecting Hermes Agent to a VK community via a safe MVP bridge: VK Callback API -> localhost Python bridge -> Hermes CLI -> VK messages."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [devops, hermes, vk, gateway, callback-api, bridge]
    related_skills: [hermes-agent, secure-project-server-ops]
---

# VK Hermes Bridge MVP

## Overview

Use this workflow to connect Hermes Agent to VK when VK is not a built-in Hermes Gateway platform. The recommended MVP is a small, isolated bridge:

`VK Callback API -> nginx HTTPS path -> localhost-only Python bridge -> Hermes CLI -> VK messages.send`

This keeps the existing Telegram/Hermes gateway untouched, stores VK credentials outside code, and limits the initial scope to text messages from an allowlisted VK user.

## When to Use

Use this when:

- The owner wants Hermes to answer in VK in addition to Telegram.
- A VK community should act as the bot identity.
- The goal is minimal risk to the current Hermes gateway.
- MVP scope starts as single allowlisted user, but can support practical rich features: text, photos, documents, VK voice/audio transcription, videos as links/files when VK exposes them, and outbound `MEDIA:/path` attachments.

Do not use this for:

- Full production multi-user VK support with rich attachments, routing, and admin controls — build a real platform adapter instead.
- Public bot access without a whitelist.
- Cases where the owner cannot provide a VK community access token with message permissions.

## Required Inputs

Ask for or derive:

1. VK community link or numeric group id.
2. Owner VK profile link or numeric user id.
3. VK community access token with **Messages** permission.
4. Callback API secret — generate a VK-safe alphanumeric string only.
5. HTTPS domain/path available through nginx.
6. Decision: MVP scope should be text-only and allowlisted unless explicitly expanded.

Never repeat the VK token in chat after the owner provides it. Store it in a root-only config file and redact it from logs/tool output.

## Safe Architecture

- Python bridge binds only to `127.0.0.1`, not a public interface.
- nginx exposes exactly one hidden HTTPS Callback path and proxies to the local bridge.
- VK token, callback secret, group id, allowlisted user id, and confirmation code live in a `.env` file with restrictive permissions.
- The bridge validates:
  - expected `group_id`;
  - Callback API `secret` for all non-confirmation events;
  - `message_new` event type;
  - `from_id` equals the allowlisted VK user id.
- The bridge responds to VK immediately with `ok`, then processes the message in a background worker so VK does not retry slow requests.
- Existing Telegram gateway is not restarted or modified.

## Implementation Checklist

1. Run server preflight before server work: memory, swap, disk, load, live services.
2. Create a dedicated directory such as `/opt/vk-hermes-bridge`.
3. Write a root-only `.env` with:
   - `VK_GROUP_ID`
   - `VK_GROUP_TOKEN`
   - `VK_ALLOWED_USER_ID`
   - `VK_CALLBACK_SECRET`
   - `VK_CONFIRMATION_CODE`
   - `VK_LISTEN_HOST=127.0.0.1`
   - `VK_LISTEN_PORT=<local-port>`
   - `HERMES_BIN=<path-to-hermes>`
   - `HERMES_SESSION_NAME=<stable-session-name>`
4. Resolve the numeric owner VK id via VK API if only a screen name/link was provided.
5. Fetch the Callback API confirmation code via VK API and store it in the `.env`.
6. Write the lightweight Python bridge using only stdlib when the server is memory constrained.
7. Test locally before nginx:
   - `GET /health` returns `ok`.
   - `POST` with `type=confirmation` returns the VK confirmation code.
   - non-allowlisted `message_new` is ignored.
8. Install a dedicated systemd service for the bridge with conservative limits.
9. Add a narrow nginx location for the hidden callback path and proxy it to `127.0.0.1:<port>`.
10. Test nginx config, reload nginx softly, and verify the public HTTPS callback URL returns the confirmation code.
11. In VK community settings, configure Callback API URL and secret, then enable `message_new` events.
12. Disable VK Long Poll if it was left over from an old bot and is not needed.
13. Clear old VK keyboards by sending a message with an empty keyboard to the owner, if old bot buttons remain.
14. Run a full synthetic callback test: event -> bridge -> Hermes -> VK `messages.send`.
15. Ask the owner to send a real text message in VK and verify the answer.

## Voice, Attachments, and Hermes Environment Pitfalls

For a rich VK bridge, reuse Hermes' existing media/STT paths instead of inventing separate storage:

- Add `/usr/local/lib/hermes-agent` to `sys.path` and use `gateway.platforms.base` cache helpers for inbound photos, audio, videos, and documents.
- Save VK voice/audio to Hermes' audio cache, then call `tools.transcription_tools.transcribe_audio` so the same STT provider configuration is used.
- The standalone systemd service must run with Hermes' venv Python, not plain `/usr/bin/python3`, otherwise packages like `openai` required for Groq STT may be missing. Use `ExecStart=/usr/local/lib/hermes-agent/venv/bin/python /opt/vk-hermes-bridge/vk_bridge.py`.
- Load the main profile env such as `/root/.hermes/.env` into the bridge process before calling STT; otherwise `GROQ_API_KEY` may exist on the server but be invisible to the bridge.
- If `tools.transcription_tools.get_env_value()` does not see process env in a direct systemd process, wrap it inside the bridge before `transcribe_audio` so it first checks `os.environ` and only then falls back to Hermes config.
- Verify voice end-to-end with a synthetic VK Callback `audio_message` that points to a temporary local OGG file; success is a log entry showing Groq transcription and then an answered VK event.
- Do not install local Whisper/faster-whisper on a tiny production host without preflight; prefer the existing cloud STT key if available.

## Hermes CLI Session Pitfall

If the bridge uses `hermes chat --continue <name>` before that named session exists, Hermes exits with a message like “No session found matching ...”. The bridge must handle this gracefully:

1. Try `--continue <stable-name>`.
2. If the named session is missing, run a first `hermes chat --query ...` without `--continue`.
3. Read the `session_id` printed by Hermes.
4. Rename the created session to the stable VK session name with `hermes sessions rename <session_id> <stable-name>`.
5. Future messages can use `--continue <stable-name>`.

This prevents the first real VK message from receiving a fake internal-error response.

## VK Keyboard Cleanup

Old community bots often leave a persistent keyboard in the VK dialog. The bridge does not need buttons for MVP. To clear it, send a normal VK `messages.send` to the owner with:

```json
{"buttons": [], "one_time": true}
```

If the VK client still shows buttons, tell the owner to close/reopen the dialog or send one more text message; VK may cache keyboards visually.

## Security Rules

- Never print or commit the VK access token, callback secret, or full hidden callback path in public logs/docs.
- Do not put the token in code or systemd command arguments.
- Redact token-looking strings in diagnostic output.
- Keep the bridge local-only; expose only nginx HTTPS.
- Use a hidden path for Callback API, but treat the VK callback secret as the real authentication.
- Keep MVP allowlisted to the owner’s numeric VK id.
- If the token was pasted into chat, recommend rotating it after the first successful test.

## Verification Checklist

- [ ] Server preflight performed; no heavy install/build on a constrained host.
- [ ] `.env` exists with restrictive permissions and contains no missing required keys.
- [ ] Bridge service is active.
- [ ] Local `/health` returns `ok`.
- [ ] Public Callback URL returns the confirmation code for VK confirmation.
- [ ] VK Callback server count/status checked; the new server is active.
- [ ] Long Poll is disabled if the MVP uses Callback API only.
- [ ] Non-allowlisted sender is ignored.
- [ ] Allowlisted synthetic callback sends a VK reply.
- [ ] Owner’s real VK message receives a normal Hermes answer.

## VK ↔ Telegram: что 1:1, а что нет (аудит 2026-06-10)

**Управление — то же самое.** Мост гонит сообщения в того же агента Hermes, поэтому из ВК доступны
те же команды, навыки, проекты, делегирование и логика, что и из Telegram. «Управлять всем из ВК как
из ТГ» — да, можно.

**Что у моста уже есть (близко к паритету):** входящие текст, фото, голосовые/аудио со STT (Groq
whisper), документы, видео-ссылки; исходящие — текст, фото, документы, и **голосовые сообщения**
(`upload_vk_audio_message`, добавлено 2026-06-10: `.ogg/.opus` уходят как голосовой кружок ВК через
`docs.getMessagesUploadServer?type=audio_message`, а не как файл-документ). Индикатор «печатает»
(`messages.setActivity`) есть.

**Чего в ВК нет и почему (не баг моста, а ограничения платформы):**
- **Реакции 👀/👍** на сообщение пользователя. В Telegram это нативный `set_message_reaction`
  (lifecycle: 👀 при старте → 👍/👎 в конце). У VK Callback API для community-ботов эквивалента нет —
  не реализуемо без костылей; принято оставить как есть. (Заменитель: индикатор «печатает».)
- **Нативный платформенный toolset.** Telegram — встроенная платформа Hermes (полный gateway
  lifecycle), а ВК — внешний мост через `hermes chat`. Поэтому тонкие платформенные фишки
  (inline-кнопки гейтвея, прогресс-реакции) в ВК отсутствуют by design; основная работа агента — та же.

**Если нужно расширить ВК-паритет дальше** — это правки `vk_bridge.py` (surgical, с бэкапом
`vk_bridge.py.bak.*`, `py_compile`, рестарт только `vk-hermes-bridge.service`). Менять авторизацию,
allowlist и секреты при этом нельзя.

## Current Known Good Pattern

The proven MVP used:

- A separate `vk-hermes-bridge.service`.
- A stdlib Python bridge.
- nginx HTTPS path -> localhost bridge.
- Hermes CLI in quiet mode with `--source vk`.
- Stable named session fallback logic as described above.
- VK old keyboard cleared with an empty keyboard payload.
- VK Long Poll disabled so old bots do not process messages in parallel.
