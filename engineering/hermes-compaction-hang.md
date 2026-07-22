---
id: hermes-compaction-hang
type: engineering
tags: [hermes, gateway, compression, compaction, groq, codex, watchdog, incident, 217]
updated: 2026-07-22
secret_refs: []
---

# Зависание агента в петле сжатия контекста (инцидент 2026-07-22)

**Симптом для владельца:** «агент умер». Пишешь «Ты работаешь?» — тишина, задача (договор)
не сделана. При этом `systemctl status hermes-gateway` — `active (running)`, процесс жив,
`Restart=always` не срабатывает, ни одна проверка не звонит.

## Что было на самом деле

В журнале 13:30–14:05:

```
🗜️ Compacting context — summarizing earlier conversation so I can continue...
⚠️  Session compressed 32 times — accuracy may degrade.
⚠ Compression summary failed: Error code: 413 — Request too large for model
  `llama-3.3-70b-versatile` ... tokens per minute (TPM): Limit 12000
⚠ Compression summary failed: Codex auxiliary Responses stream exceeded 45.0s total timeout
WARNING agent.auxiliary_client: marking local/custom unhealthy for 600s (payment / credit error)
```

**Корневая причина:** `auxiliary.compression` был настроен на Groq
(`llama-3.3-70b-versatile`, `base_url: api.groq.com`), а сжимать надо было ~93k токенов.
Лимит Groq — **12 000 токенов в минуту**, то есть 413 гарантирован на КАЖДОЙ попытке.
Проверено по всем моделям Groq на этом ключе: `llama-3.3-70b-versatile` — 12 000,
`openai/gpt-oss-120b` и `gpt-oss-20b` — 8 000. Ни одна не годится для сжатия реального диалога.

Дальше — замкнутый круг: сжатие падает → контекст не уменьшается → следующий ход снова
превышает порог → снова сжатие. Резервный codex-суммаризатор не укладывался в таймаут 45 c
и добивал каждую попытку. Агент круглосуточно «работал», но не отвечал.

Усугубляло: `compression.threshold: 0.025` — ниже пола `MINIMUM_CONTEXT_LENGTH`, поэтому порог
вырождался в жёсткие 64 000 токенов независимо от окна модели (у `gpt-5.6-terra` окно 272 000),
и компакция запускалась почти на каждом ходе.

## Что сделано (217, 2026-07-22)

Бэкап конфига: `/root/.hermes/config.yaml.bak.20260722_141757`.

```yaml
compression:
  threshold: 0.5            # было 0.025 -> порог 136 000 вместо 64 000
auxiliary:
  compression:
    provider: auto          # было custom (Groq)
    model: ''               # было llama-3.3-70b-versatile
    base_url: ''            # было https://api.groq.com/openai/v1
    api_key: ''
    timeout: 300            # было 45
```

`provider: auto` для вспомогательных задач берёт основную модель — codex `gpt-5.6-terra`,
окно 272k, подписка ChatGPT, лимитов по токенам в минуту нет.

**Боевая проверка (не «тесты зелёные», а тот самый вызов):** сжатие диалога на ~85 500 токенов
через `auxiliary_client.call_llm(task='compression', ...)` — до фикса 413 от Groq,
после фикса осмысленное резюме за 11,5 c моделью `gpt-5.6-terra`. После рестарта в журнале
ноль компакций.

## Сторож, который ловит это без владельца

`scripts/hermes_compaction_watchdog.py` + системный cron каждые 5 минут:

```
*/5 * * * * /usr/bin/python3 /root/.hermes/agent-knowledge/scripts/hermes_compaction_watchdog.py >> /var/log/hermes_watchdog.log 2>&1
```

Почему **системный** cron, а не `hermes cron`: задания hermes исполняет сам gateway — когда он
в петле, его собственные проверки висят вместе с ним. Сторож шлёт сообщение напрямую через
Bot API (токен `/root/.hermes/secure/claude_code/bot_token`), не через агента.

Что проверяет: служба не active → рестарт; ≥3 падений сжатия или ≥12 компакций за 15 минут →
тревога, при повторе на следующей проверке — рестарт (кулдаун час); `auxiliary.compression`
снова смотрит на модель с малым лимитом токенов → тревога (защита от возврата причины).
Окно журнала начинается не раньше последнего старта службы, иначе старые строки читаются как
новая петля. Тихий, пока всё хорошо.

Тест на реальном журнале инцидента: `python tests/test_compaction_watchdog.py`
(фикстура `tests/fixtures/journal_compaction_storm_2026-07-22.txt` — настоящие строки из journald).

## Урок

`Restart=always` защищает только от падения процесса. Зависание в петле выглядит как здоровье:
сервис active, CPU идёт, логи пишутся. Такие состояния ловятся только по признаку «нет полезной
работы» — и проверять их должен процесс, живущий ОТДЕЛЬНО от того, за кем следит.

См. также `logs/mistakes.md`, `engineering/server-preflight.md`.
