---
id: albery-hermes
type: project
project: albery
tags: [albery, hermes, agent, codex, cron, telegram, mcp, reference]
updated: 2026-05-30
secret_refs: [proj/albery/ssh/root]
---

# Albery — Hermes agent (autonomous AI employee)

> ⚠ Server IP: current prod is `217.198.12.236`. Some legacy commands below reference the
> historical IP `186.246.7.32` from the 2026-05-27 setup; treat those as "the prod server"
> and verify against the live host before running (to be reconciled during brain sync).
> Credentials by NAME only — never print or commit secrets.

> Extracted from `server-context.md`. Hermes (Nous Research) is the autonomous agent that
> runs 24/7 on prod as a systemd service, lives in Telegram, with persistent memory, skills,
> a cron scheduler and an MCP client. Brain = ChatGPT (`gpt-5.5`) via the `openai-codex` provider.

## Codex (OpenAI) на прод-сервере

> ✅ **Установлено 2026-05-31 на текущем хосте `217.198.12.236`.** `codex-cli 0.135.0` →
> `/usr/bin/codex` (`npm install -g @openai/codex`, Node 22/npm 10, prefix `/usr`).
> `auth.json` скопирован с ПК (`C:\Users\hotiz\.codex\auth.json`) в `/root/.codex/auth.json` (600);
> `codex login status` → **Logged in using ChatGPT**. Исходящий IP `95.85.243.43` (VPN-Эстония),
> **403 нет**. **High-reasoning кодинг включён глобально:** `/root/.codex/config.toml` (600) =
> `model_reasoning_effort = "high"` — проверено `codex exec` (`model: gpt-5.5`,
> `reasoning effort: high`, ответ `PING-OK`). Делегирование (`skills/codex-delegation`) на 217
> теперь работает. Минор: bubblewrap не в PATH → Codex берёт встроенный; для полноценного
> sandbox опц. `apt install bubblewrap`. (Раздел ниже исходно описывал прежний хост `186.246.7.32`.)

Установлен `@openai/codex` (codex-cli) глобально через npm (Node 20+ уже есть):

```bash
npm install -g @openai/codex
codex --version
```

**Вход в ChatGPT-аккаунт НА сервере напрямую сделать нельзя:** OpenAI (Cloudflare)
блокирует страницы входа и `codex login --device-auth` с серверных/дата-центровых
IP (403). При этом сам рантайм Codex с уже готовым токеном через VPN работает.
Поэтому вход переносится с ПК:

1. На ПК, где Codex залогинен в ChatGPT (`codex login` через браузер), взять файл
   `%USERPROFILE%\.codex\auth.json` (Windows) или `~/.codex/auth.json` (Linux/mac).
2. Положить его на сервер в `/root/.codex/auth.json` (chmod 600).
3. Проверить: `codex login status` → должно быть `Logged in using ChatGPT`.

**Критично:** без блокировки исходящего IPv6 (см. VPN-раздел, она в `vpn_apply.sh`)
Codex идёт в `wss://chatgpt.com/backend-api/codex/responses` по российскому IPv6 в
обход VPN и получает `403`. С блокировкой IPv6 трафик идёт через IPv4-VPN (Эстония),
и бэкенд отвечает.

Тест запроса с сервера:

```bash
cd /tmp && printf "Respond with exactly: PING-OK" | codex exec --skip-git-repo-check
```

- Реальная работа Codex зависит от тарифа ChatGPT-аккаунта: на бесплатном будет
  `You've hit your usage limit` — нужен ChatGPT Plus/Pro с квотой Codex.
- Если вход на сервере «протух» (токен истёк и не обновляется автоматически) —
  просто заново скопировать свежий `~/.codex/auth.json` с ПК.
- Логин/пароль ChatGPT в `.env` (`GPT Логин`/`GPT_Password`) для входа Codex
  бесполезны (вход только браузером) — их лучше убрать из `.env`.

## Hermes Agent (автономный ИИ-агент, мозг = ChatGPT Plus)

Настроено 2026-05-27. Поставлен локально на ПК в WSL2 для теста; следующий шаг —
перенос на прод-сервер.

### Что это и зачем

`Hermes Agent` (Nous Research, open-source) — автономный агент с **постоянной
памятью, навыками, cron-планировщиком и MCP-клиентом**. Он **model-agnostic**:
своего «мозга» у него нет, модель подключается по OAuth/API. Это **обвязка-агент**
(как Codex/Cline), а НЕ модель.

Наша задача: «цифровой сотрудник» по отчётам/действиям (а не правка кода). Albery
уже отдаёт инструменты для этого через MCP — Hermes выступает автономным
исполнителем поверх них. «Мозг» сейчас — **ChatGPT Plus (модель `gpt-5.5`)**.

### Ключевые пути и факты

```text
версия:        v0.14.0
бинарь:        ~/.local/bin/hermes
установка:     ~/.hermes/hermes-agent
конфиг:        ~/.hermes/config.yaml
токены аккаунтов: ~/.hermes/auth.json   ← для смены аккаунта и переноса на сервер
провайдер:     openai-codex   (= аккаунт ChatGPT через OAuth)
модель:        gpt-5.5        (доступна и gpt-5.4)
дашборд:       http://127.0.0.1:9119   (hermes dashboard --tui)
```

### Важные понятия (чтобы не путать)

- Провайдер **`openai-codex`** — это НЕ отдельный урезанный продукт, а технический
  **OAuth-канал к твоему аккаунту ChatGPT**. Модель `gpt-5.5` — обычная ChatGPT.
- Подписку ChatGPT в Hermes можно подключить **только** через `openai-codex`.
  Провайдер `openai` использует **API-ключ**, а не подписку.
- **Лимиты**: на подписке Plus они есть всегда, как ни подключайся. «Без потолка» —
  только **API-ключ** (платишь по токенам). Для автономного агента 24/7 на сервере
  правильнее API-ключ; подписка Plus периодически будет упираться в `usage limit`.

### Предусловие на Windows-ПК: сеть WSL2 через VPN

`AmneziaVPN` на Windows ломает сеть внутри WSL2 (исходящий TCP виснет). Лечится
**mirrored-режимом** — WSL начинает ходить через сетевой стек хоста (вместе с VPN,
выход через Эстонию `95.85.243.43`), и API OpenAI/Anthropic становятся доступны.

Создать `C:\Users\<user>\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
autoProxy=true
```

Затем `wsl --shutdown` (перезапуск WSL). Проверка из WSL:
`curl -s https://api.ipify.org` → должно быть `95.85.243.43`.

### Установка Hermes (Linux / WSL2 / сервер)

Требуется **Node.js 20+** (для сборки веб-дашборда на Vite) и Python 3.11
(ставит установщик сам). На прод-сервере Node 20 уже есть; в WSL ставился nvm-ом.

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc        # или новый терминал
hermes --version
```

- Установщик ставит uv, Python 3.11, клонирует репо, создаёт venv.
- Опциональные `ripgrep`/`ffmpeg` требуют sudo — можно пропустить (агент работает
  без них; поиск идёт через grep).
- **ВАЖНО при неинтерактивном запуске** (фон, `curl | bash` без терминала):
  установщик читает `/dev/tty` и **виснет на sudo-вопросе про ripgrep/ffmpeg**.
  Запускать в сеансе без управляющего терминала (`setsid`) и с флагами
  `--skip-setup --skip-browser`, либо просто ставить в живом SSH-терминале.

Если в системе старый Node — поставить 20 через nvm (без sudo):

```bash
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"
nvm install 20 && nvm alias default 20
# затем пересобрать веб-морду дашборда:
cd ~/.hermes/hermes-agent/web && rm -rf node_modules package-lock.json && npm install && npm run build
```

### Подключение аккаунта ChatGPT (openai-codex, OAuth device-code)

```bash
hermes auth add openai-codex --type oauth
```

- Покажет URL `https://auth.openai.com/codex/device` и короткий код.
- В браузере сначала **войти в аккаунт ChatGPT** (страница перекинет на `/log-in`),
  потом **снова открыть** `/codex/device`, ввести код, подтвердить (Authorize).
- Аккаунт должен быть **Plus/Pro** — на бесплатном будет `usage limit`.
- Токен сохраняется в `~/.hermes/auth.json`. Проверка: `hermes auth list`.
- **IP-нюанс**: вход с датацентрового IP Cloudflare может блокировать (`403`).
  На ПК (через VPN-Эстонию) сработало. На сервере вход может не пройти — см. перенос.

### Провайдер и модель по умолчанию

```bash
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5      # или gpt-5.4; интерактивно: hermes model
# проверка:
printf '' | hermes -z "Respond with exactly: PING-OK"
```

### Смена аккаунта / провайдера

Для сервера `217.198.12.236` добавлен быстрый локальный менеджер аккаунтов Hermes/Codex:

```powershell
.\scripts\hermes-codex-accounts.cmd          # double-click/launcher for Windows
.\scripts\hermes-codex-accounts.ps1          # меню: список, импорт текущего Codex, активация
python scripts/hermes_codex_accounts.py --target new list
python scripts/hermes_codex_accounts.py --target new import-current
python scripts/hermes_codex_accounts.py --target new activate 2
python scripts/hermes_codex_accounts.py --target new ensure-failover
```

Что делает `import-current`: читает локальный `%USERPROFILE%\.codex\auth.json`, конвертирует
его в `openai-codex` credential для `/root/.hermes/auth.json`, делает бэкап в
`/root/.hermes/auth-backups/`, ставит импортированный аккаунт priority `0` и перезапускает
`hermes-gateway`. Токены не передаются в аргументах командной строки; запись идёт через SFTP.
`ensure-failover` выставляет `credential_pool_strategies.openai-codex: fill_first`: Hermes
использует аккаунт #1 до лимита, при `usage limit`/429 помечает его exhausted и автоматически
ротирует на следующий доступный аккаунт в пуле.
После смены аккаунта в активном Telegram-чате с Hermes написать `/reset`, чтобы сессия
подтянула новый credential.

```bash
hermes auth list                       # что подключено
hermes auth logout openai-codex        # выйти из аккаунта
hermes auth remove <index|id|label>    # удалить конкретный кредл
hermes auth add openai-codex --type oauth   # войти заново (другим аккаунтом)
```

Переключиться на **API-ключ** (без потолка лимитов, платно по токенам):

```bash
hermes auth add openai --type api-key --api-key sk-...     # или anthropic / gemini
hermes config set model.provider openai                    # anthropic | gemini
hermes config set model.default <model-id>
```

Весь токен-стор — один файл `~/.hermes/auth.json` (его можно бэкапить/копировать).

### Запуск

```bash
hermes                       # чат в терминале
hermes dashboard --tui       # веб-дашборд: чат + настройки + сессии + cron, порт 9119
#   полезные флаги: --no-open  --port N  --skip-build (отдать готовый dist без сборки)
#                   --status   --stop
hermes gateway run           # фоновый шлюз/cron (для «сотрудника»); install — как сервис
```

Дашборд слушает `127.0.0.1:9119`; при mirrored-WSL открывается в браузере Windows
по `http://localhost:9119`.

### Перенос на прод-сервер (`186.246.7.32`, Ubuntu 22.04)

1. Установить (Node 20 там уже есть):
   `curl -fsSL .../install.sh | bash` (в живом SSH-терминале — TTY-хак не нужен).
2. **Логин аккаунта** — упрётся в датацентровый IP (как было с Codex). Два пути:
   - **(а) device-login:** на сервере `hermes auth add openai-codex --type oauth`,
     а URL+код открыть/ввести в браузере на ПК (жилой IP). Если опрос токена с
     сервера получит `403` — использовать путь (б).
   - **(б) скопировать готовый `~/.hermes/auth.json` с ПК на сервер** (как делали с
     `~/.codex/auth.json` для Codex): `scp ... root@186.246.7.32:/root/.hermes/auth.json`,
     `chmod 600`. Тогда отдельный вход на сервере не нужен.
3. Прописать провайдера/модель (`hermes config set ...`, см. выше).
4. Держать запущенным: `hermes gateway install` (systemd-сервис, автозапуск) или
   дашборд как сервис.
5. VPN на сервере уже заворачивает исходящий трафик через Эстонию (см. раздел про
   VPN-шлюз) — он нужен, иначе OpenAI отдаёт `403` российскому IP.

### Что нужно для работы (чек-лист)

- **Node 20+** (дашборд) и Python 3.11 (ставит установщик).
- **Рабочий мозг**: `openai-codex` (ChatGPT Plus) или API-ключ.
- **Нероссийский исходящий IP** (VPN) — OpenAI режет РФ.
- Для роли «сотрудник по отчётам» (следующий этап): подключить **MCP Albery**
  (секция `mcp_servers` в `~/.hermes/config.yaml`, HTTP-транспорт на
  `https://mcp.m4s.ru/mcp/<MCP_SHARED_SECRET>`) и настроить **cron-задачи**
  (`hermes cron`) — тогда агент сам по расписанию читает инструкции, собирает
  данные и формирует отчёты через инструменты Albery.

### Служебное (на ПК)

- `C:\Users\<user>\.wslconfig` — mirrored-сеть WSL (не удалять, иначе WSL снова
  потеряет интернет под VPN).
- Разовые вспомогательные скрипты установки лежали в `C:\Users\<user>\*.sh` —
  их можно удалить, на работу агента не влияют.

### Прод-развёртывание Hermes (выполнено 2026-05-27)

Hermes перенесён с ПК на прод-сервер `186.246.7.32` и работает **24/7** как
systemd-служба. Мозг — ChatGPT Plus (`gpt-5.5`) через `openai-codex` OAuth.
Чтобы не сжигать 5-часовой лимит Codex, reasoning на проде снижен до `medium`:
`model.reasoning_effort=medium` и `agent.reasoning_effort=medium`.

Расположение на сервере:

```text
бинарь:   /usr/local/bin/hermes
код:      /usr/local/lib/hermes-agent
дом:      /root/.hermes/   (config.yaml, .env, cron/, sessions/, logs/, state.db)
служба:   /etc/systemd/system/hermes-gateway.service  (enabled+active, автозапуск)
```

Что сделано:

- **Вход в ChatGPT:** `/root/.hermes/auth.json` скопирован с ПК (chmod 600) — вход
  на серверном IP блокирует Cloudflare, а готовый токен работает через VPN-Эстонию.
- **Swap:** добавлен `/swapfile` 2 ГБ (`vm.swappiness=10`, в `/etc/fstab`) — страховка
  от OOM на 2 ГБ RAM. Сам агент лёгкий (~185–270 МБ), модель считается удалённо.
- **MCP:** в `/root/.hermes/config.yaml` секция `mcp_servers.albery` =
  `https://mcp.m4s.ru/mcp/<MCP_SHARED_SECRET>` (секрет из `/var/www/albery/.env`,
  auth none). 38 инструментов. TZ сервера = Europe/Moscow, поэтому cron-время — МСК.
- **Gateway-служба:** `hermes gateway install --system --run-as-user root`
  (под root, т.к. весь стек тут под root). Планировщик cron работает автоматически.
- **Telegram:** подключён к gateway через `/root/.hermes/.env`:
  `TELEGRAM_BOT_TOKEN=<из .env TG_BOT_TOKEN>` и
  `TELEGRAM_ALLOWED_USERS=<из .env TG_ID>`. Установлена зависимость
  `python-telegram-bot[webhooks]` в `/usr/local/lib/hermes-agent/venv`.
  Пользователь нажал `/start`, после этого проверочный пуш через
  `hermes send --to telegram:<TG_ID> ...` вернулся `sent`.
- **Тихий Telegram-режим:** в `/root/.hermes/config.yaml` включено
  `display.platforms.telegram.tool_progress: off` — Telegram не показывает
  технические tool-calls вида `mcp_albery_*`; и `cron.wrap_response: false` —
  cron присылает только чистый ответ агента без обёртки `Cronjob Response`,
  `job_id` и подсказки `stop reminder`.

Две автоматизации (`hermes cron list`):

- `zoom-to-tasks` — `*/30 * * * *`: находит Zoom-созвоны без отчёта
  **без расхода Codex на пустых проверках**. Реализовано как `no-agent` cron
  со скриптом `/root/.hermes/scripts/zoom_watchdog.sh`: скрипт напрямую и быстро
  проверяет PostgreSQL (`zoom_calls` за последние 2 дня, `analytical_note=''`,
  транскрипт есть). Если новых Zoom нет — stdout пустой, Telegram молчит, LLM не
  вызывается. Если есть новый Zoom — только тогда скрипт запускает `hermes -z` с
  промптом из `/root/.hermes/scripts/hermes_zoom_to_tasks_prompt.txt`
  (источник правды в git: [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt)).
  Промпт подставляет `$DATE_FROM`, `$DATE_TO`, `$MISSING` через awk-substitution
  (без проблем со sed-escaping для многострочных значений).
  В скрипте есть `flock` и cooldown 7200 сек на тот же набор missing-call id,
  чтобы при ошибке не жечь лимит каждые 30 минут.

  **Что делает агент.** По промпту строго:
  1. `start_here_always_read_ai_instructions` → `get_context_guide`;
  2. для каждого созвона: `get_report_contract(zoom_processing)` (контракт — 13 KB, 12 разделов в `report_text` + JSON-схема с обязательным `operational_tasks`), `get_zoom_call_transcript(include_full_text=true)`, `get_org_structure`;
  3. формирует отчёт **строго по контракту** (12 разделов + полный JSON) и сохраняет через `save_zoom_call_report` — это кладёт `analytical_note` и `raw_json.ai_report.analysis.operational_tasks`;
  4. в Битрикс задачи НЕ создаёт (verification mode).

  **Что приходит в Telegram (формат принципиально короткий).** Никакого пересказа отчёта, никаких разделов «Краткая суть» / «Риски» / «Выводы»:
  ```
  Созвон: <ДД.ММ.ГГГГ> — <тема>

  Предлагаю поставить задачи в Битрикс:
  1. <ФИО> — <task_text>. Срок: <deadline_text>. Критерий: <result_criteria>.
  2. …

  Создаём задачи в Битрикс? Ответь «ставь» — я по каждому ответственному создам одну агрегированную задачу «Итоги созвона <ЧЧ:ММ>» с дедлайном <дата созвона> 19:00 МСК и описанием со списком всех его задач из созвона (формат как в Albery UI). «Не ставь» — пропускаю. «Правки по №<n>: <текст>» — пересоберу конкретную.
  ```
  Если задач 0 — строка «Задач не выделено.» и финальный вопрос не задаётся. Если обработано несколько созвонов — каждый отдельным блоком через разделитель «———».

  Полный отчёт по контракту (краткая суть, риски, поведенческие факторы, диагностика и т.д.) живёт **только в БД** (`analytical_note` + `raw_json.ai_report.analysis`) и доступен через UI Albery / MCP `get_zoom_call_transcript`. В Telegram он не дублируется.

  **На ответ «ставь» (Phase 2 — отправка в Битрикс).** Hermes в Telegram-сессии **НЕ создаёт по одной мелкой задаче через `create_bitrix_task`** — он использует existing UI dispatcher (тот же код, что и кнопка «Отправка задач» в Albery UI):
  1. `list_pending_zoom_operational_dispatches()` без аргументов — возвращает массив `pending` ТОЛЬКО за сегодня (Europe/Moscow). Это именно те созвоны, которые владелец видел в недавней сводке.
  2. Для каждого `pending` → `dispatch_zoom_operational_tasks(call_id, confirm=true)`. Этот инструмент сам сгруппирует `operational_tasks` по ответственному, создаст **одну агрегированную Bitrix-задачу** «Итоги созвона ЧЧ:ММ» на каждого человека с описанием через стандартный intro `Ознакомьтесь со списком выделенных из созвона задач и поставьте себе самые важные в Битрикс…` + нумерованный список этого человека.
  3. После успешной отправки бэкенд помечает `zoom_calls.raw_json.ai_report.bitrix_dispatch` (timestamp + task_ids) → следующий `list_pending` для того же дня уже не вернёт этот созвон.
  4. Hermes отвечает владельцу короткой человеческой сводкой («Создано M задач в Битрикс по созвону <тема>: — ФИО (N задач)»), без техн id, MCP, прочей кухни.

  Правило поведения на «ставь» зафиксировано отдельной AI-инструкцией в Albery («Cron автоматизации/Zoom задачи — ответ ставь», источник в git: [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md)). Hermes читает её через `start_here_always_read_ai_instructions` в начале Telegram-сессии. Деплой инструкции — `python scripts/upsert_albery_ai_instruction.py "<path>" scripts/ai_instruction_zoom_approval.md`.

  Жёсткие правила в этой AI-инструкции (важны чтобы Hermes не сжигал токены и не делал лишнего):
  - НЕ переспрашивай «3 обязательных поля» — у `dispatch_zoom_operational_tasks` все поля собираются из БД автоматически.
  - НЕ вызывай `create_bitrix_task` для отдельных задач — это создаёт много мелких задач вместо одной агрегированной.
  - НЕ ищи `call_id` вручную через `list_zoom_calls`/`get_zoom_call_transcript` — `list_pending_zoom_operational_dispatches` уже отфильтровал нужное.
  - НЕ читай `get_org_structure`, `get_zoom_call_transcript`, `get_report_contract` — dispatch сам всё подтянет из БД.
  - На «не ставь» — ничего не создавай, отвечай «Понял, задачи не ставлю.».
  - На «правки по №N: …» — `dispatch_zoom_operational_tasks` не вызывай; режим редактирования отдельной задачи пока не автоматизирован, обсуди с владельцем устно.

  **Деплой обновлённого промпта/watchdog'а**:
  ```powershell
  python scripts/update_hermes_zoom_to_tasks.py
  # Опции:
  #   --reset-and-run <zoom_call_uuid>
  #     дополнительно: удалит сохранённый отчёт за этот созвон через MCP
  #     delete_zoom_call_report, сбросит cooldown, и запустит watchdog один раз
  #     через bash (для разработки; в проде используйте `hermes cron run f217482a8618`
  #     если нужна реальная cron-delivery в Telegram).
  ```
  Источники правды в git:
  - [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt) — текст промпта (на проде: `/root/.hermes/scripts/hermes_zoom_to_tasks_prompt.txt`);
  - [scripts/hermes_zoom_watchdog.sh](scripts/hermes_zoom_watchdog.sh) — wrapper (на проде: `/root/.hermes/scripts/zoom_watchdog.sh`, права 0700);
  - [scripts/update_hermes_zoom_to_tasks.py](scripts/update_hermes_zoom_to_tasks.py) — патчер.
  - [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md) — AI-инструкция Albery для Telegram-сессии.
  - [scripts/upsert_albery_ai_instruction.py](scripts/upsert_albery_ai_instruction.py) — общий патчер AI-инструкций через MCP `upsert_ai_instruction`.
  Бэкап предыдущего watchdog'a: `/root/.hermes/scripts/zoom_watchdog.sh.bak`.
- `owner-daily` — `0 18 * * *`: формирует и сохраняет ежедневный отчёт собственнику
  по контракту `get_report_contract(owner_daily)`. **На уровне prompt самого Hermes**
  (не MCP-инструкций — контракт `owner_daily` НЕ трогали) включён двухфазный
  режим согласования рекомендаций → отправка в Битрикс.

  **Фаза 1 — формирование (cron в 18:00 МСК).** Hermes:
  1. читает живые AI-инструкции, контракт `owner_daily`, источники за день (чаты с OCR, Zoom-отчёты, Bitrix-задачи, оргструктуру, регламенты, предыдущий owner-отчёт);
  2. вызывает `save_owner_daily_report` и **дополнительно передаёт** аргумент `manager_messages` — массив адресных сообщений ТОЛЬКО для пятёрки (Сергей Виноградов, Наталья Горюнова, Артур Степанян, Евгений Палей, Александр Никитенко). В каждом `message_text` уже лежит ПОЛНЫЙ финальный текст в формате «<Имя>, приветствую! Рекомендации: 1) … 2) …», который пойдёт в Битрикс одной репликой;
  3. для Евгения Палея (собственник) в начало `message_text` добавляется блок «Главный вывод дня — <2-3 строки executive summary>»;
  4. на стороне MCP `tool_save_owner_daily_report` после INSERT в `owner_daily_reports` вызывает `save_owner_daily_manager_messages` (в `app.py`), который парсит `manager_messages` и пишет каждое сообщение строкой в `owner_manager_recommendations` со `status='new'`;
  5. для **НЕ-разрешённых** сотрудников рекомендации в `manager_messages` НЕ передаются вообще — наблюдения по ним остаются только в `report_text/recommendations` отчёта;
  6. **если для пятёрки за день нет фактов-оснований** (нет созвонов/чатов/ответов/просрочек) — `manager_messages` пустой, в БД ничего не записывается, и Hermes возвращает **пустой stdout** → Telegram молчит вообще (правило тишины, как у `zoom-to-tasks` при отсутствии новых созвонов);
  7. если хоть один блок есть — Hermes собирает единое сообщение и присылает мне в Telegram:
     ```
     Согласуйте что мы отправляем:

     Евгений, приветствую!
     Главный вывод дня — …
     Рекомендации: 1) … 2) …

     ———

     Сергей, приветствую!
     Рекомендации: 1) …

     Отправляю в Битрикс? Ответь: отправляй / не отправляй / правки по <имя>: <текст>.
     ```

  **Фаза 2 — отправка в Битрикс (ответ владельца в Telegram).** На «отправляй»
  Hermes в новой Telegram-сессии:
  1. `list_pending_owner_recommendations(report_date=today)` — читает сохранённые черновики из `owner_manager_recommendations` (статус `new`);
  2. собирает `recipient_recommendations = {manager_bitrix_user_id: recommendation_text}` строго как есть (тексты уже финальные и одобренные);
  3. `send_owner_recommendations_to_bitrix(report_date, recipient_recommendations, confirm=true)` → backend (`send_owner_report_recommendations_to_bitrix` в `app.py`) шлёт каждому через **`im.message.add` от моего имени** (через существующий `BITRIX_WEBHOOK_BASE`, отдельного бота пока не делаем) с fallback на `im.notify.personal.add` при `ERROR_NO_ACCESS`;
  4. факт отправки пишется в `owner_recommendation_dispatches` (channel `bitrix_im` или `bitrix_notification`), статус соответствующих `owner_manager_recommendations` обновляется на `sent`, в `owner_recommendation_events` фиксируется событие `sent`;
  5. на «правки по <имя>: …» — Hermes пересобирает текст для этого человека и снова показывает на согласование (старый черновик можно пометить `cancel_owner_recommendation(recommendation_id, reason)`);
  6. на «не отправляй» — отметка статусов `cancelled`, ничего в Битрикс не уходит.

  Сценарий полностью автоматизированный — отдельного «Альбери Бота» в Bitrix пока нет, сообщения идут от моего пользователя через тот же webhook, что и `create_bitrix_task`. Когда добавим отдельного бота (Phase 2), достаточно будет переключить `send_owner_report_recommendations_to_bitrix` на новый webhook.

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
polling, поэтому отдельный webhook/Nginx не нужен. Для проверки логов:
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

Current `217.198.12.236` values as of 2026-05-30:

- `session_reset.idle_minutes=30`: if Telegram is quiet for 30 minutes, the next message starts a fresh session.
- `telegram_context_guard.token_threshold=50000`: before running the model on a large Telegram session, gateway asks whether to compress old context and then continue with the original message.
- `telegram_context_guard.message_limit=80`: extra safety valve for very long chats even if token estimate is unavailable.
- Context guard buttons: `Compress and continue` (`Сжать и продолжить`) sends visible Telegram chat messages `Сжимаю контекст...` before `/compress` and `Контекст сжат, думаю, как ответить на ваше сообщение...` after successful compression, suppresses the raw technical `/compress` result, then repeats the original message. `Continue without compression` (`Продолжить без сжатия`) runs the original message once without compression.
- Persistence: context-guard UX is re-applied on every gateway start by `/root/.hermes/patches/context_guard_ux_patch.py` via `/etc/systemd/system/hermes-gateway.service.d/30-context-guard-ux.conf`.
- Backs up before server patches: `/usr/local/lib/hermes-agent/gateway/run.py.bak.<stamp>`, `/usr/local/lib/hermes-agent/gateway/platforms/telegram.py.bak.<stamp>`, `/root/.hermes/config.yaml.bak.<stamp>`.

Hermes task time budgets on `217.198.12.236` as of 2026-05-29:

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


### Дорожная карта: внедрение Hermes в компанию + RBAC по ролям (план, не выполнено)

Обсуждено 28.05.2026. Сейчас Hermes на проде — **один инстанс, один Telegram-бот, один MCP-секрет**, `TELEGRAM_ALLOWED_USERS=<TG_ID владельца>`. Это работает для владельца, но **не масштабируется** на менеджеров/сотрудников.

**Ограничение Hermes:** `hermes tools list --platform telegram` задаёт toolset на **всю платформу**, не на отдельного TG-пользователя. Внутри одного бота сделать «владельцу всё, менеджеру половину, сотруднику только read» **нельзя нативно** — только soft-RBAC в AI-инструкции, который модель может «забыть» после `/compress`. Для Bitrix-write это недопустимо.

**Целевая архитектура (3 тира, расширение существующего FAQ MCP):**

```
Albery backend (один)
├── /mcp/<MCP_SHARED_SECRET>         → 45 tools (full)          → hermes-owner   (твой TG)
├── /mcp-manager/<MCP_MANAGER_SECRET> → ~20 tools (read + своя
│                                       зона, без im.message,
│                                       без dispatch, без delete) → hermes-manager (5 TG)
└── /mcp-faq/<MCP_FAQ_SHARED_SECRET> → 12 tools (read-only,
                                       уже работает)             → hermes-staff   (все TG)
```

Каждый Hermes — отдельный systemd-юнит в `/root/.hermes-<role>/` со своим `auth.json`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, своей `state.db`/памятью. Cron-джобы (`zoom-to-tasks`, `owner-daily`) остаются **только у owner-инстанса**.

**Цена:** RAM ~250 МБ × 3 = 750 МБ (на 2 ГБ + swap 2 ГБ — тянет). Codex-лимит делится поинстансно → лучше отдельные ChatGPT Plus подписки на инстанс с реальной нагрузкой. Иначе все три инстанса будут конкурировать за один 5-часовой лимит.

**Шаги внедрения (в этом порядке):**

1. **Расширить MCP до manager-эндпоинта.** В [mcp/context_server.py](mcp/context_server.py) добавить третью точку входа `/mcp-manager/<secret>` рядом с `/mcp/` и `/mcp-faq/` (по аналогии с тем, как сделан FAQ — см. [agent.md:608-626](agent.md#L608-L626)). Toolset для менеджера: `search_tasks`, `get_task_comments`, `search_zoom_transcripts`, `get_zoom_call_transcript`, `search_company_knowledge`, `get_company_file`, `list_chats`, `search_messages`, `get_chat_transcript`, `get_org_structure`, `get_context_guide`, `start_here_always_read_ai_instructions`, `health`, `list_available_sources`. **Не давать** менеджеру: `create_bitrix_task`, `delete_bitrix_task`, `dispatch_zoom_operational_tasks`, `send_bitrix_message`, `send_owner_recommendations_to_bitrix`, `save_*_report`, `delete_zoom_call_report`, `upsert_ai_instruction`, `process_chat_ocr`, `cancel_owner_recommendation`.
2. **Поднять `hermes-manager` инстанс.** Отдельный `/root/.hermes-manager/`, отдельный бот в BotFather, `TELEGRAM_ALLOWED_USERS` = TG-id 1-2 менеджеров для пилота. Без cron. Прицепить только `/mcp-manager/`. Свой `auth.json`, желательно отдельный ChatGPT-аккаунт.
3. **Обкатать 1-2 недели** на пилотной паре менеджеров. AI-инструкция для manager-MCP — отдельный документ в Albery «Hermes для менеджера: что можно делать», читается через `start_here_always_read_ai_instructions` каждой сессией.
4. **Если зайдёт — открыть `hermes-staff`** через уже существующий `/mcp-faq/` (12 tools, регламенты + Zoom-расшифровки + оргструктура). Третий бот, ширим на всех сотрудников.

**Чего НЕ делать:** не давать сотрудникам MCP-секрет напрямую (только через серверного Hermes-бота); не публиковать секреты в клиентском коде; не запускать второй планировщик cron-джоб против того же Albery (версионная чехарда отчётов — см. [agent.md:1621-1624](agent.md#L1621-L1624)).

**Альтернатива «попроще» (1 инстанс + soft-RBAC):** оставить один Hermes, в AI-инструкции вшить «если `sender_tg_id ∈ {X, Y}` — нельзя `dispatch_*`, `send_bitrix_message`, `delete_bitrix_task`, `send_owner_recommendations_to_bitrix`». Дёшево, но **это не безопасность** — модель может проигнорировать после сжатия контекста. Годится для UX-разделения «не показывай менеджеру owner-команды», не для защиты от злого умысла.

### Обучение Hermes (где править поведение, по убыванию силы)

| Уровень | Источник правды | Кто читает | Деплой |
|---|---|---|---|
| Контракт отчёта (структура секций + JSON-схема) | Albery UI → `Сводная аналитика → Настройка промтов` (`zoom_processing`, `owner_daily`) | Все — Hermes, внешние ассистенты | Сохранение в UI = live |
| AI-инструкции (правила поведения) | Albery UI → `Настройки → Инструкции для ИИ` + git: [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md) | Hermes через `start_here_always_read_ai_instructions` в начале сессии | `python scripts/upsert_albery_ai_instruction.py <path> <file>` |
| Cron-промпт (что делает одна джоба) | git: [scripts/hermes_zoom_to_tasks_prompt.txt](scripts/hermes_zoom_to_tasks_prompt.txt), [scripts/hermes_owner_daily_prompt.txt](scripts/hermes_owner_daily_prompt.txt) | Только эта cron-джоба | `python scripts/update_hermes_*_prompt.py` → restart gateway |
| Память Hermes (личные предпочтения) | `/root/.hermes/state.db` через `hermes memory` или «запомни: …» в Telegram | Hermes везде, в рамках инстанса | Live |

**Правило большого пальца:** что должно быть у всех (формат отчёта, состав пятёрки, что считать срочным) → **контракт/AI-инструкции в Albery**. Что специфично для одной cron-джобы (cooldown, формат Telegram-сводки) → **cron-промпт в git**. Личные предпочтения владельца → **`hermes memory`**.

**Болевая точка** из ретро [agent.md:1545-1549](agent.md#L1545-L1549): обучать **жёсткими запретами** в AI-инструкции, а не уговорами. Пример из [scripts/ai_instruction_zoom_approval.md](scripts/ai_instruction_zoom_approval.md): «НЕ вызывай `create_bitrix_task` / НЕ читай `get_org_structure`» — это спасло Codex-лимит. Без таких запретов Hermes идёт в `search_files` и сжигает 100k токенов.



### Фикс падения Hermes `NameError: name 'event'` + команды `/accounts` `/limits` + авто-переприменение правок (29.05.2026)

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
ssh root@217.198.12.236 'bash /root/.hermes/patches/update.sh'
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
