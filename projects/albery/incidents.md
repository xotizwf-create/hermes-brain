---
id: albery-incidents
type: project
project: albery
tags: [incidents]
updated: 2026-07-12
secret_refs: []
---

# Albery — incidents

Append-only, newest on top.

## 2026-07-02 → 2026-07-12 — батч-синк молча умирал 10 дней (чаты и снапшоты задач устарели)

- **Impact:** реестр чатов стоял с 30.06, снапшоты задач/period-export и drive-синки — с 02.07.
  Живые задачи НЕ пострадали: bitrix_tasks обновляются событиями Bitrix inline
  (`BITRIX_TASK_EVENT_PROCESS_INLINE=1`) + кнопка «Обновить из Bitrix» — поэтому в UI всё
  выглядело свежим и поломку никто не заметил. Zoom тоже жил своим событийным путём.
- **Root cause:** рефакторинг ~02.07 вынес `sync_google_drive_company_documents` и
  `sync_google_drive_call_transcripts` из `app.py` в `gdrive.py`; hourly-cron
  `/etc/cron.d/albery-daily-sync` → `scripts/run_daily_sync.py` продолжал звать `app.sync_…`
  → `AttributeError` при построении списка шагов, т.е. ДО запуска любого шага — падали
  и чаты, и снапшоты, и team-синк. Traceback уходил только в
  `/var/log/albery/daily-sync.cron.log`; старый selfcheck смотрел лишь на ходы бота.
  Ночью 12.07 гейтвей-агент собрал отдельный systemd-таймер для drive-доков (работает),
  но остальной батч не чинил.
- **Fix (12.07):** `run_daily_sync.py` импортирует `gdrive` (albery-репо `4844321`);
  догоняющий прогон `AUTO_SYNC_CHAT_LOOKBACK_DAYS=13` — все шаги success, данные догнаны
  (чаты/снапшоты/sync_runs = 12.07 14:25 МСК).
- **Prevention:** `albery_selfcheck.py` расширен и проверен боем: свежесть батча по его же
  `daily-sync.log` (run_finished ≤2ч и success=true), systemd failed units, диск ≥85%,
  падения hermes-cron джоб (дедуп по сигнатуре), антиспам «тот же набор проблем — не чаще
  раза в 6ч» (state `/var/log/albery/selfcheck_state.json`). До фикса алерт реально ушёл
  в TG (батч + owner-weekly), после фикса — clean. Бэкапы: `/root/backups/*.bak-20260712`.
  Урок: при выносе функций из app.py грепать `app.<имя>` по scripts/ и кронам.

<!-- ## YYYY-MM-DD — title
- Impact / Timeline / Root cause / Fix / Prevention -->
