#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест сторожа зависаний агента на РЕАЛЬНОМ журнале инцидента 2026-07-22.

Запуск: python tests/test_compaction_watchdog.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "hermes_compaction_watchdog.py")
STORM = os.path.join(ROOT, "tests", "fixtures", "journal_compaction_storm_2026-07-22.txt")

failures = []


def run(journal_file, state):
    proc = subprocess.run(
        [sys.executable, SCRIPT, "--journal-file", journal_file,
         "--state", state, "--dry-run"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def check(name, condition, detail=""):
    print(("  OK   " if condition else "  FAIL ") + name + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        failures.append(name)


with tempfile.TemporaryDirectory() as tmp:
    # 1. Реальный журнал инцидента: сторож обязан увидеть петлю.
    state = os.path.join(tmp, "state.json")
    code, out = run(STORM, state)
    check("реальный инцидент 22.07 распознан как петля сжатия",
          code == 1 and "петле сжатия" in out, out[:200])
    check("первый раз только предупреждает, не перезапускает",
          "перезапустил бы" not in out.lower(), out[:200])

    # 2. Повтор подряд -> самолечение рестартом.
    code2, out2 = run(STORM, state)
    check("при повторе перезапускает агента сам",
          "перезапустил бы hermes-gateway" in out2.lower(), out2[:200])

    # 3. Здоровый журнал -> полная тишина.
    quiet = os.path.join(tmp, "quiet.log")
    with open(quiet, "w", encoding="utf-8") as fh:
        fh.write("Jul 22 15:00:01 andigital python[1]: INFO agent: turn finished ok\n" * 40)
    code3, out3 = run(quiet, os.path.join(tmp, "state3.json"))
    check("на здоровом журнале молчит", code3 == 0 and out3.strip() == "", out3[:200])

    # 4. Файл состояния действительно пишется (иначе самолечение не сработает).
    with open(state, encoding="utf-8") as fh:
        saved = json.load(fh)
    check("состояние сохраняется между запусками", saved.get("storm_seen") is True, str(saved))

print()
if failures:
    print("ТЕСТЫ УПАЛИ:", ", ".join(failures))
    sys.exit(1)
print("ВСЕ ТЕСТЫ ЗЕЛЁНЫЕ")
