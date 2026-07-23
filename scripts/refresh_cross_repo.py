#!/usr/bin/env python3
"""Пересобрать кросс-репо картину связей Hermes Brain <-> Albery.

Что делает (быстрый путь, без затрат на LLM):
  1. берёт уже построенные графы graphify обоих репо (graphify-out/graph.json);
  2. сливает их (`graphify merge-graphs`) в cross-repo-graph.json;
  3. вычисляет "мосты" между репозиториями по совпадающим сущностям
     (graphify НЕ строит рёбра между репо — связь считается здесь);
  4. классифицирует мосты по трём слоям (документирование / рантайм-вызов /
     общая инфраструктура) и регенерирует интерактивную визуализацию
     graphify-out/cross-repo.html из scripts/cross_repo_template.html.

Использование:
  python scripts/refresh_cross_repo.py            # быстро: только merge+мосты+HTML
  python scripts/refresh_cross_repo.py --reindex  # + AST-переиндексация обоих репо
                                                   #   (код; доки этим не обновляются)

Полный семантический проход по докам (нужен модели, поэтому отдельно и не тут):
  graphify extract . --backend claude-cli --no-viz   # в каждом репо

Пути: brain = папка с этим репо; albery = соседняя папка ../Albery
(переопределяется флагами --brain / --albery).
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys, collections
from pathlib import Path

BRAIN = Path(__file__).resolve().parent.parent
ALBERY_DEFAULT = BRAIN.parent / "Albery"

# --- инфраструктурные концепты, общие для обоих проектов (описаны с двух сторон) ---
SHARED_INFRA = [
    "Bitrix24 webhooks", "Hermes gateway (217.198.12.236)", "MCP-контракт",
    "PostgreSQL albery", "Zoom /zoom/events", "Google Drive /google-drive/events",
    "Nginx m4s.ru", "cron zoom-to-tasks",
]
# --- прямые рантайм-зацепки: код Albery, обращающийся к мозгу ---
RUNTIME_HOOKS = [
    ("hermes_brain_answer()", "b24bot.py — прогоняет ход через локальный Hermes-мозг"),
    ("agent_knowledge.py", "загрузчик GitHub-реестра знаний (тот же git, что и мозг)"),
]


def gfy(*args: str) -> None:
    """Вызвать graphify через `python -m graphify` — не зависит от PATH."""
    subprocess.run([sys.executable, "-m", "graphify", *args], check=True)


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9а-я]+", "", (s or "").lower())


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def compute_bridges(merged: dict) -> tuple[list, dict]:
    """Совпадающие по имени сущности из разных репо = мосты."""
    A: dict[str, list] = {}
    H: dict[str, list] = {}
    for n in merged["nodes"]:
        (A if n.get("repo") == "Albery" else H).setdefault(
            norm(n.get("norm_label") or n.get("label")), []).append(n)
    bridges = []
    for k in set(A) & set(H):
        if len(k) < 4:
            continue
        a, h = A[k][0], H[k][0]
        hs = h.get("source_file") or ""
        kind = ("doc-of-albery" if hs.startswith("projects/albery")
                else "infra" if h.get("file_type") == "concept" else "shared-helper")
        bridges.append({"label": a.get("label"), "alb": a.get("source_file"),
                        "brain": hs, "kind": kind})
    # brain-doc -> {albery_file: count}
    docmap: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for b in bridges:
        if b["kind"] == "doc-of-albery":
            docmap[b["brain"]][b["alb"]] += 1
    return bridges, docmap


def build_viz(bridges: list, docmap: dict, brain_n: int, albery_n: int) -> dict:
    nodes, links = [], []
    def add(i, label, repo, kind, meta=""):
        nodes.append({"id": i, "label": label, "repo": repo, "kind": kind, "meta": meta})

    add("brain", "Hermes Brain", "hermes-brain", "hub",
        f"мозг агента: {brain_n} узлов")
    add("albery", "Albery", "Albery", "hub", f"боевая система: {albery_n} узлов")

    seen_files = set()
    for braindoc, files in docmap.items():
        did = "D:" + braindoc
        add(did, braindoc.replace("projects/albery/", ""), "hermes-brain", "doc",
            f"{sum(files.values())} задокумент. сущностей")
        links.append({"s": "brain", "t": did, "type": "owns"})
        for f, c in files.items():
            fid = "F:" + f
            if fid not in seen_files:
                add(fid, f, "Albery", "file"); seen_files.add(fid)
                links.append({"s": "albery", "t": fid, "type": "owns"})
            links.append({"s": did, "t": fid, "type": "documents", "w": c})

    for label, meta in RUNTIME_HOOKS:
        rid = "RT:" + label
        add(rid, label, "Albery", "runtime", meta)
        links.append({"s": "albery", "t": rid, "type": "owns"})
        links.append({"s": rid, "t": "brain", "type": "calls"})

    for i, name in enumerate(SHARED_INFRA):
        iid = "I:" + str(i)
        add(iid, name, "shared", "infra")
        links.append({"s": "brain", "t": iid, "type": "shares"})
        links.append({"s": "albery", "t": iid, "type": "shares"})

    n_bridges = sum(1 for b in bridges if b["kind"] == "doc-of-albery")
    return {"nodes": nodes, "links": links,
            "stats": {"brain_nodes": brain_n, "albery_nodes": albery_n,
                      "total": brain_n + albery_n, "bridges": n_bridges,
                      "infra": len(SHARED_INFRA)}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brain", default=str(BRAIN), type=Path)
    ap.add_argument("--albery", default=str(ALBERY_DEFAULT), type=Path)
    ap.add_argument("--reindex", action="store_true",
                    help="перед слиянием обновить AST-графы обоих репо (только код)")
    args = ap.parse_args()

    brain, albery = args.brain.resolve(), args.albery.resolve()
    bg = brain / "graphify-out" / "graph.json"
    ag = albery / "graphify-out" / "graph.json"

    if args.reindex:
        print("[refresh] AST-переиндексация обоих репо (код)…")
        gfy("update", str(brain)); gfy("update", str(albery))

    for p in (bg, ag):
        if not p.exists():
            sys.exit(f"[refresh] нет графа: {p}\n  собери его: "
                     f"cd {p.parent.parent} && graphify extract . --backend claude-cli --no-viz")

    out = brain / "graphify-out" / "cross-repo-graph.json"
    print("[refresh] слияние графов…")
    gfy("merge-graphs", str(bg), str(ag), "--out", str(out))

    merged = load(out)
    brain_n = sum(1 for n in merged["nodes"] if n.get("repo") == "hermes-brain")
    albery_n = sum(1 for n in merged["nodes"] if n.get("repo") == "Albery")

    bridges, docmap = compute_bridges(merged)
    n_doc = sum(1 for b in bridges if b["kind"] == "doc-of-albery")
    print(f"[refresh] мостов «док↔код»: {n_doc}  ·  brain={brain_n}  albery={albery_n}")

    viz = build_viz(bridges, docmap, brain_n, albery_n)
    tpl = (Path(__file__).parent / "cross_repo_template.html").read_text(encoding="utf-8")
    html = tpl.replace("__DATA__", json.dumps(viz, ensure_ascii=False))
    dest = brain / "graphify-out" / "cross-repo.html"
    dest.write_text(html, encoding="utf-8", newline="\n")
    (brain / "graphify-out" / "_bridges.json").write_text(
        json.dumps(bridges, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[refresh] визуализация: {dest}")
    print("[refresh] готово. Открой cross-repo.html в браузере или переопубликуй артефакт.")


if __name__ == "__main__":
    main()
