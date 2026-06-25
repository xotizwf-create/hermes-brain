---
id: hermes-brain-incidents
type: project
project: hermes-brain
tags: [incidents]
updated: 2026-06-25
secret_refs: []
---

# Hermes Brain — incidents

## 2026-06-25 (вечер) — Albery-бот на 186 ставит задачи 2-4 мин = тот же мёртвый IPv6 на eth0

Владелец: бот в Битриксе (мозг на 186) ОЧЕНЬ долго создаёт задачи — после «Да» задача ставилась
~3 мин (норма — секунды). Гипотеза владельца: «слишком много инструментов грузится, надо
облегчать». **Гипотеза проверена замерами и ОПРОВЕРГНУТА — корень оказался сетевым (как на 217).**

Findings (всё по живым замерам на 186, `hermes -z … -t albery-ops --yolo`):
- **Число инструментов на латентность НЕ влияет.** A/B одинакового промпта: без вызова инструмента
  ~6 c при любом тулсете (faq=15 / ops=66 / full=70 инструментов). Форсированный одиночный вызов:
  faq(15)=93 c, ops(66)=74 c — узкий срез оказался даже МЕДЛЕННЕЕ. Значит «грузить меньше
  инструментов» (узкие срезы / RAG-классификатор) проблему НЕ решает.
- **Бимодальный разброс одной и той же операции:** 11-13 c ИЛИ 72-93 c. Это не структура, а
  перемежающиеся залипания исходящих вызовов.
- **Корень — мёртвый IPv6 default-route на `eth0`** (тот же класс, что на 217). `ip -6 route show
  default` → `default via fe80::… dev eth0 proto ra`; глобального IPv6 на eth0 нет (только
  link-local). `openrouter.ai` резолвится и в AAAA (`2a06:98c1:…`); codex-стрим gpt-5.5 пробовал
  IPv6 → мёртвый путь → залипал до таймаута (60-90 c) → ретрай. Проверено: `curl -6 openrouter` →
  `code=000` (висел ~2 c), `curl -4` → `200` за 0.30 c. `disable_ipv6` был `0`.
- Постановка задачи = 2-3 модельных round-trip'а, каждый рисковал залипнуть → 148 c и 269 c в
  реальных ходах владельца (журнал `bitrix_bot_interactions` dialog 16, ходы 155/157).

Fix applied (идентичен 217, хирургически — бокс 2 ГБ + 2 ГБ swap):
- **Отключён IPv6 только на `eth0`:** `sysctl -w net.ipv6.conf.eth0.disable_ipv6=1`, персист
  `/etc/sysctl.d/99-hermes-eth0-no-ipv6.conf`. v6 default-route и v6-адрес с eth0 ушли → IPv6
  фейлится мгновенно (0.0001 c), весь внешний трафик идёт по рабочему IPv4.
- **Отличия от 217:** на 186 НЕТ Tailscale (трогать `all`/`tailscale0` было нельзя только на 217).
  `lo`/`::1` НЕ тронуты — Postgres слушает `[::1]:5432`, проверено `select 1` после фикса = OK.
  Бэкап маршрутов: `/root/.hermes/ipv6_eth0.bak.<ts>`. Откат: убрать sysctl-файл + `…disable_ipv6=0`.
- Verified post-fix: v6 default-route нет, eth0 без v6, `::1`/Postgres живы, albery/hermes-gateway/
  postgresql active. Before/after (round-trip с быстрым инструментом): до — 2 из 4 залипали на
  72-73 c; после — 11.7/16.0/11.6 c, ноль залипаний. Постановка задачи ожидаемо ~20-30 c.
- **Остаточный нюанс:** в прокси-тесте на `list_zoom_calls` один прогон всё ещё дал 62 c — это
  МЕДЛЕННЫЙ сам инструмент (сканирует созвоны), не модель/сеть; к постановке задач (быстрые
  `create_bitrix_task`≈0.5 c, `get_org_structure`≈мгновенно) отношения не имеет. Остаточная
  провайдерская латентность openrouter/codex возможна, но редка и вне нашего контроля.

**ВТОРАЯ (настоящая) причина «задача не ставится» — найдена после IPv6-фикса (в новой сессии задача
всё равно не ставилась):** баг парсера срока в `create_bitrix_task`. `_normalize_bitrix_deadline`
принимал только дату-без-времени или ISO-с-`T` и ОТВЕРГАЛ `2026-06-28 15:00` / `28.06.2026 15:00`
(дата+ПРОБЕЛ+время) — а модель из «до 27.06 15:00» формирует именно так. Отказ → модель перебирает
форматы по round-trip'ам → мнимый «инструмент дважды не ответил по таймауту», задача не создаётся.
Изоляция: прямой `tasks.task.add`=0.4 c, прямой MCP `create_bitrix_task` мгновенно отказывал на
«пробельном» формате; с ISO-`T` создавал за 0.5 c. **Фикс** (`mcp/context_server.py`, коммит Albery
`f589db6`): принимать дату+время с пробелом ИЛИ `T` для обоих форматов даты + ISO с tz. Проверено:
все форматы → задача; сквозь мозг бота — задача с первого раза за 40 c (было 148-269 c и провал).
**IPv6 был необходим, но НЕ достаточен:** он убрал залипания (минуты→секунды/попытка), парсер — то,
что вообще не давало поставить. **Деплой:** живо на 186 + локальный коммит `f589db6`; пуш в GitHub
отложен (186 без кредов, 217 недоступен сессией) — запушить через 217 + guarded reset 186.

Доступ для разбора 186 с ПК: `tmp/d186.py` (paramiko, креды из `tmp/alb186.env`, тянутся из vault
на 217 через `tmp/fetch_once.py`); вывод через `PYTHONIOENCODING=utf-8`. См. память
[[hermes-217-direct-ssh-and-ipv6-fix]] и [[albery-server-access-from-pc]].

## 2026-06-25 — агент «очень долго отрабатывает / тупит» = сетевой провал 217 + мёртвый IPv6

Владелец: hermes-агент очень медленно отрабатывал запрос про hh.ru, «как будто сервер мёртв»,
и «после обновления стал тупить». Сначала с ПК 217 вообще не пинговался (таймаут на 22/80/443),
хотя 186/95 и интернет были живы — это и был тот же провал, а не «бокс лёг».

Findings (всё подтверждено по SSH на 217):
- **Это был ограниченный сетевой инцидент**, окно ≈14:41–15:13 UTC (17:41–18:13 МСК), ~32 минуты.
  Журнал `hermes-gateway` был забит `[Telegram] api.telegram.org connection failed → fallback IP
  149.154.166.110 failed → path unreachable`. В тот момент падал даже IPv4-фолбэк. Параллельно
  стрим главного мозга (codex/gpt-5.5) залипал (`Codex stream sent no events for 60s … Reconnecting`,
  `provider failed after retries`) — отсюда «тупит и очень долго»: каждый ответ в TG и каждый
  шаг hh-задачи уходил в ретраи с 10-сек таймаутами. До/после окна — чисто; к моменту разбора
  всё само восстановилось (load 0, outbound telegram/openai/groq < 0.5 c).
- **Хроническая болячка, усугублявшая каждый такой блип: IPv6 на 217 мёртв**, но в системе висел
  IPv6 default-route на `eth0` (`default via 2a03:6f00:a::1` + RA-маршрут). `api.telegram.org`
  резолвится в IPv6 (`2001:67c:…`), gateway пробовал IPv6 первым → таймаут → фолбэк на IPv4.
  Проверено: `curl -6 https://api.telegram.org` → `000`, `curl -4` → `302` за 0.27 c.
  `/etc/gai.conf` уже имел `precedence ::ffff:0:0/96 100`, но telegram_network-плагин шлюза всё
  равно лез в IPv6 мимо getaddrinfo-предпочтения.
- **Ложные подозреваемые исключены:** обновление НИ ПРИ ЧЁМ (config.yaml тронут 24.06; сегодняшний
  apt-upgrade 06:03 UTC — рутинный perl/libvnc). **Регрессии сжатия НЕТ** (в отличие от 11.06/18.06):
  `auxiliary.compression` = `llama-3.3-70b-versatile`, `compression.threshold: 0.025` — как надо.
  Диск 87% (13/15 ГБ) — занят легитимным софтом (`/usr` 7.2G, `/var/www`, meshcentral, google),
  не runaway-лог; не причина.

Fix applied (хирургически, бокс хрупкий — 1 ГБ):
- **Отключён IPv6 только на `eth0`**: `sysctl -w net.ipv6.conf.eth0.disable_ipv6=1`, персист в
  `/etc/sysctl.d/99-hermes-eth0-no-ipv6.conf`. Мёртвый IPv6 default-route ушёл → IPv6-коннект теперь
  фейлится мгновенно (нет маршрута) и сразу идёт по рабочему IPv4. **Tailscale-меш (`tailscale0`,
  `fd7a:115c:…`) и loopback `::1` НЕ тронуты** — трогать `all`/`tailscale0` нельзя (мешевая связь
  между серверами). SSH-сессия шла по IPv4, отвала не было. Бэкап маршрутов:
  `/root/.hermes/ipv6_route.bak.<ts>.txt`. Откат: убрать sysctl-файл + `sysctl -w …disable_ipv6=0`.
- Безопасная чистка диска (journal vacuum, 17→4 старых `config.yaml.bak*`, apt clean) — освободила
  крохи; autoremove = 0 пакетов. Диск останется ~87%; если поползёт к 95%+ — расширять том у
  хостера (15→25 ГБ), а не удалять реальный софт.
- Verified post-fix: `eth0` IPv6 убран, Tailscale цел, outbound telegram 302/0.32 c, openai 0.38 c,
  groq 0.44 c, gateway active, новых `telegram_network`-ошибок — 0.

Доступ для разбора: с ПК напрямую `paramiko` → `217.198.12.236` (root, пароль из brain `.env`
`HERMES_BRAIN_*`), БЕЗ цепочки vault — она нужна только для 186 (Albery). См. память
[[hermes-217-direct-ssh-and-ipv6-fix]].

## 2026-06-20 — `claude-tg` bot spent Claude Code limit and stayed silent

Owner reported that the Telegram bot connected to Claude Code on the 217 Hermes Brain server accepted prompts, consumed the Claude limit, and did not answer/progress-report.

Findings:
- The live side service is PM2 app `claude-tg`, script `/root/claude-agent/bridge.js`.
- The bridge previously ran Claude Code with `--model opus --output-format json` and only sent Telegram typing actions until the process exited.
- A live minimal Claude Code check returned a 5-hour rate-limit event with reset at `2026-06-21 02:40 MSK` and zero new token usage.
- The local state showed only two bridge requests, but large cached-token usage; the problem was heavy Claude Code sessions rather than Telegram polling itself.

Fix applied:
- Corrected the bridge back to the owner-required Claude Code default: Opus + medium effort + `stream-json` + request budget cap.
- Added a cheap account-limit preflight before the expensive Opus run so an exhausted account returns a clear message instead of burning another coding session.
- Forward short assistant progress text from the stream to Telegram, in addition to tool-use based status messages, so the owner sees what Claude is doing before the final answer.
- Persist Claude Code `session_id` as soon as any stream event contains it; this keeps `/new`, `/sessions`, `/switch`, and follow-up context closer to the Hermes-style session model even if the run ends via limit/error.
- Added second-layer quota protections after the post-incident review: block new expensive runs when account utilization is already dangerously high, warn at high utilization, cap oversized Telegram text prompts, auto-start a fresh Claude session when the active session becomes too context-heavy, and return an explicit timeout message instead of staying silent.
- Verified `node --check` passes and PM2 app is online after restart. A live account-limit check still returned 5-hour status `rejected` until `2026-06-21 02:40 MSK`, so a full Opus end-to-end test must wait for reset.
