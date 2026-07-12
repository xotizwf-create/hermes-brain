---
id: albery-web-browsing
type: project
project: albery
tags: [albery, hermes, browser, web-search, tools]
updated: 2026-07-12
---

# Albery — браузер и поиск в интернете у агентов (186.246.7.32)

Включено 2026-07-12 по просьбе владельца: агенты на выделенном Albery-сервере умеют
искать в интернете и работать в браузере.

## Что стоит и как устроено

- **Google Chrome 150** (`/usr/bin/google-chrome`, официальный .deb, как на 217).
  Движок Hermes (`browser: engine: auto` в `/root/.hermes/config.yaml`) находит его в PATH;
  браузер поднимается на время задачи и сам гаснет по бездействию (`inactivity_timeout: 120`).
- **Toolset `browser` уже был включён** в Hermes 0.17 — не хватало только бинаря Chrome.
  `web` (web_search) тоже включён и работает.
- **Главный агент (hermes-gateway, TG владельца):** браузер+поиск доступны из коробки.
- **Второй агент @Albery_AI2_Bot (albery-tg.service):** toolsets задаются env
  `TG_AGENT_TOOLSETS`; добавлен systemd drop-in
  `/etc/systemd/system/albery-tg.service.d/browser.conf` → `albery,web,browser`.
  Убрать браузер у бота = удалить drop-in + `daemon-reload` + рестарт.
- **Инструкция агенту** — секция «Поиск в интернете» в `/root/.hermes/SOUL.md`
  (подгружается свежей на каждое сообщение, рестарт не нужен): web_search → открыть
  1-3 результата; browser_navigate+browser_snapshot для страниц; fetch_url (MCP) для
  статичных страниц/документов; владельцу — результат по-русски без технических деталей.
  Бэкап: `/root/.hermes/SOUL.md.bak-20260712`.

## Проверено боем (2026-07-12)

- `hermes -z` (полный набор): `browser_navigate`+`browser_snapshot` → `BROWSER-OK: Example Domain`.
- `hermes -z -t albery,web,browser --yolo` (как вызывает tg_agent): `BROWSER-T-OK`.
- `web_search`: `SEARCH-OK: bitrix24.ru`.
- После рестартов `hermes-gateway`, `albery-tg`, `albery` — active; ExecStartPre-патчи
  (provider_error, media_rescue, mcp_resilience) — «already applied».

## Память/ресурсы (2 ГБ RAM + 2 ГБ swap)

Перед включением: available ~792 МБ — Chrome (~300 МБ на сессию) помещается.
Правило прежнее (`engineering/server-preflight.md`): перед тяжёлыми операциями
`free -m`; браузер живёт только на время задачи. Если станет тесно — смотреть,
не висит ли Chrome дольше `inactivity_timeout`.

## Откат

1. Drop-in бота: `rm /etc/systemd/system/albery-tg.service.d/browser.conf && systemctl daemon-reload && systemctl restart albery-tg`.
2. SOUL.md: вернуть из `.bak-20260712`.
3. Chrome: `apt remove google-chrome-stable` (toolset browser сам перестанет предлагаться — бинаря нет).
