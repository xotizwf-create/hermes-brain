---
id: albery-vpn-gateway
type: project
project: albery
tags: [albery, vpn, amneziawg, networking, reference]
updated: 2026-05-30
secret_refs: [proj/albery/ssh/root, proj/albery/vpn/estonia-root]
---

# Albery — VPN gateway (AmneziaWG)

> ⚠ Server IP: current prod is `217.198.12.236`. Some legacy commands below reference the
> historical IP `186.246.7.32` from the 2026-05-27 setup; treat those as "the prod server"
> and verify against the live host before running (to be reconciled during brain sync).
> Credentials by NAME only — never print or commit secrets.

> Extracted from `server-context.md` (legacy `agent.md` import). Routes all outbound prod
> traffic through Estonia so foreign APIs (OpenAI/Codex) don't get 403'd on the RU IP.


Настроено 2026-05-27.

### Зачем

Прод-сервер `186.246.7.32` — российский. Некоторые иностранные сервисы режут
российские IP (например, OpenAI/Codex отдают `HTTP 403`). Чтобы такие сервисы
открывались, **весь исходящий трафик сервера заворачивается через эстонский
AmneziaWG-VPN** и выходит в интернет с эстонского IP `95.85.243.43`.
При этом **сайт `m4s.ru`/`mcp.m4s.ru` и SSH остаются на прямом российском IP** —
входящие посетители не страдают.

Проверка эффекта: с сервера `curl https://api.openai.com/v1/models` отдаёт `403`
напрямую и `401` (т.е. дошли, нужен только ключ) через VPN. Gemini/googleapis
доступен из РФ и без VPN.

### Серверы и ключи (.env)

```env
# Эстонский VPN-сервер (там стоит Amnezia/AmneziaWG)
VPN_SERVER_HOST=IP: 95.85.243.43
VPN_SERVER_USER=root
VPN_SERVER_PASSWORD=...
# Российский прод-сервер
root_password=...
```

- Эстонский сервер `95.85.243.43`: Amnezia в Docker. Профиль **1234** (UDP 1234,
  контейнер `amnezia-awg-1234`, клиент `10.8.2.2`) закреплён за прод-сервером.
  Там же есть старый профиль на UDP 47138 с личными устройствами владельца —
  **его не трогать**. Клиентский конфиг профиля 1234:
  `C:\Users\hotiz\Desktop\amnezia-estonia-1234.conf` — НЕ импортировать на ПК
  (адрес `10.8.2.2` уже занят прод-сервером, будет конфликт).
- Российский прод-сервер `186.246.7.32`: на нём стоит **клиент AmneziaWG** (`awg0`).

### Как подключаться к серверам (без SSH-ключей, пароль из .env)

Вход по паролю root через Python/Paramiko (как и для всего остального в этом проекте):

```python
import re, paramiko
env = {...}  # прочитать .env
host = re.search(r"\d+\.\d+\.\d+\.\d+", env["VPN_SERVER_HOST"]).group(0)  # 95.85.243.43
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(host, username="root", password=env["VPN_SERVER_PASSWORD"],
          look_for_keys=False, allow_agent=False)
# для прод-сервера: host="186.246.7.32", password=env["root_password"]
```

Пароли и приватные ключи в чат/логи не выводить.

### Как это работает (архитектура)

- На прод-сервере поднят интерфейс `awg0` (AmneziaWG) с `Table = off` — туннель
  сам по себе НЕ меняет маршруты. Маршрутизацией управляет отдельный скрипт.
- **Policy-routing** (`/root/vpn_apply.sh`, запускается как `PostUp` туннеля):
  - таблица `200`: маршрут по умолчанию через `awg0` (→ Эстония);
  - `ip rule` для `sport 22/443/80 → main` и пометка connmark входящих на `eth0`
    соединений (`fwmark 0x1 → main`) — ответы сервера как сайта/SSH уходят прямо
    через `eth0` на российский IP;
  - всё остальное (исходящее, инициированное сервером) → таблица `200` → туннель;
  - endpoint VPN, локальная подсеть и DNS-апстримы (85.193.93.193/194) прибиты
    прямым маршрутом через `eth0`, чтобы не зацикливать туннель и не ломать DNS;
  - туннель только IPv4, поэтому исходящий IPv6 в интернет **заблокирован**
    (`ip6tables` REJECT для NEW на `2000::/3`, входящий на сайт по IPv6 сохранён),
    плюс `/etc/gai.conf` предпочитает IPv4. Без этого приложения (например Codex)
    уходят по российскому IPv6 в обход VPN и получают блок.
- `PreDown` (`/root/vpn_rollback.sh`) снимает всю эту маршрутизацию при остановке
  туннеля, возвращая сервер на прямой маршрут (сайт при этом продолжает работать).

### Файлы на прод-сервере

```text
/etc/amnezia/amneziawg/awg0.conf                 конфиг туннеля (Table=off, PostUp/PreDown, MTU=1280)
/root/vpn_apply.sh                               включает policy-routing (endpoint определяется сам)
/root/vpn_rollback.sh                            снимает policy-routing
/root/vpn_apply.log                              лог apply/rollback
/usr/local/sbin/vpn-healthcheck.sh               тест состояния VPN (exit 0 = OK)
/usr/local/sbin/vpn-watchdog.sh                  авто-перезапуск туннеля, если он реально упал
/usr/local/sbin/amneziawg-ensure-module.sh       пересборка модуля ядра при апгрейде ядра
/etc/systemd/system/awg-quick@awg0.service.d/override.conf   ExecStartPre=ensure-module
/etc/systemd/system/vpn-watchdog.{service,timer}
/etc/modules-load.d/amneziawg.conf
/usr/src/amneziawg-linux-kernel-module, /usr/src/amneziawg-tools   исходники
```

### Установка с нуля (что было сделано на прод-сервере)

PPA `ppa:amnezia/amneziawg` больше нет — ставится из исходников с GitHub
(GitHub с сервера доступен):

```bash
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y build-essential dkms git "linux-headers-$(uname -r)"
# модуль ядра
cd /usr/src && git clone --depth=1 https://github.com/amnezia-vpn/amneziawg-linux-kernel-module
cd amneziawg-linux-kernel-module/src && make -j"$(nproc)" && make install && depmod -a && modprobe amneziawg
# утилиты awg / awg-quick
cd /usr/src && git clone --depth=1 https://github.com/amnezia-vpn/amneziawg-tools
cd amneziawg-tools/src && make -j"$(nproc)" && make install
```

Конфиг `/etc/amnezia/amneziawg/awg0.conf` = клиентский конфиг профиля 1234, но:
добавлено `Table = off`, `MTU = 1280`, `PostUp = /root/vpn_apply.sh`,
`PreDown = /root/vpn_rollback.sh`; строка `DNS = ...` удалена (чтобы awg-quick
не трогал системный DNS). Включение:

```bash
systemctl enable --now awg-quick@awg0
```

### Автозапуск после перезагрузки сервера

«Всегда включён» обеспечивают:

- `systemctl enable awg-quick@awg0` — туннель + policy-routing (через PostUp)
  поднимаются при загрузке (после `network-online.target`);
- `ExecStartPre=/usr/local/sbin/amneziawg-ensure-module.sh` — если ядро
  обновилось и модуля для него нет, он пересобирается перед стартом туннеля;
- `/etc/modules-load.d/amneziawg.conf` — модуль грузится на раннем этапе;
- `PersistentKeepalive=25` в конфиге — туннель сам переустанавливает handshake;
- **watchdog** `vpn-watchdog.timer` (каждые ~3 мин): если handshake устарел И
  через туннель нет интернета — перезапускает `awg-quick@awg0`.

### Тест / проверка состояния

Быстрый health-тест (печатает статус, код возврата 0 = всё ок):

```bash
ssh root@186.246.7.32 /usr/local/sbin/vpn-healthcheck.sh
```

Проверяет: сервис enabled+active, свежесть handshake, выходной IP = `95.85.243.43`,
доступность OpenAI (не 403), что сайт `:5002` жив.

Проверка пути загрузки БЕЗ полной перезагрузки (удалить интерфейс и поднять заново
через systemd — имитация ребута):

```bash
ssh root@186.246.7.32 'awg-quick down awg0; systemctl restart awg-quick@awg0; sleep 5; /usr/local/sbin/vpn-healthcheck.sh'
```

Полный тест ребутом (сайт на ~1 мин недоступен во время перезагрузки; VPN должен
подняться сам):

```bash
ssh root@186.246.7.32 reboot
# подождать ~1-2 минуты, затем:
ssh root@186.246.7.32 /usr/local/sbin/vpn-healthcheck.sh   # ожидаем RESULT: OK
```

### Как поставить ДРУГОЙ VPN (заменить профиль/сервер)

Если появится новый VPN (другой эстонский/другой сервер) с AmneziaWG-конфигом:

1. Положить новый клиентский конфиг в `/etc/amnezia/amneziawg/awg0.conf`.
2. Дописать/сохранить в секции `[Interface]`:
   `Table = off`, `MTU = 1280`,
   `PostUp = /root/vpn_apply.sh`, `PreDown = /root/vpn_rollback.sh`;
   удалить строку `DNS = ...`.
3. Перезапустить и проверить:

```bash
systemctl restart awg-quick@awg0
/usr/local/sbin/vpn-healthcheck.sh
```

Менять `vpn_apply.sh` НЕ нужно — IP нового VPN-сервера (endpoint) он определяет
сам из туннеля. Если новый VPN — обычный WireGuard (без обфускации), используется
стандартный `wg`/`wg-quick` и `/etc/wireguard/awg0.conf`, остальная логика та же.

### Откат / временно отключить VPN (сервер вернётся на прямой IP, сайт продолжит работать)

```bash
ssh root@186.246.7.32 'bash /root/vpn_rollback.sh && awg-quick down awg0'
# отключить и автозапуск:
ssh root@186.246.7.32 'systemctl disable --now awg-quick@awg0 vpn-watchdog.timer'
```

### Диагностика

```bash
awg show awg0                       # handshake, трафик, endpoint
ip rule show                        # должны быть правила 900/901/902/1000/1001
ip route show table 200             # default dev awg0 + прямые маршруты endpoint/DNS
tail -n 40 /root/vpn_apply.log
journalctl -t vpn-watchdog -n 20    # срабатывания сторожа
curl -s https://ifconfig.me/ip      # должно быть 95.85.243.43
```

Кросс-проверка с эстонской стороны (endpoint пира `10.8.2.2` должен показывать
`186.246.7.32` — это и есть прод-сервер):

```bash
ssh root@95.85.243.43 "docker exec amnezia-awg-1234 wg show wg0"
```

