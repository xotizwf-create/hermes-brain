---
id: albery-hermes-operations
type: project
project: albery
tags: [albery, hermes, cron, telegram, sessions, stt, operations, reference]
updated: 2026-06-13
secret_refs: [proj/albery/ssh/root]
---

# Hermes — эксплуатация (cron, Telegram, сессии, фиксы)

> Извлечено из `hermes.md` при разбиении монолита по темам (2026-06-13). Сосед­ние документы: [hermes.md](hermes.md) (хаб), [hermes-setup.md](hermes-setup.md), [hermes-automations.md](hermes-automations.md), [hermes-operations.md](hermes-operations.md).

## Cron, Telegram и управление сессиями (операционка)

Обе cron-задачи доставляют результаты в Telegram:

```text
zoom-to-tasks -> Deliver: telegram:<TG_ID>
owner-daily   -> Deliver: telegram:<TG_ID>
```

Управление и наблюдение (по SSH на сервере):

```bash
hermes cron list                       # список автоматизаций
hermes cron pause/resume/edit <id>     # пауза/правка
hermes chat                            # живой чат с агентом (есть руки Albery MCP)
hermes sessions list                   # история запусков
hermes logs gateway -f                 # лог шлюза
journalctl -u hermes-gateway -f        # системный лог службы
systemctl status hermes-gateway        # статус службы
hermes send --to telegram:<TG_ID> "..." # тестовый пуш в Telegram
```

Telegram-бот принимает команды только от `TG_ID`. Снаружи бот работает через
polling, поэтому отдельный webhook/Nginx не нужен.

### Управление доступом к TG-агенту (кто может писать) — `tg_access.py` + skill `tg-access` (2026-06-16)

**Реальный гейт DM-доступа = env `TELEGRAM_ALLOWED_USERS` в `/root/.hermes/.env`** (читает
`_is_user_authorized` в `gateway/run.py`; по умолчанию остальным — отказ/pairing). `config.yaml`
`telegram.allowed_chats` синхронизируем для консистентности. Разрешены ровно двое (оба full-tier,
полные руки): **Александр `1451982360` (@alexxandrn, владелец) + Евгений `6514126096` (@Evgenii_Pal)**.
Отрицательные id в `allowed_chats` (`-528…`/`-524…`) — **групповые чаты** (home-channel + командная
группа), инфраструктура доставки, не трогать.

Управление **из чата**: навык `tg-access` (`/root/.hermes/skills/tg-access/SKILL.md`) + скрипт
[scripts/tg_access.py](scripts/tg_access.py) репо Albery (на проде копия `/root/.hermes/scripts/tg_access.py`,
700). Владелец просит «покажи/выдай/убери доступ» → агент зовёт `python3 .../tg_access.py
list|add <id> [имя]|remove <id>|whoami`. Скрипт правит env+config (бэкап), хранит имена в
`tg_access_names.json`, и **перезапускает gateway ОТЛОЖЕННО/detached** (`systemd-run --on-active=4s`):
агент сам крутится внутри gateway, мгновенный рестарт убил бы его до ответа. Владельца удалить нельзя.
@username бот не резолвит, пока человек не написал → сначала `/start`, потом `whoami` (id из лога), `add`.

**Почему skill, а не патч ядра:** кастомные slash-команды/патчи `telegram.py`/`run.py` **НЕ переживают
`hermes update`** — задокументированные ранее `/accounts`/`/limits` и `apply_patches.py` уже исчезли с
186. Поэтому управление — через native config/env + навык. Деплой скрипта: `git pull` в `/var/www/albery`
+ `cp scripts/tg_access.py /root/.hermes/scripts/`. Коммиты Albery: `da87823`, `e2b82ac`. Для проверки логов:
`tail -f /root/.hermes/logs/gateway.log` и `journalctl -u hermes-gateway -f`.
Если в Telegram снова появятся строки `⚙️ mcp_albery_...`, вернуть тихий режим:

```bash
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path('/root/.hermes/config.yaml')
cfg = yaml.safe_load(p.read_text()) or {}
cfg.setdefault('display', {}).setdefault('platforms', {}).setdefault('telegram', {})['tool_progress'] = 'off'
cfg.setdefault('cron', {})['wrap_response'] = False
p.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False))
PY
systemctl restart hermes-gateway
```

**Telegram toolset — обновлено 2026-05-30 (раньше было наоборот).** Прежнее ограничение снято: для
платформы `telegram` теперь **включены** `terminal`, `file`, `code_execution`, `skills`, `cronjob`,
`web`, `browser`, `vision`, `image_gen`, `tts`, `todo`, `memory`, `session_search`, `delegation`,
`messaging`, `computer_use`, `clarify`. Отключены только `video`, `video_gen`, `x_search`, `moa`,
`context_engine`, `homeassistant`, `spotify`, `yuanbao`. То есть через TG-чат у агента полноценные
«руки»: править свой мозг (git-клон, см. `skills/update-knowledge`) и код проектов, заводить cron,
писать себе скиллы — **под approval-gate** (показать дифф → дождаться «да» → commit/push). Изначально
эти toolset'ы отключали ради экономии 5-часового лимита Codex после инцидента с раздуванием контекста
(см. ниже) — следи за бюджетом и дроби крупные задачи. Проверка:

```bash
hermes tools list --platform telegram
```

28.05.2026 была удалена раздутая Telegram-сессия
`20260527_232811_0b70890e`: на команде `Ещё раз попробуй` агент сделал 25 API
вызовов, разогнал контекст до 100k+ токенов и полез в `search_files/read_file`.
Если такое повторится: `systemctl restart hermes-gateway`, затем
`hermes sessions list` и `hermes sessions delete --yes <session_id>`.

Чтобы Telegram больше не тянул бесконечную историю и не сжигал 5-часовой лимит
Codex, но при этом не забывал активный рабочий диалог, на сервере включён режим
«час простоя = новый чат, активный диалог = сжатие»:

```yaml
session_reset:
  mode: both
  idle_minutes: 30
  at_hour: 4
compression:
  enabled: true
  threshold: 0.5
  target_ratio: 0.2
  protect_first_n: 3
  protect_last_n: 20
  hygiene_hard_message_limit: 80
telegram_context_guard:
  enabled: true
  token_threshold: 50000
  message_limit: 80
```

Current values (Albery Hermes on `186.246.7.32`) as of 2026-05-30:

- `session_reset.idle_minutes=30`: if Telegram is quiet for 30 minutes, the next message starts a fresh session.
- `telegram_context_guard.token_threshold=50000`: before running the model on a large Telegram session, gateway asks whether to compress old context and then continue with the original message.
- `telegram_context_guard.message_limit=80`: extra safety valve for very long chats even if token estimate is unavailable.
- Context guard buttons: `Compress and continue` (`Сжать и продолжить`) sends visible Telegram chat messages `Сжимаю контекст...` before `/compress` and `Контекст сжат, думаю, как ответить на ваше сообщение...` after successful compression, suppresses the raw technical `/compress` result, then repeats the original message. `Continue without compression` (`Продолжить без сжатия`) runs the original message once without compression.
- Persistence: context-guard UX is re-applied on every gateway start by `/root/.hermes/patches/context_guard_ux_patch.py` via `/etc/systemd/system/hermes-gateway.service.d/30-context-guard-ux.conf`. **(⚠️ СТЁРТО к 2026-06-16 — этого патча и drop-in больше нет; сам context guard жив нативно. См. таблицу аудита ниже.)**
- Backs up before server patches: `/usr/local/lib/hermes-agent/gateway/run.py.bak.<stamp>`, `/usr/local/lib/hermes-agent/gateway/platforms/telegram.py.bak.<stamp>`, `/root/.hermes/config.yaml.bak.<stamp>`.

Hermes task time budgets (Albery Hermes on `186.246.7.32`) as of 2026-05-29 — **⚠️ СТЁРТО к 2026-06-16: ручной wall-clock guard (`task_wall_timeout_seconds`) больше не применён, остался только нативный таймаут простоя; ниже — история**:

```yaml
agent:
  task_wall_timeout_seconds: 600
  code_task_wall_timeout_seconds: 3600
```

- The same preference is saved in `/root/.hermes/memories/USER.md`.
- Ordinary non-code tasks have a 10 minute wall-clock budget from task start.
- Code/server/debug/deploy tasks have a 1 hour wall-clock budget from task start.
- Code-related includes files, scripts, repos, deploys, servers, APIs, MCP, logs, bugs, stack traces, Python/JS/TS/React/Node/Git/Docker/systemd.
- This is a separate wall-clock guard in `/usr/local/lib/hermes-agent/gateway/run.py`; `agent.gateway_timeout` still means inactivity timeout, not total task time.

Смысл настройки:

- если в Telegram нет активности 30 минут, следующий запрос стартует как новый
  чат — это защита от случайного подтягивания огромной истории;
- пользователь может вручную начать новый чат командой `/new` или `/reset`;
- каждый день в 04:00 gateway дополнительно сбрасывает активные сессии, чтобы
  они не жили неделями;
- если контекст растёт в рамках активного диалога, Hermes рано сжимает старую часть в summary
  и оставляет свежий хвост из последних 12 сообщений;
- дополнительно на проде установлен Telegram context guard в
  `/usr/local/lib/hermes-agent/gateway/run.py` и
  `/usr/local/lib/hermes-agent/gateway/platforms/telegram.py`: если перед
  запуском модели в Telegram-сессии примерно `50000+` токенов или `80+`
  сообщений, gateway **не запускает модель**, а присылает предупреждение с
  кнопками `Да, сжать и продолжить` / `Нет, продолжить так`. При выборе
  `Да` сначала выполняется `/compress`, затем повторяется исходное сообщение.
  При выборе `Нет` исходное сообщение запускается без сжатия, но это уже
  осознанное решение владельца;
- старые transcript-сессии чистятся через 3 дня;
- прошлые сессии физически остаются в SQLite, но **не подтягиваются
  автоматически** в Telegram: авто-поиск по старым диалогам отключён, потому что
  он может найти нерелевантное и снова сжечь лимит. Если после reset нужна
  связь с прошлой темой, лучше коротко напомнить контекст или заранее сохранить
  важное через `запомни: ...`;
- постоянные предпочтения нужно хранить не в длинной переписке, а в `memory`
  или в явных инструкциях cron/Albery. Пользователь может писать боту:
  `запомни: ...`, но важные правила для отчётов лучше фиксировать в
  `Настройки → Инструкции для ИИ` или в этом `agent.md`.

Веб-дашборд слушает `127.0.0.1:9119` (наружу не открыт). Смотреть через SSH-туннель:

```bash
ssh -L 9119:127.0.0.1:9119 root@186.246.7.32
# затем на ПК открыть http://localhost:9119  (нужен запущенный `hermes dashboard`)
```

«Обучение»: поведение отчётов/задач правится в Albery (`Настройки → Инструкции
для ИИ` и `Сводная аналитика → Настройка промтов`: контракты `zoom_processing`,
`owner_daily`) — это читают и Hermes, и внешние ассистенты. Уровень Hermes —
`hermes memory` и тексты cron (`hermes cron edit <id> --prompt "..."`).

Важно: на ПК (локальный WSL) остался свой Hermes с теми же cron-задачами, но без
запущенного gateway — он не сработает. Не запускать оба планировщика против одного
Albery (иначе версионная чехарда в отчётах). На тарифе Plus возможны upstream
`usage limit` на тяжёлых прогонах — при необходимости перейти на API-ключ.

### Голосовые сообщения — распознавание речи (STT), Groq (31.05.2026)

**Что было сломано.** Любое голосовое в Telegram «вешало» агента (бесконечное
«думаю…»). Hermes умеет принимать voice (скачивает .ogg, кэширует, вызывает
`tools.transcription_tools.transcribe_audio`), но провайдер STT стоял `local`
(faster-whisper), а сам пакет **не установлен**. В этом случае
`_transcribe_local` пытается **на лету `pip install faster-whisper`** (ctranslate2/
onnxruntime — сотни МБ) и затем качать+гонять модель CPU-инференсом. На этом хосте
(**957 МБ RAM, свободно ~330 МБ**) это виснет минутами и грозит OOM — ровно
запрещённый hard-rule #7 сценарий. **Локальный Whisper на этом проде гонять нельзя.**

**Решение — облачный STT (нагрузка на сервер = 0): Groq.** Бесплатный тариф,
`whisper-large-v3-turbo`, отличный русский, ~1-2 с. Настроено в `/root/.hermes/`:

```yaml
# config.yaml
stt:
  enabled: true
  provider: groq
  groq:
    model: whisper-large-v3-turbo
```

```ini
# /root/.hermes/.env  (chmod 600, секрет — НЕ в git)
GROQ_API_KEY=gsk_...        # ключ из https://console.groq.com/keys (бесплатно)
```

После правки — `systemctl restart hermes-gateway`. Транскрипт подставляется в текст
сообщения (`[The user sent a voice message... "<текст>"]`), и агент выполняет команду.

**Грабли (важно для будущих проверок):**
- Запрос к `api.groq.com` через `urllib`/`Python-urllib` **ловит Cloudflare 403 код
  1010** (блок по User-Agent), хотя ключ валиден. Реальный код Hermes идёт через
  `openai` SDK (httpx UA) — он **проходит**. Проверять ключ нужно SDK-путём
  (`OpenAI(base_url='https://api.groq.com/openai/v1').models.list()`), а не curl/urllib.
- Сервер ходит через VPN-Эстонию (`95.85.243.43`); до Groq достукивается.
- `ffmpeg` на сервере есть (нужен Hermes для не-WAV входов локального STT; для Groq
  конвертация не требуется — Groq принимает .ogg напрямую).

**Сменить провайдер/ключ:** правишь `stt.provider` (`groq`/`openai`/`mistral`/`xai`) и
соответствующий ключ в `.env` (`GROQ_API_KEY` / `VOICE_TOOLS_OPENAI_KEY` / …), затем
рестарт gateway. Доступные провайдеры — `tools/transcription_tools.py`. Бэкапы перед
правкой: `/root/.hermes/config.yaml.bak.<ts>`, `/root/.hermes/.env.bak.<ts>`.
**Не переключай на `local` на этом боксе** (OOM, rule #7).

### Cron script timeout (увеличен 28.05.2026 до 900s)

По умолчанию Hermes убивает `--script` cron-задачу через **120 секунд**. Для
`zoom-to-tasks` этого мало: когда `zoom_watchdog.sh` находит новый созвон и
запускает `hermes -z` с тяжёлым промптом (полный транскрипт + AI-генерация),
сессия идёт 3-7 минут — раньше cron падал с
`Script timed out after 120s: /root/.hermes/scripts/zoom_watchdog.sh`.

Лимит вынесен в `/root/.hermes/config.yaml`:

```yaml
cron:
  wrap_response: false
  max_parallel_jobs: null
  script_timeout_seconds: 900
```

Резолвится в порядке: env `HERMES_CRON_SCRIPT_TIMEOUT` → `cron.script_timeout_seconds`
в config.yaml → `120` (default). После изменения — `systemctl restart hermes-gateway`.
Бэкап старого конфига перед правкой: `/root/.hermes/config.yaml.bak.<unix_ts>`.

### Деплой Hermes-промптов

Промпт cron-задачи `owner-daily` живёт в **двух местах**:

1. **Источник правды (в git):** [scripts/hermes_owner_daily_prompt.txt](scripts/hermes_owner_daily_prompt.txt)
2. **Применённый на проде:** поле `prompt` у джобы `owner-daily` в
   `/root/.hermes/cron/jobs.json`.

Применение/обновление промпта на проде:

```powershell
python scripts/update_hermes_owner_daily_prompt.py
```

Скрипт:
- читает `scripts/hermes_owner_daily_prompt.txt`;
- через paramiko заходит на прод (пароль из локального `.env`, не светится в логе);
- сохраняет бэкап `/root/.hermes/cron/jobs.json.bak`;
- патчит `prompt` у джобы `owner-daily` и кладёт обратно (chmod 600);
- делает `systemctl restart hermes-gateway`.

Откат — переименовать `jobs.json.bak` обратно в `jobs.json` и рестартануть gateway.

### Правило: после любых изменений в Hermes / MCP — рестартить gateway и писать дальнейшие шаги владельцу

**Обязательное правило для будущих изменений.** `update_server.sh` перезапускает только `albery.service` (там живёт MCP HTTP-сервер). Но **`hermes-gateway.service` отдельный процесс**, который кэширует список MCP-инструментов на старте + Telegram-сессии дополнительно кэшируют toolset на старте сессии. Поэтому если ничего больше не делать — Hermes продолжит видеть старый список, и активный Telegram-чат тоже.

Триггеры, после которых **обязателен** рестарт `hermes-gateway`:
- добавлен/удалён/переименован MCP-инструмент в [mcp/context_server.py](mcp/context_server.py);
- изменена `inputSchema` или `description` существующего MCP-инструмента (Hermes их кэширует);
- изменён `/root/.hermes/config.yaml` (`display`, `cron`, `session_reset`, `compression`, `telegram_context_guard`, toolsets платформы);
- изменён `/root/.hermes/cron/jobs.json` (промпт, расписание, deliver) — `update_hermes_*_prompt.py` это уже делают сами;
- изменён код Hermes в `/usr/local/lib/hermes-agent/` (патчи gateway/telegram.py и т.п.).

Команда (рестарт пары):

```bash
ssh root@186.246.7.32 'systemctl restart albery hermes-gateway && systemctl is-active albery hermes-gateway'
```

Проверка, что Hermes увидел новый toolset:

```bash
ssh root@186.246.7.32 'hermes mcp test albery 2>&1 | grep -E "Tools discovered|<new_tool_name>"'
```

**После рестарта — обязательно сообщить владельцу дальнейшие шаги в чате.** Минимум: «в Telegram-чате с Hermes напиши `/reset` (или `/new`), чтобы сессия подтянула новый список инструментов». Без `/reset` активная Telegram-сессия может продолжать видеть старый toolset до тех пор, пока её не сбросит idle-таймер (30 минут, повторить cron-команду в чате, или одобрить рассылку — указать конкретное действие).

Признак, что toolset устарел: Hermes отказывает с описанием **другого** инструмента (видел 2026-05-28 после деплоя `send_bitrix_message` — Hermes сослался на `send_owner_recommendations_to_bitrix`, потому что в кэше сессии нового инструмента ещё не было).

### Command approval mode = off (полный авто-доступ codex, 2026-06-05)

По запросу владельца снят интерактивный approval-gate Hermes: в `/root/.hermes/config.yaml`
`approvals.mode: manual` → `off` (yolo-эквивалент). Telegram-агент больше НЕ показывает
«Command Approval Required» / security-scan (Tirith «Pipe to interpreter» и пр.) и выполняет
команды без подтверждения.

- **YAML-нюанс:** `mode: off` PyYAML читает как boolean `False`; код `tools/approval.py`
  (`_normalize`, ~847) намеренно трактует `False` как строку `"off"` — значение корректно,
  кавычки не нужны. Проверено: `raw=False → normalized=off`.
- **Что остаётся несбрасываемым даже при `off`:** HARDLINE-блок-лист (~12 катастрофичных
  паттернов, `approval.py` `HARDLINE_PATTERNS`, проверяется ДО yolo — `rm -rf /` и т.п.). Хост
  защищён от необратимого. Плюс агент не может сам править свой `~/.hermes/config.yaml`/`.env`
  (sensitive write target) — менять только напрямую по SSH под root.
- `approvals.cron_mode: deny` НЕ трогали — это про cron-контекст, не интерактив.
- **Бэкап перед правкой:** `/root/.hermes/config.yaml.bak.1780671169`.
- **Откат:** вернуть `approvals.mode: manual` (или восстановить бэкап) + `systemctl restart
  hermes-gateway`.
- После правки сделан `systemctl restart hermes-gateway`; в активном Telegram-чате нужен `/reset`,
  чтобы сессия подтянула новый режим.

### ⚠️ СТАТУС ручных патчей gateway — аудит 2026-06-16 (читать перед разделами ниже)

Апдейт/переустановка Hermes ~13.06 **стёрла большинство ручных патчей** ниже, а
авто-восстановление (`apply_patches.py`) тоже исчезло. Фактическое состояние на 186
(Hermes v0.14.0, код gateway от 13.06; на сервере в `/root/.hermes/patches/` остался только
`provider_error_patch.py`, в systemd drop-ins — лишь `20-provider-errors.conf` + `40-groq-env.conf`):

| Что описано ниже | Реальность 2026-06-16 |
|---|---|
| Context guard (анти-раздувание контекста) | ✅ **жив** — НАТИВНО в `run.py`, читает `config.yaml`→`telegram_context_guard` |
| `session_reset` / `compression` / `reasoning_effort: medium` | ✅ **живы** (через `config.yaml`, апдейт его не трогает) |
| Фикс `NameError: name 'event'` | ✅ **неактуален** — патч, вносивший баг (wall-clock guard), тоже стёрт → бага нет, агент работает |
| Команды бота `/accounts` `/limits` | ❌ **СТЁРТЫ** (нет в `telegram.py`); восстановить можно через `apply_patches.py`+systemd, если понадобятся |
| Wall-clock лимит задач (`task_wall_timeout_seconds` 600/3600) | ❌ **стёрт** — остался только нативный таймаут простоя |
| Русский UX кнопок сжатия (`context_guard_ux_patch.py`) | ❌ **стёрт** (косметика; нативные англ. подсказки) |
| `apply_patches.py` + `update.sh` авто-переприменение | ❌ **нет** (есть только `provider_error_patch.py`) |

**Важно:** Hermes **на ~2090 коммитов позади** (версия от 16.05). `hermes update` — большой
рискованный прыжок, который **снова сотрёт ручные патчи**. Не обновлять без отдельной подготовки.

Разделы ниже (29.05) сохранены как ИСТОРИЯ того, как патчи делались; по факту см. таблицу выше.

### Молчаливый дроп вложений на 186 — фикс 2026-06-16 (БЕЗ патча кода)

Симптом (self-check): `WARNING gateway.platforms.base: Skipping unsafe MEDIA directive path outside
allowed roots` — агент «отправил файл», а он не дошёл. Причина: Albery-Гермес крутится под **root**,
пишет файлы в `/root/...`, а `/root` — в денилисте доставки; нативный recency-rescue денилист не
обходит. Патч 217 (`hermes_media_rescue_patch.py`) сюда НЕ ложится — у 186 другая версия `base.py`,
анкоры не совпадают.

Фикс нативный, переживает `hermes update` (правки вне кода gateway):
1. `mkdir -p /root/.hermes/outbox` (chmod 700).
2. Код читает **ENV `HERMES_MEDIA_ALLOW_DIRS`** (а НЕ config-ключ `media_delivery_allow_dirs` — тот не
   подхватывается!). Добавлено `HERMES_MEDIA_ALLOW_DIRS=/root/.hermes/outbox` в
   `/root/.hermes/secure/hermes-gateway.env` (грузится drop-in’ом `40-groq-env.conf`; бэкап `.bak.<ts>`).
3. Правило в `/root/.hermes/memories/USER.md`: файлы для отправки сохранять в `/root/.hermes/outbox`.

Проверено: runtime-env гейта содержит переменную; `validate_media_delivery_path('/root/.hermes/outbox/x.pdf')`
возвращает путь. Бонус: `/tmp/<файл>` доставляется нативно (recency 600с). Остаточный риск: USER.md —
мягкое правило; если агент снова напишет в `/root` — дроп повторится (ловит self-check), тогда
портировать rescue-патч под анкоры 186.

### Фикс падения Hermes `NameError: name 'event'` + команды `/accounts` `/limits` + авто-переприменение правок (29.05.2026, частично СТЁРТО — см. таблицу выше)

**Симптом.** В Telegram-чате с Hermes любое сообщение (даже «Как меня зовут») падало с
`Sorry, I encountered an error (NameError). name 'event' is not defined`. В журнале
`journalctl -u hermes-gateway`:

```
File "/usr/local/lib/hermes-agent/gateway/run.py", line 17738, in _run_agent
    _event_text = (getattr(event, "text", "") or "").casefold()
NameError: name 'event' is not defined
```

**Причина.** В ручном патче «wall-clock task guard» ([agent.md:1718-1730](agent.md#L1718-L1730))
для классификации задачи (code/general) код обращался к переменной `event`, которой в
`_run_agent` нет — там текст сообщения лежит в параметре `message`.

**Фикс.** В `/usr/local/lib/hermes-agent/gateway/run.py`:
`_event_text = (getattr(event, "text", "") or "").casefold()` > `_event_text = (message or "").casefold()`.

#### Команды бота `/accounts` и `/limits`

Добавлены в `/usr/local/lib/hermes-agent/gateway/platforms/telegram.py`. Обрабатываются
**самим gateway напрямую** (перехват в `_handle_command` до вызова модели) — мгновенно и
**без траты токенов Codex**. Также добавлены в меню бота (`set_my_commands`).

Команда читает `/root/.hermes/auth.json` (+ `config.yaml` для стратегии failover) и выдаёт по
каждому аккаунту: активен/резерв, план (из JWT access_token), статус лимита, время сброса
(если упёрся в лимит), счётчик запросов. Пример:

```
🔑 Аккаунты Hermes

openai-codex — 2 шт., автопереключение: fill_first
  1. 🟢 активен — codex-bis.sdan21@gmail.com
     план: plus | лимит: ✅ свободен | запросов: 0
  2. ⚪ резерв — openai-codex-oauth-1
     план: plus | лимит: ✅ свободен | запросов: 0
```

Реальный остаток лимита ChatGPT нигде заранее не хранится — Hermes узнаёт его только когда
аккаунт упирается в лимит (тогда у credential заполняются `last_status` / `last_error_reset_at`,
и команда покажет `лимит: ⛔ … (сброс: …)`). Автопереключение (`fill_first`) включено через
`python scripts/hermes_codex_accounts.py --target new ensure-failover` — при исчерпании активного
аккаунта Hermes сам переходит на резервный.

#### Авто-переприменение правок («под ключ»)

`hermes update` перезаписывает `/usr/local/lib/hermes-agent` и стирает любые ручные патчи.
Чтобы это **никогда не теряло** фикс `event` и команды `/accounts`/`/limits`, настроено
самовосстановление:

- **Источник правды (в git):** [scripts/hermes_apply_patches.py](scripts/hermes_apply_patches.py) —
  идемпотентный скрипт. Переприменяет обе правки по якорям; пишет через temp + `py_compile` и
  атомарный `os.replace`, при любой ошибке откатывается и **никогда не ломает файл**; всегда
  завершается кодом 0 (не блокирует старт gateway). Если якоря в новой версии Hermes изменятся —
  печатает `SKIP (anchors changed)` и оставляет файл нетронутым (тогда патч переносится вручную).
- **На проде:** `/root/.hermes/patches/apply_patches.py` (права 700).
- **Context guard UX patch:** `/root/.hermes/patches/context_guard_ux_patch.py` (права 700) keeps the Telegram compression-button messages non-technical after Hermes updates.
- **Запуск перед каждым стартом gateway:** systemd drop-in
  `/etc/systemd/system/hermes-gateway.service.d/10-reapply-patches.conf` >
  `ExecStartPre=/usr/local/lib/hermes-agent/venv/bin/python /root/.hermes/patches/apply_patches.py`.
  Context guard UX additionally uses
  `/etc/systemd/system/hermes-gateway.service.d/30-context-guard-ux.conf` >
  `ExecStartPre=/usr/local/lib/hermes-agent/venv/bin/python /root/.hermes/patches/context_guard_ux_patch.py`.
  Любой `systemctl restart hermes-gateway` сам возвращает правки.
- **One-command обновление:** [scripts/hermes_update.sh](scripts/hermes_update.sh) (на проде
  `/root/.hermes/patches/update.sh`): `hermes update` > `daemon-reload` > `restart hermes-gateway`
  (триггерит переприменение) → проверка `is-active` + лог `hermes-reapply`.

Проверено 29.05.2026: восстановил оригинальный (непропатченный) `telegram.py` из бэкапа →
`systemctl restart hermes-gateway` → в логе `[hermes-reapply] telegram.py: accounts/limits re-applied`,
команды вернулись, gateway `active`.

**Как обновлять Hermes теперь:**

```bash
ssh root@186.246.7.32 'bash /root/.hermes/patches/update.sh'
# либо вручную: hermes update && systemctl restart hermes-gateway
```

**Обновить сами правки** (после изменения `scripts/hermes_apply_patches.py` в git): залить новый
файл в `/root/.hermes/patches/apply_patches.py` и `systemctl restart hermes-gateway`.

Бэкапы перед правками на проде: `run.py.bak.<ts>`, `telegram.py.bak.<ts>`.

### Локальный веб-интерфейс базы знаний agent-knowledge (29.05.2026)

Интерфейс, чтобы владелец сам добавлял/редактировал инструкции и скиллы Hermes в удобной
форме и заливал на сервер одной кнопкой. Только `agent-knowledge` (instructions + skills +
INDEX.md) — Albery, AI-конфиг агента и его память не затрагиваются.

- **Запуск:** двойной клик по [scripts/hermes-knowledge-ui.cmd](scripts/hermes-knowledge-ui.cmd)
  (или `python scripts/hermes_knowledge_ui.py`). Открывает `http://127.0.0.1:8765`.
- **Код:** [scripts/hermes_knowledge_ui.py](scripts/hermes_knowledge_ui.py) — чистый Python
  stdlib (без pip и npm), слушает только localhost.
- **Что делает:**
  - левая панель — `INDEX.md (маршрутизация)`, список инструкций, список скиллов;
  - редактор markdown со сплит-превью; кнопки «Сохранить», «Удалить»;
  - `+ добавить` инструкцию (файл `instructions/<имя>.md`) или скилл (папка
    `skills/<имя>/SKILL.md` с автогенерацией YAML-фронтматтера из имени и описания);
  - **«⬆ Залить на сервер»** — упаковывает локальный `agent-knowledge` в tar, кладёт через
    SFTP в `/root/.hermes/_kn_upload.tar`, на сервере бэкапит текущую базу в
    `agent-knowledge.bak`, затем `rm -rf agent-knowledge && tar -xf …` (сервер становится точной
    копией локального — удаления тоже применяются). Использует `_deploy_helper.connect("new")`.
- **Источник правды** — локальная папка `agent-knowledge/` в репозитории; заливка делает
  серверную `/root/.hermes/agent-knowledge` её точной копией.
- **Подхват изменений:** Hermes читает базу знаний по требованию (через `agent-knowledge/INDEX.md`),
  рестарт gateway не нужен. Чтобы новая инструкция «нашлась» — добавьте на неё строку в
  `## Routing` внутри `INDEX.md` (редактируется в том же интерфейсе).
- **Откат заливки:** на сервере `cd /root/.hermes && rm -rf agent-knowledge && mv agent-knowledge.bak agent-knowledge`.
