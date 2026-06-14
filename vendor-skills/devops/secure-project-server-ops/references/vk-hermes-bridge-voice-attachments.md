# VK Hermes bridge: outbound voice attachments

Session lesson: VK bridge outbound TTS can create `MEDIA:/.../*.mp3`, but VK community messages should not upload that file as a generic document if the user expects a voice bubble.

## Symptom

- VK chat shows a fallback text like: `Не смог отправить вложение tts_YYYYMMDD_HHMMSS.mp3, но файл создан на сервере`.
- Service log shows VK API error 100: `One of the parameters specified was missing or invalid: file is undefined`.
- Root cause is often that the upload response did not include a non-empty `file`, but the bridge still called `docs.save(file="")`.

## Durable fix pattern

1. Treat audio extensions (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.opus`) as audio output, not generic docs.
2. Convert non-OGG/Opus TTS output to mono OGG/Opus before VK upload, for example with `ffmpeg`:
   - `-vn -ac 1 -ar 48000 -c:a libopus -b:a 32k`
3. Use VK `docs.getMessagesUploadServer` with `type=audio_message` and `peer_id=<user_id>`.
4. Upload multipart field named exactly `file`.
5. Before calling `docs.save`, verify the upload response contains a non-empty `file`; otherwise raise/log a clear bridge error. Calling `docs.save` with an empty file produces the misleading VK API error 100 `file is undefined`.
6. After `docs.save`, build the message attachment from `response.audio_message` when present, with fallback to `response.doc`.
7. Verify with a synthetic generated MP3 through the same `send_vk_attachment()` path, not only with `py_compile`/service restart.

## Verification snippet shape

- Generate a tiny MP3 with `ffmpeg -f lavfi -i sine=frequency=880:duration=0.35 ...`.
- Load `/opt/vk-hermes-bridge/.env` into the test process without printing secrets.
- Import `vk_bridge.py` with `sys.modules['vk_bridge']=module` before `exec_module()` so dataclasses resolve correctly.
- Call `send_vk_attachment(VK_ALLOWED_USER_ID, '/tmp/.../vk_voice_test.mp3')` and confirm it reaches VK as a voice message.
