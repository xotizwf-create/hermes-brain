#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hermes_selfcheck.py — surface the agent's SILENT degradations so they stop looking like
"the model got dumb". Scans the hermes-gateway journal for the failure signatures we've
actually hit, and prints a concise Russian alert ONLY if something crossed a threshold
(empty output = all good → a cron delivers nothing).

Intended as an hourly cron alongside self-review. Quiet unless actionable.

Signatures (grounded in the real journal, 2026-06-14):
  - SOUL/context blocked by the exfil scanner  -> agent silently loses its system rules
  - Codex auth invalid (token_invalidated)     -> the ChatGPT "brain" drops out (blocker #1)
  - aux provider marked unhealthy              -> Groq rate limits kill titles/approval/compression
  - context compression/compaction failing     -> degraded multi-turn behaviour, slow turns
  - media/attachment drop                      -> "I sent the file" but nothing arrives
"""
import argparse, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# key -> (regex, alert-threshold for the window, human label, severity)
CHECKS = {
    "soul_blocked":  (r"Context file .*blocked|SOUL\.md blocked|exfil_?curl", 1,
                      "SOUL.md/системные правила вырезаются сканером (агент теряет инструкции)", "CRIT"),
    "codex_limit":   (r"usage_limit_reached|usage limit reached|plan_type.*resets_in", 1,
                      "Codex/ChatGPT ЛИМИТ исчерпан — агент не отвечает до сброса (один аккаунт без фолбэка)", "CRIT"),
    "codex_auth":    (r"token_invalidated|auth(entication)?[^a-z]*invalid|401 Unauthorized|missing access_token|refresh_token_reused|credential_pool_refresh_failure|Primary provider auth failed|relogin_required", 1,
                      "Codex (основной мозг) ПОТЕРЯЛ авторизацию (token_invalidated / refresh_token_reused / missing access_token) — нужен hermes auth add openai-codex", "CRIT"),
    "media_drop":    (r"Skipping unsafe MEDIA|unsafe MEDIA", 1,
                      "вложения молча дропаются (файл «отправлен», но не дошёл)", "CRIT"),
    "provider_unhealthy": (r"marking .*unhealthy|provider .*unhealthy", 8,
                      "вспомогательный провайдер (Groq) уходит в unhealthy — лимиты токенов/мин", "WARN"),
    "compression_fail": (r"compress(ion)?.*(fail|error|timeout)|compaction.*(fail|error)|summar(y|ize|ization).*(fail|timeout)|failed to generate context summary", 1,
                      "сжатие/компакция контекста падает (тупит/медленные ходы)", "WARN"),
}


def _since_arg(minutes):
    """Look back at most `minutes`, but after a config repair don't re-alert on stale pre-fix lines."""
    window_start = time.time() - minutes * 60
    cfg_path = "/root/.hermes/config.yaml"
    try:
        window_start = max(window_start, os.path.getmtime(cfg_path))
    except OSError:
        pass
    return "@" + str(int(window_start))


def journal(minutes):
    try:
        out = subprocess.run(
            ["journalctl", "-u", "hermes-gateway", "--since", _since_arg(minutes), "--no-pager"],
            capture_output=True, text=True, timeout=60).stdout
        return out.splitlines()
    except Exception as e:
        print(f"selfcheck: cannot read journal: {e}", file=sys.stderr)
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=70, help="lookback window (hourly cron ~70)")
    ap.add_argument("--always", action="store_true", help="print a summary even if all-clear")
    args = ap.parse_args()

    lines = journal(args.minutes)
    hits = {}
    for key, (pat, thr, label, sev) in CHECKS.items():
        rx = re.compile(pat, re.I)
        matched = [ln for ln in lines if rx.search(ln)]
        if matched:
            hits[key] = (len(matched), matched[-1], thr, label, sev)

    alerts = {k: v for k, v in hits.items() if v[0] >= v[2]}
    if not alerts and not args.always:
        return  # silent: nothing actionable

    if not alerts:
        print(f"✅ Hermes self-check ({args.minutes//60}ч): тихо, сигнатур сбоев нет.")
        return

    explanations = {
        "soul_exfil": (
            "Я мог потерять часть системных правил при ответе.",
            "Если ответы стали странными или непоследовательными — лучше перезапустить Hermes и проверить журнал безопасности."
        ),
        "codex_auth": (
            "Слетела авторизация ChatGPT/Codex, поэтому основная модель могла не отвечать.",
            "Нужно заново проверить вход в Codex/ChatGPT."
        ),
        "telegram_send_fail": (
            "Telegram временно не принял одно или несколько сообщений.",
            "Обычно это сетевой таймаут; если повторяется — проверить связь с Telegram и ретраи отправки."
        ),
        "provider_unhealthy": (
            "Вспомогательная модель была нестабильна или упёрлась в лимиты.",
            "Это может ломать заголовки, сжатие контекста и мелкие фоновые операции; если повторяется — сменить или разгрузить вспомогательный провайдер."
        ),
        "compression_fail": (
            "Не получилось сжать длинный диалог для продолжения работы.",
            "Из-за этого я могу тормозить или хуже помнить длинный контекст; если будет мешать — начать новый диалог или проверить модель для сжатия."
        ),
    }

    crit = [v for v in alerts.values() if v[4] == "CRIT"]
    head = "🔴" if crit else "🟠"
    print(f"{head} Самопроверка Hermes: есть сбои за последний час")
    print("")
    for key, (n, sample, thr, label, sev) in sorted(alerts.items(), key=lambda kv: kv[1][4]):
        mark = "‼️" if sev == "CRIT" else "•"
        what_happened, what_to_do = explanations.get(key, (label, "Если повторится — посмотреть журнал Hermes."))
        print(f"{mark} {what_happened}")
        print(f"   Повторов: {n}")
        print(f"   Что сделать: {what_to_do}")
    print("")
    print("Технический лог не прикладываю, чтобы не засорять чат. Если нужно — я сам открою его при разборе.")


if __name__ == "__main__":
    main()
