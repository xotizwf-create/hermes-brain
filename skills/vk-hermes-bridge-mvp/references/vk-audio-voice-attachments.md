# VK voice/audio attachments in Hermes bridge

Use this when a VK bridge can send text but fails to send generated voice/audio back to VK.

## Durable lesson from session

Symptom in bridge logs/API response:

- VK API error 100
- message like: `One of the parameters specified was missing or invalid: file is undefined`
- Telegram delivery of the same voice/audio may work while VK delivery fails

Likely cause: the bridge is trying to pass an audio file to `messages.send` without first converting/uploading it in the VK-compatible voice-message flow, so the final `attachment`/`file` parameter is missing or invalid.

## Safe diagnostic path

1. Do production preflight first if on the live server: CPU/RAM/disk/load, current service status, and exact service unit.
2. Inspect the bridge code path that handles Hermes media output, especially audio/voice MIME/extension branches.
3. Confirm the failing VK response body before changing code; do not assume all attachment failures are the same.
4. For audio intended as a voice message, convert to a VK-compatible format before upload. In practice this usually means OGG/Opus voice-message format, then using the VK upload endpoint/flow expected for voice/doc attachments and passing the returned attachment string to `messages.send`.
5. Add logging around: local media path, converted path, upload server response, upload result, saved attachment id, and final `messages.send` response. Redact tokens and URLs containing secrets.
6. Restart only the bridge service, then verify with a real voice reply from VK and read fresh logs.

## Pitfalls

- Do not treat Telegram and VK attachment delivery as identical: Telegram can accept files directly from Hermes/gateway, while VK needs its own upload/save/send sequence.
- Do not report success from code edit alone. Verify with a real VK send attempt and the service logs.
- If VK and Telegram answers appear out of sync, distinguish transport bugs from channel-context bugs: attachment upload failure is transport; different memory/session/channel context is orchestration/configuration.
