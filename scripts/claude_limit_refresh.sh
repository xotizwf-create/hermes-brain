#!/usr/bin/env bash
# Обновление окна лимитов Claude Code — по одному минимальному запросу на аккаунт.
# Живёт на 217 как /root/.hermes/scripts/claude_limit_refresh.sh, зовётся заданием
# `claude-code-limit-refresh` (0 3,8,13 * * * UTC = 06:00/11:00/16:00 МСК).
#
# Аккаунты:
#   - основной — обычный вход Claude Code в /root/.claude (как было до многоаккаунтности);
#   - дополнительные — папка на аккаунт: <ACCOUNTS_DIR>/<имя>/oauth_token, куда кладётся
#     long-lived токен из `claude setup-token` (режим 600). Своя HOME на аккаунт, иначе
#     входы затирают друг друга в /root/.claude.
# Пока папки с дополнительными аккаунтами нет, скрипт ведёт себя ровно как одноаккаунтный.
#
# Тишина при успехе (cron ничего не доставляет), при сбое — одна строка на аккаунт.
# Намеренно без `set -e`: упавший аккаунт не должен отменять обновление остальных.
set -uo pipefail

PROMPT='OK'
ACCOUNTS_DIR=/root/.hermes/secure/claude_code/accounts
HOMES_DIR=/root/claude-accounts
failures=0

# $1 — имя для отчёта, $2 — HOME, $3 — long-lived токен ('' = брать вход из HOME)
refresh() {
  local name="$1" home="$2" token="$3"
  local out err status detail
  out="$(mktemp)"
  err="$(mktemp)"

  # stdin из /dev/null: без него claude ждёт ввод 3 секунды и падает, когда скрипт
  # запускают не из-под cron (например, вручную по SSH) — проверка врала бы.
  if [ -n "$token" ]; then
    HOME="$home" CLAUDE_CODE_OAUTH_TOKEN="$token" \
      timeout 90s claude -p --model claude-haiku-4-5 --output-format json "$PROMPT" \
      >"$out" 2>"$err" </dev/null
  else
    HOME="$home" \
      timeout 90s claude -p --model claude-haiku-4-5 --output-format json "$PROMPT" \
      >"$out" 2>"$err" </dev/null
  fi
  status=$?

  if [ "$status" -ne 0 ]; then
    # Отказ уровня аккаунта (403 «организация отключила доступ», исчерпанный лимит)
    # приходит НЕ в stderr, а телом JSON в stdout — без разбора алерт сказал бы
    # только «Код: 1», и причину пришлось бы искать руками.
    detail="$(tr '\n' ' ' <"$err" | cut -c1-400)"
    if [ -z "$detail" ] && [ -s "$out" ]; then
      detail="$(python3 - "$out" <<'PY' 2>/dev/null
import json, sys
try:
    data = json.load(open(sys.argv[1]))
except Exception:
    raise SystemExit
parts = []
if data.get("api_error_status"):
    parts.append("HTTP %s" % data["api_error_status"])
if data.get("result"):
    parts.append(str(data["result"])[:300])
print(" · ".join(parts))
PY
)"
    fi
    printf '🔴 %s: не удалось обновить окно лимитов Claude Code. Код: %s. %s\n' \
      "$name" "$status" "$detail"
    failures=$((failures + 1))
  fi

  rm -f "$out" "$err"
}

refresh 'основной аккаунт' /root ''

# Маска без совпадений раскрывается сама в себя — отсюда проверка -f.
for token_file in "$ACCOUNTS_DIR"/*/oauth_token; do
  [ -f "$token_file" ] || continue
  slug="$(basename "$(dirname "$token_file")")"
  mkdir -p "$HOMES_DIR/$slug"
  chmod 700 "$HOMES_DIR/$slug"
  refresh "аккаунт $slug" "$HOMES_DIR/$slug" "$(cat "$token_file")"
done

exit "$failures"
