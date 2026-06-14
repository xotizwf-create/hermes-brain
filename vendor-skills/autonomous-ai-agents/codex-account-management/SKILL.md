---
name: codex-account-management
description: "Управление OpenAI Codex OAuth-аккаунтами в Hermes: подключение, проверка работоспособности, дедупликация по реальному аккаунту."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, codex, oauth, credentials, account-management]
    related_skills: [hermes-agent]
---

# Codex account management for Hermes

Используй этот навык, когда пользователь просит подключить, проверить, удалить или почистить OpenAI Codex / `openai-codex` аккаунты в Hermes.

## Главное правило

Никогда не считать Codex-аккаунты уникальными по `label`, `id` записи или имени импорта. Эти поля технические и могут дублировать один и тот же реальный аккаунт.

Уникальность проверяется только по данным внутри OAuth/JWT:

1. `sub` / `https://api.openai.com/auth` / другой стабильный user/account id из access token claims;
2. email из claims — только как человекочитаемое подтверждение, если он есть;
3. при наличии нескольких токенов с одинаковым реальным user/account id — это дубль, даже если labels разные.

Токены, refresh tokens и полные JWT в чат, логи и финальные ответы не выводить.

## Где лежат данные

- Текущий профиль: `~/.hermes/auth.json`
- Именованные профили: `~/.hermes/profiles/<profile>/auth.json`
- Codex pool: `credential_pool.openai-codex`
- Singleton state старого формата может быть в `providers.openai-codex`

Перед чисткой проверяй все профили, если пользователь говорит «подключено сюда» или уже были дубли в профилях.

## Безопасная проверка уникальности

Запускай аудит скриптом, который:

1. читает только `auth.json` нужных профилей;
2. декодирует JWT payload локально без отправки токенов наружу;
3. выводит только label, profile, entry id, статус наличия токена, email/user_id в укороченном или хэшированном виде;
4. группирует записи по реальному account key;
5. отдельно помечает:
   - уникальные рабочие аккаунты;
   - дубли одного аккаунта;
   - мёртвые/просроченные токены;
   - записи без читаемого identity.

Минимальный локальный аудит claims:

```bash
python - <<'PY'
import base64, json, pathlib, hashlib
roots = [pathlib.Path('/root/.hermes')]
roots += [p for p in pathlib.Path('/root/.hermes/profiles').glob('*') if p.is_dir()]

def claims(token):
    try:
        part = token.split('.')[1]
        part += '=' * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part.encode()))
    except Exception:
        return {}

def short(v):
    if not v: return ''
    s = str(v)
    return s if '@' in s and len(s) < 80 else hashlib.sha256(s.encode()).hexdigest()[:12]

groups = {}
for root in roots:
    auth = root / 'auth.json'
    if not auth.exists():
        continue
    data = json.loads(auth.read_text())
    entries = (data.get('credential_pool') or {}).get('openai-codex') or []
    for i, e in enumerate(entries):
        c = claims(e.get('access_token') or '')
        ident = c.get('sub') or c.get('https://api.openai.com/auth') or c.get('oid') or c.get('uid') or c.get('email') or ''
        email = c.get('email') or c.get('preferred_username') or c.get('upn') or ''
        key = str(ident or f'no-identity:{root}:{i}')
        groups.setdefault(key, []).append({
            'profile': 'default' if root == pathlib.Path('/root/.hermes') else root.name,
            'idx': i,
            'id': e.get('id'),
            'label': e.get('label'),
            'email': email,
            'identity': short(ident),
            'status': e.get('last_status'),
        })
for key, rows in groups.items():
    print('ACCOUNT', short(key), 'entries=', len(rows))
    for r in rows:
        print(' ', r)
PY
```

## Реальная проверка работоспособности

Claims показывают идентичность, но не доказывают, что аккаунт работает. После аудита сделай минимальный реальный запрос к Codex API каждой уникальной записи. Проверка должна быть короткой и дешёвой.

Если запрос возвращает `token_invalidated`, `invalid_token`, `invalid_grant`, `expired`, `unauthorized`, помечай запись как нерабочую и не считай её активным аккаунтом.

## Дедупликация

Если несколько записей имеют один реальный account key:

1. оставить одну запись с живым refresh/access token;
2. предпочтительно оставить запись из активного текущего профиля или запись с понятным label;
3. перед удалением сформировать список exact profile + provider + pool index/id + label;
4. удалять только точечную дубль-запись, не всю группу;
5. после удаления повторить аудит и реальный запрос.

Если запись мёртвая и принадлежит ожидаемому второму аккаунту пользователя — не заменять её дублем другого аккаунта; честно сказать, что второй аккаунт надо заново авторизовать.

## Подключение нового Codex-аккаунта

1. До авторизации сделать аудит текущих уникальных Codex-аккаунтов.
2. Запустить OAuth без автоматического браузера на целевом Hermes home, если это обычная локальная среда:

```bash
hermes auth add openai-codex --type oauth --label '<human-label>' --no-browser --timeout 600
```

Если сервер просит открыть ссылку/ввести код — отправить пользователю только ссылку и код авторизации, не просить пароль в Telegram.

3. После успешного логина сразу выполнить аудит identity.
4. Если новый token ведёт к уже существующему account key — это дубль: удалить новую дубль-запись и сообщить пользователю, что он вошёл не в тот аккаунт.
5. Если account key новый — выполнить короткий реальный запрос Codex API и подтвердить, что добавился новый уникальный рабочий аккаунт.
6. Финальный ответ давать количеством уникальных рабочих аккаунтов и понятными email/labels, без токенов.

## Выделенный Codex-аккаунт для удалённого Hermes

Когда пользователь хочет подключить **отдельный** ChatGPT/Codex-аккаунт к удалённому Hermes-агенту (например, проектному боту на сервере), не авторизуй его в основном локальном `~/.hermes`: это смешает аккаунты и усложнит перенос.

Правильный поток:

1. На удалённом сервере сначала read-only проверить активный `HERMES_HOME`, `hermes-gateway.service`, текущий `auth.json` и наличие `credential_pool.openai-codex` / `providers.openai-codex` без вывода токенов.
2. Если `hermes auth add openai-codex ...` на сервере возвращает 403 уже на device-code request, не пытаться повторять с логином/паролем: датацентровые IP часто блокируются. Генерировать OAuth на локальной машине/среде, где пользователь может открыть браузер.
3. Создать временный изолированный Hermes home и запускать авторизацию там:

```bash
rm -rf ~/.hermes/tmp/<project>-codex-oauth-home
mkdir -p ~/.hermes/tmp/<project>-codex-oauth-home
HERMES_HOME=~/.hermes/tmp/<project>-codex-oauth-home \
  hermes auth add openai-codex --type oauth \
  --label '<project>-dedicated-codex-YYYYMMDD' \
  --no-browser --timeout 900
```

4. Отправить пользователю только `https://auth.openai.com/codex/device` и короткий код. Явно попросить войти в **выделенный аккаунт проекта**, а не в уже подключённые аккаунты.
5. После завершения авторизации декодировать JWT локально и сравнить identity с уже известными аккаунтами. Если это дубль — удалить временный home/запись и попросить перелогиниться в другой ChatGPT-аккаунт.
6. Только после проверки переносить credential на удалённый сервер в его активный `HERMES_HOME`, предварительно сделав бэкап `auth.json`. Не копировать один и тот же refresh token в два живых Hermes-процесса без явного согласия: совместное обновление OAuth может инвалидировать сессии.
7. После переноса проверить `hermes auth list openai-codex`, модельный `PING-OK`, затем перезапустить только целевой `hermes-gateway.service` и попросить `/reset` в чате проекта, чтобы сессия подхватила новый credential.

## Формат ответа пользователю

Писать по-русски и по-человечески:

- сколько уникальных Codex-аккаунтов найдено;
- какие labels являются дублями, если есть;
- какие записи удалены и почему;
- что нужно сделать пользователю, если он вошёл не в тот аккаунт;
- не показывать технические id, пути и команды без необходимости.
