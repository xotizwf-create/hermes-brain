---
id: albery-server-integrations-sync
type: project
project: albery
tags: [albery, sync, cron, google-drive, apps-script, reference]
updated: 2026-06-13
secret_refs: []
---

# Albery — синхронизация данных (почасовой cron, Google Drive / Apps Script)

> Извлечено из `server-context.md` при разбиении по темам (2026-06-13). Соседние документы: [server-context.md](server-context.md) (хаб), [server-infra.md](server-infra.md), [server-mcp-tools.md](server-mcp-tools.md), [server-integrations-sync.md](server-integrations-sync.md).

## Автоматическая Почасовая Синхронизация

Почасовая синхронизация ставится отдельным cron-файлом:

```text
/etc/cron.d/albery-daily-sync
```

Время запуска:

```text
каждый час в 00 минут по Europe/Moscow
```

Установить или обновить cron:

```bash
cd /var/www/albery && ./scripts/install_daily_sync_cron.sh
```

Запустить вручную:

```bash
cd /var/www/albery
ALBERY_LOG_DIR=/var/log/albery ALBERY_DAILY_SYNC_LOG=/var/log/albery/daily-sync.log .venv/bin/python scripts/run_daily_sync.py
```

Что запускает `scripts/run_daily_sync.py`:

- `bitrix_team` - синхронизация сотрудников Bitrix
- `bitrix_tasks` - синхронизация Bitrix-задач за период
- `bitrix_chat_messages` - синхронизация списка чатов и сообщений
- `zoom_api_calls` - синхронизация Zoom-созвонов через Zoom API
- `google_drive_company_instructions` - подтягивание Google Drive документов/инструкций в раздел "О компании"
- `google_drive_zoom_transcripts` - подтягивание `transcript.txt` из Google Drive для Zoom, если включено

Логи:

```text
/var/log/albery/daily-sync.log       структурированный JSONL-лог каждого шага
/var/log/albery/daily-sync.cron.log  stdout/stderr cron-обертки
```

Смотреть логи:

```bash
tail -n 200 /var/log/albery/daily-sync.log
tail -n 200 /var/log/albery/daily-sync.cron.log
grep '"status": "failed"' /var/log/albery/daily-sync.log
```

Настройки в `.env`:

```env
AUTO_SYNC_BITRIX_LOOKBACK_DAYS=30
AUTO_SYNC_CHAT_LOOKBACK_DAYS=1
AUTO_SYNC_CHAT_GENERATE_REPORTS=0
AUTO_SYNC_ZOOM_FROM=2026-01-01
AUTO_SYNC_ZOOM_TO=
AUTO_SYNC_GOOGLE_DRIVE_ZOOM_TRANSCRIPTS=1
```

Если нужно, чтобы при вечерней синхронизации сразу формировались дневные отчеты по чатам:

```env
AUTO_SYNC_CHAT_GENERATE_REPORTS=1
```

## Google Apps Script (Google Drive company sync)

Код Apps Script, который отдаёт документы и дерево папок из Google Drive,
лежит в репозитории и деплоится через `clasp` (а НЕ через `update_server.sh`).

- Проект: `scripts/google_drive_company_sync_project/` (`Code.gs`, `appsscript.json`)
- `.clasp.json` в корне: `scriptId = 1ga97W3bs386A00JokAHZyiQffEC1fFFjOoyzJm5GXUYkKjd3aXiRUoO9`
- Логин clasp: владелец скрипта `xotizwf@gmail.com` (`clasp show-authorized-user`)
- Прод web app deployment (это и есть `/exec` в `GOOGLE_APPS_SCRIPT_SYNC_URL`):
  - deploymentId = `AKfycbwsEL8z_HAoNmLP9utV4HCtkNDAcgbaAxnWsZ1Njs7h4L6DcrmRzcehzxB1y070CarBgA`
  - `/exec` URL = `https://script.google.com/macros/s/<deploymentId>/exec`

Обновление кода Apps Script (обновляет существующий `/exec`, URL не меняется):

```bash
clasp push --force
clasp redeploy AKfycbwsEL8z_HAoNmLP9utV4HCtkNDAcgbaAxnWsZ1Njs7h4L6DcrmRzcehzxB1y070CarBgA -d "что изменилось"
clasp deployments   # проверить активную версию
```

ВАЖНО — почему раньше `/exec` отдавал 404 после CLI-деплоя:

- Используйте `clasp redeploy <deploymentId>` (обновление на месте), а не
  `clasp deploy` (создаёт НОВЫЙ deployment с другим URL).
- В `appsscript.json` обязан быть блок `webapp`, иначе clasp создаёт версию
  без web app entry point и `/exec` отдаёт 404:

  ```json
  "webapp": { "executeAs": "USER_DEPLOYING", "access": "ANYONE_ANONYMOUS" }
  ```

Проверка, что `/exec` живой (должен вернуть JSON `{"ok": true, ...}`, не HTML):

```bash
token=$(awk -F= '$1=="GOOGLE_APPS_SCRIPT_SYNC_TOKEN"{print $2; exit}' .env)
url=$(awk -F= '$1=="GOOGLE_APPS_SCRIPT_SYNC_URL"{sub(/^[^=]*=/,""); print; exit}' .env)
curl -sS -L "$url?token=$token" | head -c 200
```

Логика синхронизации (инкрементально, без перезаписи неизменных файлов):

- сервер шлёт в Apps Script `known_files`/`known_folders` (id, имя, `updated_at`,
  `parent_folder_id`, `path`); скрипт по ним помечает неизменные файлы
  `unchanged: true` и НЕ выгружает их контент (DOC/XLS не конвертируются заново);
- сервер обновляет `company_folders` только при реальном изменении
  (сравнение `content_hash`, пути, родителя), иначе только `last_seen_at`;
- структура Google Drive зеркалится: папки -> `company_drive_folders` +
  `company_folders`, документы кладутся внутрь своих папок;
- временный сбой конвертации (`document_errors`, напр. Drive rate limit) НЕ
  удаляет уже синхронизированный документ — он подтянется на следующем прогоне.

Запустить серверную синхронизацию вручную:

```bash
cd /var/www/albery
.venv/bin/python - <<'PY'
from dotenv import load_dotenv; load_dotenv("/var/www/albery/.env")
import app, json
print(json.dumps(app.sync_google_drive_company_documents(), ensure_ascii=False, default=str)[:600])
PY
```

Авто-обновление по триггеру (near-realtime, ~1 минута):

- В Apps Script стоит time-driven триггер `checkDriveChangesAndNotify`
  (раз в минуту). Он считает лёгкую сигнатуру дерева папки (id, время правки,
  имена, родители; БЕЗ контента) и пингует сервер ТОЛЬКО при реальном изменении.
- Сервер: вебхук `POST /google-drive/events/<GOOGLE_DRIVE_EVENT_SECRET>` запускает
  ту же инкрементальную синхронизацию под Postgres advisory-lock (не пересекается
  с почасовым cron / ручной кнопкой; если занято — 409, триггер повторит).
- Секрет: `.env` `GOOGLE_DRIVE_EVENT_SECRET` == `CHANGE_NOTIFY_URL` в `Code.gs`.
- Триггер создаётся ОДИН раз вручную: открыть редактор скрипта, выбрать функцию
  `setupDriveChangeTrigger`, нажать Run, пройти авторизацию (нужны scope
  `script.scriptapp` и `drive`). Повторный запуск безопасен (старые триггеры
  удаляются). Снять триггер: запустить `removeDriveChangeTriggers`.
- Проверка вебхука: `curl https://mcp.m4s.ru/google-drive/events/<secret>` -> JSON
  `{"ok": true, ...}`; `POST` туда же запускает синхронизацию и возвращает result.
- Триггеры в Apps Script: https://script.google.com/home/triggers
