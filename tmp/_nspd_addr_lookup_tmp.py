#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Armed address->cadastral lookup via official НСПД (pynspd), DNS-free (direct IP).

Polls until НСПД is reachable (run with the PC's VPN OFF -> real RU residential IP),
then text-searches each address, dumps candidate objects (cad_num, type, address,
area) to _nspd_addr_candidates.json. Survives the VPN-off window so the Claude
session can drop and the result is read afterwards.
"""
import json, sys, time, traceback

from pynspd import Nspd

OUT = "_nspd_addr_candidates.json"
DEADLINE_MIN = 25

# (label, [query variants tried in order until one returns hits])
TARGETS = [
    ("Промплощадка 2 (Сарапул, Красный проезд, 1)", [
        "Удмуртская Республика, г. Сарапул, ул. Красный проезд, д. 1",
        "Удмуртская Республика, г Сарапул, ул Красный проезд, д 1",
        "Сарапул, Красный проезд, 1",
    ]),
    ("Склад г. Ижевска (Нагорная, 3)", [
        "Удмуртская Республика, г. Ижевск, ул. Нагорная, д. 3",
        "Удмуртская Республика, г Ижевск, ул Нагорная, д 3",
        "Ижевск, Нагорная, 3",
    ]),
]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def feat_brief(f):
    p = getattr(f, "properties", None)
    o = getattr(p, "options", None) if p else None
    od = {}
    if o is not None:
        od = o if isinstance(o, dict) else (o.model_dump() if hasattr(o, "model_dump") else {})
    cat = getattr(p, "category_name", None) or getattr(p, "category", None)
    return {
        "cad_num": od.get("cad_num") or od.get("cad_number") or getattr(f, "cadastral_number", None),
        "category": cat,
        "type": od.get("land_record_type") or od.get("build_record_type_value")
                 or od.get("land_record_category_type") or "",
        "address": od.get("readable_address") or "",
        "area": od.get("specified_area") or od.get("declared_area") or od.get("area") or "",
        "permitted_use": od.get("permitted_use_established_by_document") or od.get("permitted_use") or "",
    }


def run_lookups(nspd):
    result = []
    for label, variants in TARGETS:
        entry = {"label": label, "tried": [], "candidates": []}
        for q in variants:
            entry["tried"].append(q)
            try:
                feats = nspd.search(q) or []
            except Exception as e:
                log(f"  [{label}] query {q!r} error: {e}")
                continue
            if feats:
                entry["query_hit"] = q
                entry["candidates"] = [feat_brief(f) for f in feats]
                log(f"  [{label}] {len(feats)} hit(s) on {q!r}")
                break
            else:
                log(f"  [{label}] 0 hits on {q!r}")
        result.append(entry)
    return result


def main():
    t0 = time.time()
    with Nspd(client_dns_resolve=True, client_retry_on_blocked_ip=True) as nspd:
        attempt = 0
        while time.time() - t0 < DEADLINE_MIN * 60:
            attempt += 1
            try:
                # cheap reachability probe: a known parcel from last session
                probe = nspd.find_landplot("18:30:000423:1789")
                if probe is not None:
                    log(f"NSPD reachable on attempt {attempt} (~{int(time.time()-t0)}s). Searching...")
                    res = run_lookups(nspd)
                    with open(OUT, "w", encoding="utf-8") as fh:
                        json.dump({"ok": True, "results": res}, fh, ensure_ascii=False, indent=2)
                    log(f"DONE -> {OUT}")
                    print(json.dumps({"ok": True, "out": OUT}, ensure_ascii=False))
                    return
            except Exception as e:
                log(f"attempt {attempt}: not ready ({type(e).__name__}: {e})")
            time.sleep(5)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"ok": False, "error": "timeout: NSPD never became reachable (VPN still on?)"},
                  fh, ensure_ascii=False, indent=2)
    log("TIMEOUT — NSPD never reachable")
    print(json.dumps({"ok": False}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
