# KFU admissions program budget-seat research

Use this when researching Kazan Federal University (КФУ) admissions programs, especially магистратура program choice by budget places.

## Key lesson

If the user says to consider only budget-funded places, filter at the program row level before ranking fit. Do not recommend a profile with `0 бюджет` just because its title/curriculum fits well. State the budget-seat count next to each ranked option and explicitly mark excluded attractive options as `0 бюджет`.

## Official dynamic source pattern

The public KFU admissions program archive at:

- `https://admissions.kpfu.ru/programs/?query=&sptypes%5B%5D=2` for магистратура

may not include all program rows in the initial HTML and search/web extraction can miss them. The frontend loads more rows through WordPress admin-ajax:

```python
import urllib.request, urllib.parse, json

params = '?query=&sptypes%5B%5D=2'  # master programs
for page in range(1, 20):
    body = urllib.parse.urlencode({
        'action': 'getPrograms',
        'page': str(page),
        'params': params,
    }).encode()
    req = urllib.request.Request(
        'https://admissions.kpfu.ru/wp-admin/admin-ajax.php',
        data=body,
        headers={
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )
    response = json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore'))
    html = response.get('html', '')
    # strip tags / parse cards here
    if not response.get('hasNextPage'):
        break
```

The response JSON contains `html` and `hasNextPage`. Continue until `hasNextPage` is false; page URLs alone can repeat/omit data, while this endpoint follows the site’s own “load more” behavior.

## Output pattern for program ranking

For each relevant program include:

- direction code and name;
- profile name;
- institute/campus;
- form and duration;
- `N бюджет` and `N контракт`;
- whether it is included or excluded under the user’s budget-only constraint.

Example wording:

> “По смыслу подходит, но для твоего условия вычеркиваем: 0 бюджетных мест.”

## 2026 KFU example rows observed in one session

These examples are useful for checking the parser shape, not as permanently current facts:

- `38.04.05 Бизнес-информатика (профиль: Цифровые технологии в бизнесе)` — Казань, Институт вычислительной математики и информационных технологий — очная — `10 бюджет`, `2 контракт`.
- `38.04.02 Менеджмент (профиль: Управление бизнес-аналитикой в IT...)` — Казань, ИУЭиФ — очная — `0 бюджет`, `18 контракт`; attractive for AI/IT fit but excluded for budget-only selection.
- `38.04.01 Экономика (профиль: Экономика данных и цифровая аналитика; Экономика предприятия и цифровое развитие; ВЭД)` — Казань, ИУЭиФ — очная — `42 бюджет`, `2 контракт`.
- `38.04.02 Менеджмент (профиль: Бизнес и менеджмент)` — Казань, ИУЭиФ — очная — `18 бюджет`, `1 контракт`.
- `38.04.08 Финансы и кредит (профиль: Финансовая аналитика)` — Казань, ИУЭиФ — очная — `18 бюджет`, `5 контракт`.
- `38.04.04 Государственное и муниципальное управление (профиль: Современное публичное управление)` — Казань, ИУЭиФ — заочная — `18 бюджет`, `5 контракт`.

Always re-query the live official source before giving current admissions advice.
