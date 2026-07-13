---
id: albery-web-browsing
type: project
project: albery
tags: [albery, hermes, browser, web-search, tools]
updated: 2026-07-13
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
- **Битрикс-агенты (все: юрист, финансист, склад, новостной, main…):** браузер включён
  ВСЕМ по умолчанию 2026-07-12. Механика: `b24bot.py` собирает toolsets как
  `<mcp-коннектор агента> + $B24_EXTRA_TOOLSETS` (дефолт был `web`); drop-in
  `/etc/systemd/system/albery.service.d/browser.conf` → `B24_EXTRA_TOOLSETS=web,browser`.
  Изоляция не изменилась: terminal/file/exec у битрикс-агентов по-прежнему ВЫКЛЮЧЕНЫ,
  `allow_private_urls: false` не пускает браузер во внутренние адреса. Рестарт `albery`
  делался при `bitrix_inflight_turns = 0`. Проверено: `hermes -z -t agent-main,web,browser`
  → `B24-BROWSER-OK`. Откат: удалить drop-in + daemon-reload + рестарт при inflight=0.
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

## 2026-07-13 — российские сайты, карточки WB и xlsx-выгрузки (инцидент с Софьей)

Софья (техисполнитель WB) попросила сравнить две карточки WB и проанализировать
xlsx-выгрузку «Воронка продаж» — агент 10 минут долбил заблокированные страницы и
извлёк из файла 223 символа (названия листов). Корни и фиксы (Albery `69d1028`,
модуль `/var/www/albery/webread.py`, бэкапы `/root/albery-backups-20260713/`):

1. **RU-сайты режут VPN-выход** (весь egress идёт через Эстонию `95.85.243.43`:
   rbc.ru→401, WB→498). Фикс: `fetch_url` при блокирующих кодах (401/403/…/498)
   и при 200-заглушке повторяет запрос **напрямую с российского интерфейса**
   (`SO_BINDTODEVICE eth0`, прямой IP 186.246.7.32 = Москва/Timeweb; VPN и
   маршрутизация не трогаются). Порядок: VPN → прямой RU → reader-прокси.
   Кил-свитчи: `FETCH_URL_DIRECT=0`, интерфейс `FETCH_URL_DIRECT_IFACE`.
2. **Wildberries закрыт антиботом по ASN** (498 с обоих маршрутов, r.jina.ai тоже
   не пробивает, Chrome получает JS-челлендж). Фикс: ссылки `wildberries.ru/catalog/<nm>`
   `fetch_url` отвечает из **открытого CDN** `basket-NN.wbbasket.ru` (card.json +
   price-history.json) + рейтинг из `feedbacks1/2.wb.ru` → kind=`wb-card`: название,
   бренд, цена с историей (последняя точка = актуальная; витрина чуть ниже на скидку
   WB-кошелька), рейтинг/отзывы, цвета, фото-URL, все характеристики, описание.
   Номер basket-хоста ищется интерполяцией + перебором (кэшируется по vol).
   Кил-свитч: `FETCH_URL_WB_CARD=0`. Текущую витринную цену/остатки CDN не отдаёт —
   агент честно предупреждает в note.
3. **xlsx-выгрузки WB/1С пишут строки без `r=`-индексов** — openpyxl в `read_only`
   видит 1 строку на лист. Фикс: `webread.extract_xlsx` = read_only-проход, и если
   результат <1500 симв. — потоковый разбор XML листов (stdlib, память O(строка),
   inline strings поддержаны). Подключён в оба экстрактора: `b24bot._b24_extract_document`
   (вложения в чате) и `context_server._extract_binary_document` (fetch_url по ссылке).
   Файл Софьи: 223 → 7497 символов; запись в `bitrix_bot_attachments` обновлена задним числом.
4. SOUL.md (секция «Поиск в интернете», hot-reload): ссылки WB → сразу fetch_url,
   не мучить браузер; бэкап `SOUL.md.bak-20260713`.

Проверено боем: живой ход `hermes -z ... -t albery` по карточке 791046510 → «387 ₽,
рейтинг 4,9/5»; lenta.ru — прямой маршрут 141 КБ HTML; RBC отдаёт ботам пустую
заглушку с любого IP → честная ошибка (не галлюцинация). Рестарт `albery.service`
делался скриптом `/root/restart_idle.sh` (ждёт `bitrix_inflight_turns=0`).

Откат: `cp /root/albery-backups-20260713/* ...` (или `git revert 69d1028`) + рестарт
при inflight=0; SOUL.md из `.bak-20260713`; кил-свитчи выше — без рестарта.
