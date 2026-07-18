"""Upgrade the Hermes TG agent (@albery_ai_bot) on 186:
1) kawaii -> a business 'albery' persona (system prompt with tool discipline / Маршрутная карта);
2) weekly self-review cron (Mon 10:30 MSK, agent reviews its own week via get_agent_monitoring).
Config is backed up first; YAML validated before restart; crons/toolsets/model untouched
(owner rule: gpt-5.5 medium everywhere)."""
import shutil
import subprocess
import time
from pathlib import Path

import yaml

CFG = Path("/root/.hermes/config.yaml")
ts = time.strftime("%Y%m%d_%H%M%S")
backup = CFG.with_name(f"config.yaml.bak-tg-upgrade-{ts}")
shutil.copy2(CFG, backup)
print("backup:", backup)

PERSONA = (
    "Ты — универсальный ИИ-агент компании Albery (продажи на Wildberries) и личный "
    "ассистент-разработчик владельца, Евгения. Доступ максимальный (админ): все инструменты "
    "компании — Bitrix (задачи, CRM-воронки, сообщения), база знаний, Zoom-созвоны, Google "
    "(таблицы, Drive, Apps Script), управление ИИ-агентами — плюс веб-поиск. Всегда отвечай "
    "по-русски, деловым тоном, кратко и по существу, без кавайных смайликов. Дисциплина работы: "
    "в начале работы с инструментами компании вызывай start_here_always_read_ai_instructions и "
    "следуй Маршрутной карте — правильный инструмент с первого раза, обычно 1-2 вызова, без "
    "пробных; факты проверяй инструментами, не выдумывай; чего не можешь — честно скажи и "
    "предложи путь. Необратимые действия (удаления, массовые изменения, отправка сообщений "
    "людям) — только после явного подтверждения владельца."
)

text = CFG.read_text(encoding="utf-8")
assert "personality: kawaii" in text, "anchor 'personality: kawaii' not found"
text = text.replace("personality: kawaii", "personality: albery", 1)
anchor = "  personalities:\n"
assert anchor in text, "agent.personalities anchor not found"
entry = f'  personalities:\n    albery: "{PERSONA}"\n'
text = text.replace(anchor, entry, 1)
CFG.write_text(text, encoding="utf-8")

cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
assert cfg["agent"]["personalities"]["albery"].startswith("Ты — универсальный"), "yaml parse check"
print("persona set:", cfg.get("personality"))

subprocess.run(["systemctl", "restart", "hermes-gateway"], check=True)
time.sleep(10)
state = subprocess.run(["systemctl", "is-active", "hermes-gateway"], capture_output=True, text=True)
print("hermes-gateway:", state.stdout.strip())
assert state.stdout.strip() == "active", "gateway did not come back — restore the backup!"

# weekly self-review cron (skip if present)
existing = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=60)
if "self-review" in (existing.stdout or ""):
    print("self-review cron already exists")
else:
    prompt = (
        "Еженедельный SELF-REVIEW агента Albery. Вызови get_agent_monitoring(period=\"7\") и "
        "внимательно разбери неделю: ошибки и провальные ходы (лента событий type=error), "
        "медленные ходы, сообщения «Ошибка/Предложение» от сотрудников, поле problems в здоровье "
        "систем. Составь короткий отчёт владельцу по-русски, обычным текстом: 1) что сбоило и "
        "почему — сгруппируй по паттернам, не перечисляй всё подряд; 2) что работает стабильно "
        "(одной строкой); 3) 3-5 конкретных предложений улучшений с приоритетом — что чинить "
        "первым. Если неделя чистая — скажи это одной строкой и добавь 1-2 идеи улучшений."
    )
    out = subprocess.run(["hermes", "cron", "create", "30 10 * * 1", prompt,
                          "--name", "self-review", "--deliver", "telegram"],
                         capture_output=True, text=True, timeout=60)
    print("cron create:", (out.stdout or out.stderr)[:400])

final = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True, timeout=90)
print("crons now:\n", "\n".join(ln for ln in (final.stdout or "").splitlines()
                                if "Name:" in ln or "Schedule:" in ln))
