---
name: send-email
description: "Отправить письмо с почты владельца (alexxandr.nikitenko@gmail.com) кому угодно: текст и вложения, через Gmail API по HTTPS. ЕДИНСТВЕННЫЙ рабочий способ отправки почты на этом сервере (исходящий SMTP заблокирован хостером). Use when the owner says: отправь на почту, письмо, email, перешли файл/вакансии."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  created_by: agent
  created_at: 2026-06-11
---

# send-email — отправка почты с ящика владельца

Письмо уходит с собственного Gmail владельца; получатель видит обычное письмо от него.

## Команда

```bash
python3 /root/.hermes/agent-knowledge/skills/send-email/scripts/gmail_send.py \
  --to "адрес@домен" [--to "ещё@адрес"] \
  --subject "Тема" \
  --body "Текст" [--body-file /путь.txt] \
  [--attach /путь/к/файлу ...] [--cc ...] [--bcc ...] [--html]
```

- Успех = stdout `SENT id=...`. Только после этого говори «отправил».
- Любой другой вывод = НЕ отправлено: скажи владельцу честно, по-русски.

## Жёсткие правила
1. НИКОГДА не используй для отправки himalaya / msmtp / swaks — исходящий SMTP (25/465/587)
   заблокирован хостером навсегда, будет «Connection refused» после долгого таймаута.
2. Не выдумывай адрес получателя. Нет адреса — спроси владельца.
3. Письмо постороннему = внешнее действие: адресата и суть подтверждай, если владелец
   не дал их явно в этом же поручении.
4. Если скрипт пишет про invalid_grant или scope — токен протух: процедура в мозге,
   skills/google-account («Adding write access later»).
