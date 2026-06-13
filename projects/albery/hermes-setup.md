---
id: albery-hermes-setup
type: project
project: albery
tags: [albery, hermes, codex, install, deploy, accounts, reference]
updated: 2026-06-13
secret_refs: [proj/albery/ssh/root]
---

# Hermes — установка, аккаунты, деплой

> Извлечено из `hermes.md` при разбиении монолита по темам (2026-06-13). Сосед­ние документы: [hermes.md](hermes.md) (хаб), [hermes-setup.md](hermes-setup.md), [hermes-automations.md](hermes-automations.md), [hermes-operations.md](hermes-operations.md).

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
