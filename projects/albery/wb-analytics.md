---
id: albery-wb-analytics
type: project
project: albery
tags: [albery, wildberries, analytics, wb-api, dashboard]
updated: 2026-07-16
secret_refs: [proj/albery/wb/analytics-token]
---

# Albery — сервис аналитики WB (вкладка «WB-кабинет»)

Старт 2026-07-16 (владелец). Цель: полноценная аналитика кабинета Wildberries внутри Albery UI +
инструменты для ИИ-агента. Разделы: **Общий дашборд · РНП · ОПиУ · ДДС · По артикулам ·
Налоговый калькулятор**. Фильтры по бренду (в кабинете два: **Allberi, Arintela**). История ~полгода,
дальше — непрерывная синхронизация. Референсы владельца: скрины стороннего сервиса (таблица
артикулов с динамикой остатков/заказов по дням; налоговый калькулятор с Реализация/Услуги/
Налоги и затраты/Операционная прибыль).

## Ключ и доступ
- Токен в `/var/www/albery/.env` → `WB_ANALYTICS_TOKEN` (600, вне git; бэкап `.env.bak-wbkey-*`).
  Продавец: ООО «АЛБЕРИ», ИНН 2312330583, oid 4328220. Полный (НЕ read-only) доступ, **exp 15.01.2027**
  — поставить напоминание о ротации к декабрю 2026. Значение нигде не печатать.
- Заголовок: `Authorization: <token>` (без Bearer).
- **17.07.2026 (задача 1678): ключ заменён на ПЕРСОНАЛЬНЫЙ** (JWT-клейм `acc=3`; старый был
  «базовый» `acc=1` с редчайшей квотой финотчёта — Retry-After до 11,5 ч). Тот же продавец,
  exp 15.01.2027 (окно ротации прежнее — декабрь 2026). Бэкапы: `.env.bak-wbkey2-20260717_1619`
  (базовый ключ), `.env.bak-wbkey-20260716_1911`. `wb_cabinet.py` сам различает тип по `acc`:
  персональный/сервисный → до 20 минутных страниц финотчёта за тик, базовый → 1. Замена без
  рестарта `albery.service` (тик = отдельный процесс с `load_dotenv`); после замены сброшены
  `blocked_until` в `wb_sync_state`. Владелец кладёт новые ключи в локальный `.env` мозга
  (`Albery_API_WB_KEY_Personal`); на прод — файлом, не через argv.

## Разведка API (боевая, 16.07.2026, задача 1606)
| Контур | Статус | Что отдаёт |
|---|---|---|
| statistics `/api/v1/supplier/stocks` | ✅ 200 | остатки по складам: nmId, barcode, brand, subject, qty, inWayTo/From, Price |
| statistics `/api/v1/supplier/orders` | ✅ 200 | заказы: date, nmId, brand, гео (область/регион), склад, цены |
| statistics `/api/v1/supplier/sales` | ✅ 200 | выкупы/возвраты: forPay, priceWithDisc, spp |
| statistics v5 `reportDetailByPeriod` | ✅ 200 | финотчёт-строки: retail_amount, ppvz_for_pay, delivery_rub, storage_fee, penalty, deduction, acquiring_fee, комиссия, doc_type, supplier_oper_name — базис ОПиУ/ДДС/налогов |
| content v2 `cards/list` | ✅ 200 | карточки: nmID, vendorCode, brand, title, фото — справочник |
| prices `goods/filter` | ✅ 200 | текущие цены/скидки по размерам |
| advert `promotion/count` | ✅ 200 | 399 кампаний; затраты — через `upd`/`fullstats` |
| seller-analytics `paid_storage` | ✅ 202 | async-task (taskId → download) — хранение посуточно |
| seller-analytics `nm-report/detail` | ❌ 404 | путь устарел — воронку строим из orders + снапшоты stocks; уточнить актуальный путь в доке |

**⚠️ Лимитер:** второй запрос подряд к statistics → **HTTP 429** (глобальный, per seller). Синк —
строго последовательный, один воркер, экспоненциальный бэкофф, паузы ≥60с между тяжёлыми методами.
Никогда не дёргать WB API из UI/агента напрямую — только из БД.

## Схема БД (предложена владельцу 16.07, ждёт «ок»)
PostgreSQL, та же база albery. Сырьё всегда в `raw jsonb` (переживаем изменения API).

- `wb_cards` — справочник: nm_id PK, imt_id, vendor_code, brand, title, subject_id/name, photo_url, raw, updated_at.
- `wb_orders` — факт заказов: srid UNIQUE, g_number, date, last_change_date, nm_id→cards, barcode, brand,
  subject, tech_size, warehouse, region/oblast, is_cancel, total_price, discount_percent, spp, finished_price,
  price_with_disc, raw. IDX (date), (nm_id,date), (brand,date).
- `wb_sales` — выкупы/возвраты: sale_id UNIQUE (S…/R…), srid, date, nm_id, for_pay, finished_price,
  price_with_disc, spp, is_return (по префиксу R), raw. IDX как orders.
- `wb_stocks_daily` — ежедневный снапшот остатков: PK (snapshot_date, nm_id, barcode, warehouse),
  quantity, in_way_to, in_way_from, qty_full, price, discount. Для «динамики остатков» по артикулам.
- `wb_finance_details` — строки финотчёта: rrd_id PK, realizationreport_id, date_from/to, rr_dt, nm_id,
  brand_name, subject_name, sa_name, barcode, doc_type_name, supplier_oper_name, quantity, retail_price,
  retail_amount, retail_price_withdisc_rub, ppvz_for_pay, delivery_rub, return_amount, storage_fee, penalty,
  deduction, acquiring_fee, ppvz_sales_commission, commission_percent, office_name, order_dt, sale_dt, raw.
- `wb_adv_costs` — реклама: (date, advert_id) PK, sum, type, campaign_name, raw — строка «Реклама» в ОПиУ.
- `wb_paid_storage` — хранение: (date, nm_id, barcode, warehouse) PK, amount, volume, coef, raw.
- `wb_prices_current` — снапшот цен: (snapshot_date, nm_id, size_id) PK, price, discount, club_discount.
- `wb_cost_prices` — себестоимость (внутренние данные): barcode PK, nm_id, cost numeric, valid_from, source
  — для «Себестоимость продаж» в ОПиУ/калькуляторе (у команды уже есть эксели с себестоимостью).
- `wb_tax_settings` — налоговый режим: mode (УСН-Д/УСН-ДР/АУСН/СНГ), rate, vat_mode, vat_rate, effective_from.
- `wb_sync_state` — endpoint PK, last_from, last_rrd_id, last_run_at, status, note (инкрементальность).
- `wb_sync_log` — журнал прогонов: started/finished, endpoint, rows, error.

## Маппинг разделов UI → данные
- **Общий дашборд** — карточки: заказы/выкупы/возвраты за период (orders/sales), выручка, остатки суммарно,
  топ-артикулы, динамика по дням; селектор дат как в референсе.
- **РНП** («Рука на пульсе», ежедневка — ПОДТВЕРДИТЬ у владельца состав) — день к дню: заказы шт/₽,
  выкупы, ДРР (adv_costs/выручка), остатки, скорость заказов.
- **ОПиУ** — из finance_details агрегаты: продажи − комиссия − логистика − хранение − штрафы − реклама −
  себестоимость (cost_prices) = прибыль; помесячно.
- **ДДС** — по supplier_oper_name/doc_type + даты отчётов: поступления от WB (ppvz_for_pay), удержания;
  фактические платежи по неделям отчётов.
- **По артикулам** — таблица как референс: фото (cards), артикул, остаток (stocks_daily последний),
  динамика остатков (спарклайн по stocks_daily), заказы ₽ (orders), скорость заказов шт/день, по дням
  заказы (heatmap) — фильтр по бренду.
- **Налоговый калькулятор** — реализация до/после СПП (finance_details retail_amount vs
  retail_price_withdisc_rub/ppvz_for_pay), услуги WB (комиссия/логистика/реклама/прочие), режимы
  УСН-Д/УСН-ДР/АУСН/СНГ (tax_settings), себестоимость продаж/самовыкупов, затраты → операционная прибыль.

## Синхронизация (дизайн)
Отдельный скрипт `scripts/wb_sync.py` (по образцу sync_google_drive: advisory lock + cron), строго
последовательные вызовы: orders/sales — каждые 30 мин инкрементально (dateFrom = max(last_change_date));
stocks — снапшот 1 р/день (ночью); finance reportDetailByPeriod — 1 р/день по rrd_id; cards/prices — 1 р/день;
adv/storage — 1 р/день. Первичная загрузка полугода — чанками с паузами (finance по неделям). 429 → бэкофф
×2 до 10 мин, всё в wb_sync_log.

## Инструменты агента (MCP, read-only из БД)
`wb_analytics_summary(period, brand)` · `wb_article_stats(nm_id|vendor_code, period)` ·
`wb_finance_report(period, brand)` · `wb_tax_estimate(period, mode, rate)` · `wb_stocks_now(brand)`.
Плюс маршрут в «Маршрутной карте»: вопросы по продажам/остаткам/прибыли WB → эти инструменты, НЕ fetch_url.

## Этапы
1. ✅ Ключ + разведка + проект схемы (задача 1606).
2. ✅ Бекенд (Albery `aff2074`, задача 1608): миграция 053 применена; `wb_cabinet.py` (WBClient
   последовательный+бэкофф; sync_*; запросы разделов; налоги 5 режимов+НДС прозрачным построчным
   расчётом; роуты `/api/wb-cab/*` за общей auth); `scripts/wb_sync.py` (advisory lock 984312077,
   `--initial N`); systemd `albery-wb-sync.timer` каждые 30 мин — ВКЛЮЧЁН; бэкфилл 182 дней запущен
   16.07 ~19:45 (лог `/var/log/albery-wb-backfill.log`; лимитер остывал после разведки — бэкофф
   110→188с, это штатно). Болванка себестоимости: `wb_cost_prices` + GET/POST `/api/wb-cab/cost-prices`
   (импорт Excel ляжет сюда же). Владелец: РНП = «Рука на пульсе» подтверждён; метрики должны
   ЛЕГКО расширяться (слой запросов + VIEW `wb_daily_metrics`).
3. ✅ UI (Albery `39d9496`, задача 1610): `Интерфейс/src/wbcab/WbCabinet.tsx` (отдельный файл,
   App.tsx только импорт+маршрут) — все 6 разделов, общий фильтр периода+бренда, счётчики базы;
   По артикулам: фото, спарклайн остатков (SVG), heatmap заказов по дням; Налоговый калькулятор —
   раскладка по референсу. Сборка локально (C:\Albery, node 24), dist tar+атомарный свап.
4. Наполнение данными — автоматически по мере доливки бэкфилла. **Статус 17.07 ~16:30 МСК
   (после персонального ключа):** orders/sales — полгода готово (18.01→сегодня, 188k/140k, done);
   финотчёт качается страницами 100k без 429 (800k+ строк, покрытие 16.01→20.03 и растёт,
   остаток дольют тики за ~1–2 ч); stocks_daily — снапшоты только с 16.07 (истории у WB нет);
   paid_storage на курсоре 16.05; q_summary/q_rnp боем отдают живые числа. cogs_rub=0 до
   импорта Excel себестоимости.
   4b. ✅ Этап 5 (Albery `a37eaa8`+`00665c0`, задача 1614): **tick-модель** после «снова упало» —
   спящий часами бэкфилл терял advisory lock (idle-соединение умирало) → таймер плодил дубли и
   жёг квоту. Теперь: тик 30 мин = stateless-прогон ≤ минут; 429 → `blocked_until` в
   `wb_sync_state` (мигр 054) + переход к следующему источнику; закрытые методы не вызываются;
   бэкфилл по курсорам (`cursor_date`/`done`, финансы 7-дневными чанками ≤20/тик; orders/sales
   полгода одним вызовом при открытой квоте). Квоты видны в UI-панели. ПРАВИЛО: в синках WB
   НИКОГДА не спать дольше ~90с внутри процесса.
   4c. ✅ Тик переживает длинные прогоны (Albery `e08f10a`, задача 1680): 10-минутный тик с
   персональным ключом убивался `idle_in_transaction_session_timeout=120s` (shared/db.py) —
   лок-соединение висело в открытой транзакции, финальный unlock ронял unit в failed при целых
   данных. Фикс: `lock_conn.commit()` после захвата advisory lock (сессионный лок переживает
   коммит) + try/except на unlock + гейты `B24_SESSION_IDLE_WATCH/TASK_OFFER/TASK_CHECKIN=0`
   до импорта app (в тике 16:19 внутри синка стартовал второй idle-sweep — нельзя).
5b. ✅ Этап 6 — ОТДЕЛЬНАЯ СТРАНИЦА /Analytics в новом дизайне (Albery `5ee7927` бекенд + `1bcb687`
   UI, задача 1616). Владелец дал готовый эстетичный дизайн (папка «Страница WB кабинет», React 19 +
   Tailwind v4 + recharts). Решение: **самостоятельный Vite-бандл** `wb-cabinet/` в репо Albery
   (base=`/analytics/`), Flask отдаёт на `GET /analytics` + `/Analytics` (+ ассеты `/analytics/<path>`,
   SPA-fallback) за общей админ-авторизацией. Клик «WB-кабинет» в основном приложении (боковое меню +
   верхняя навигация, `Интерфейс/src/App.tsx`) → `window.location='/analytics'`. Почему отдельный
   бандл, а не в основной UI: у страницы Tailwind v4, у основного приложения своя версия — разделение
   исключает конфликт (хирургично). РНП: реальный выбор наших артикулов через новый
   `/api/wb-cab/cards?q=&brand=` (wb_cards: vendor_code/title/nm_id, фото, фильтр бренда). Дашборд
   подключён к `/api/wb-cab/tax`+`summary` — наполняется сам по мере бэкфилла (сейчас 0/пусто честно,
   без фейковых чисел); ОПиУ/ДДС/план/себестоимость — чистые заглушки под будущую логику. Сборка
   ЛОКАЛЬНО (C:\Albery\wb-cabinet, node 24), dist гитигнорится, деплой tar+свап. **Правило:**
   отдельные страницы Albery = свой Vite-бандл + Flask route за before_request-авторизацией, base под
   свой префикс, ассеты не конфликтуют с `/assets` основного приложения.
5c. ✅ Этап 7 — вкладки = отдельные страницы + анимации + интерактивные графики (Albery
   `fa6eca9`, задача 1688, 17.07). Роутер на history API (`wb-cabinet/src/lib/router.ts`):
   /analytics{,/rnp,/pnl,/cashflow,/articles,/tax,/settings}, SPA-fallback Flask уже был —
   deep-link/F5/назад работают. Загрузка «как продукт»: первая — shimmer-скелетоны (.skeleton
   в index.css), рефетч по фильтрам — кадр сохраняется и притемняется (.refetching, без
   мигания), смена раздела — fade-in. Графики: у спарклайнов crosshair+активная точка+тултип
   (дата/₽/серия); новый широкий «Динамика по дням» (столбики заказов + линия продаж
   финотчёта, общий тултип на каждой точке). Пара цветов проверена dataviz-валидатором
   (ΔE 38.9). Проверка: скриншот-харнесс = мок-API (fixtures /api/wb-cab/*) + инжект
   hover-события + Edge headless; грабля: `--virtual-time-budget` АБОРТИТ висящие fetch — для
   скелетон-скрина нужен сервер с задержкой ответов и снимок без virtual-time.
5. MCP-инструменты агента (`wb_analytics_summary`, `wb_article_stats`, `wb_finance_report`,
   `wb_tax_estimate`, `wb_stocks_now`) + маршрут в «Маршрутной карте» — СЛЕДУЮЩИЙ шаг.
6. Импорт Excel себестоимости + фильтры-доработки по фидбеку владельца.

Каждый этап = закрытая Bitrix-задача (правило №8). ⚠ Репозиторий xotizwf-create/Albery — PUBLIC
(замечено 16.07 при клонировании) — секретов в git нет, но бизнес-код открыт; поднято владельцу.
