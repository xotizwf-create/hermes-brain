#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Armed runner: wait until НСПД opens (VPN OFF -> RU residential IP), then run the
COMPLETE radius extraction for both target parcels and write two .xlsx files.

Survives the VPN-off window (DNS-free, direct IP). Read the result afterwards.
"""
import json, os, subprocess, sys, time

from pynspd import Nspd

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "scripts", "nspd_parcels_local.py")
RADIUS = "50"
DEADLINE_MIN = 25
PROBE = "18:30:000148:8"   # one of our targets, used as reachability probe

JOBS = [
    ("18:26:041310:31", "Склад_Ижевск_Нагорная3_50м_18-26-041310-31.xlsx"),
    ("18:30:000148:8",  "Промплощадка2_Сарапул_КрасныйПроезд1_50м_18-30-000148-8.xlsx"),
]
STATUS = os.path.join(HERE, "_nspd_run_status.json")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def wait_until_reachable():
    t0 = time.time()
    attempt = 0
    with Nspd(client_dns_resolve=True, client_retry_on_blocked_ip=True) as nspd:
        while time.time() - t0 < DEADLINE_MIN * 60:
            attempt += 1
            try:
                if nspd.find_landplot(PROBE) is not None:
                    log(f"NSPD reachable on attempt {attempt} (~{int(time.time()-t0)}s)")
                    return True
            except Exception as e:
                log(f"attempt {attempt}: not ready ({type(e).__name__})")
            time.sleep(5)
    return False


def main():
    results = []
    if not wait_until_reachable():
        with open(STATUS, "w", encoding="utf-8") as fh:
            json.dump({"ok": False, "error": "timeout: NSPD never reachable (VPN still on?)"},
                      fh, ensure_ascii=False, indent=2)
        log("TIMEOUT"); return
    for cad, fname in JOBS:
        out = os.path.join(HERE, fname)
        log(f"== running {cad} radius {RADIUS} -> {fname} ==")
        proc = subprocess.run(
            [sys.executable, SCRIPT, cad, "--radius", RADIUS, "--objects", "all",
             "--ip-mode", "--out", out],
            capture_output=True, text=True, encoding="utf-8",
        )
        log(proc.stderr[-2000:] if proc.stderr else "(no stderr)")
        entry = {"cad": cad, "file": fname, "returncode": proc.returncode}
        try:
            entry["summary"] = json.loads((proc.stdout or "").strip().splitlines()[-1])
        except Exception:
            entry["summary"] = None
            entry["stdout_tail"] = (proc.stdout or "")[-500:]
        results.append(entry)
        with open(STATUS, "w", encoding="utf-8") as fh:
            json.dump({"ok": True, "results": results}, fh, ensure_ascii=False, indent=2)
    log("ALL DONE")
    print(json.dumps({"ok": True, "results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
