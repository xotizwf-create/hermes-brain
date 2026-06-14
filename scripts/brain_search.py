#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brain_search.py — one search across BOTH of the agent's knowledge trees:
  1. the versioned brain  (agent-knowledge/: docs + our custom skills)
  2. Hermes' bundled skill library (/root/.hermes/skills/: research, devops, ...)

Why: the agent kept opening the wrong skill / not finding knowledge that existed,
because knowledge and skills live in separate trees and there was no unified search.
Run this BEFORE concluding "I don't know" or picking a skill.

Lexical-first (no embeddings): SQLite FTS5 (bm25, field-weighted) + a trigram fuzzy
fallback for typos/Russian morphology. Re-rank by exact tag/name hits. Tiny corpus
(~150 docs) → precise keyword retrieval beats vectors here; vectors can be added later.

Usage:
  python brain_search.py "участки росреестр в радиусе"     # query (auto-builds index if stale)
  python brain_search.py --build                            # (re)build the index
  python brain_search.py --roots /a,/b "query" --top 8
"""
import argparse, os, re, sqlite3, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_ROOTS = [
    "/root/.hermes/agent-knowledge",   # tree 1: versioned brain (docs + custom skills)
    "/root/.hermes/skills",            # tree 2: Hermes bundled skill library
]
DEFAULT_DB = "/root/.hermes/cache/brain_index.sqlite"
SKIP_DIRS = {".git", "node_modules", "__pycache__", "archive", ".obsidian"}
DOC_EXT = (".md", ".yaml", ".yml")


def classify(path, root):
    low = path.replace("\\", "/").lower()
    name = os.path.basename(path)
    if name.lower() == "skill.md":
        kind = "skill"
    elif "/references/" in low:
        kind = "reference"
    elif "/skills/" in low:
        kind = "skill-file"
    elif name == "INDEX.md" or name == "CLAUDE.md" or name == "MEMORY.md":
        kind = "index"
    elif "/logs/" in low:
        kind = "log"
    else:
        kind = "doc"
    versioned = "/agent-knowledge/" in low or os.path.basename(root.rstrip("/")) != "skills"
    return kind, ("versioned" if versioned else "bundled")


def parse_doc(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except Exception:
        return None
    title = tags = desc = ""
    body = raw
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if m:
        fm, body = m.group(1), m.group(2)
        for line in fm.splitlines():
            ls = line.strip()
            if ls.lower().startswith("name:"):
                title = title or ls.split(":", 1)[1].strip().strip('"')
            elif ls.lower().startswith(("description:", "hook:", "summary:")):
                desc = desc or ls.split(":", 1)[1].strip().strip('"')
            elif ls.lower().startswith("tags:"):
                tags = ls.split(":", 1)[1].strip().strip("[]")
    if not title:
        h = re.search(r"^#\s+(.+)$", body, re.M)
        title = h.group(1).strip() if h else os.path.basename(path)
    return title, tags, desc, body[:20000]


def iter_docs(roots):
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if fn.endswith(DOC_EXT):
                    p = os.path.join(dirpath, fn)
                    parsed = parse_doc(p)
                    if parsed:
                        kind, origin = classify(p, root)
                        yield (p, kind, origin) + parsed


def build_index(roots, db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS docs;
        CREATE VIRTUAL TABLE docs USING fts5(
            title, tags, description, body,
            path UNINDEXED, kind UNINDEXED, origin UNINDEXED,
            tokenize='unicode61 remove_diacritics 2'
        );
        DROP TABLE IF EXISTS meta;
        CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
    """)
    n = 0
    for (path, kind, origin, title, tags, desc, body) in iter_docs(roots):
        cur.execute("INSERT INTO docs(title,tags,description,body,path,kind,origin) VALUES (?,?,?,?,?,?,?)",
                    (title, tags, desc, body, path, kind, origin))
        n += 1
    # trigram table for fuzzy fallback (typos / morphology)
    has_trigram = True
    try:
        cur.execute("DROP TABLE IF EXISTS tri")
        cur.execute("CREATE VIRTUAL TABLE tri USING fts5(title, tags, body, path UNINDEXED, tokenize='trigram')")
        cur.execute("INSERT INTO tri(title,tags,body,path) SELECT title,tags,body,path FROM docs")
    except sqlite3.OperationalError:
        has_trigram = False
    cur.execute("INSERT OR REPLACE INTO meta VALUES('built_at',?)", (str(time.time()),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('count',?)", (str(n),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('roots',?)", (";".join(roots),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('trigram',?)", ("1" if has_trigram else "0",))
    con.commit(); con.close()
    return n, has_trigram


def _fts_query(terms):
    # OR the terms; quote each to avoid FTS5 syntax errors on punctuation
    parts = []
    for t in terms:
        t = t.replace('"', '')
        if t:
            parts.append(f'"{t}"')
    return " OR ".join(parts)


def search(db_path, query, top=8):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    terms = [t for t in re.split(r"[\s,/]+", query.strip()) if len(t) >= 2]
    seen, results = set(), []
    try:
        q = _fts_query(terms)
        rows = cur.execute(
            "SELECT path, kind, origin, title, "
            "snippet(docs, 3, '«', '»', ' … ', 12), "
            "bm25(docs, 10.0, 8.0, 6.0, 1.0) AS r "
            "FROM docs WHERE docs MATCH ? ORDER BY r LIMIT ?",
            (q, top * 2)).fetchall()
        # prefer how-to docs (skills/references/docs) over logs/index for routing
        KIND_W = {"skill": -3.0, "reference": -2.5, "skill-file": -2.0, "doc": -1.0,
                  "index": 0.0, "log": 1.5}
        for (path, kind, origin, title, snip, r) in rows:
            if path in seen:
                continue
            seen.add(path)
            # re-rank bonus: exact term in title/path
            bonus = sum(1 for t in terms if t.lower() in (title or "").lower() or t.lower() in path.lower())
            results.append((r - bonus * 2.0 + KIND_W.get(kind, 0.0), path, kind, origin, title, snip))
    except sqlite3.OperationalError as e:
        print(f"(fts error: {e})", file=sys.stderr)
    # fuzzy fallback if thin
    if len(results) < 3:
        trigram = cur.execute("SELECT v FROM meta WHERE k='trigram'").fetchone()
        if trigram and trigram[0] == "1":
            for t in terms:
                if len(t) < 3:
                    continue
                for (path, kind, origin, title) in cur.execute(
                        "SELECT d.path,d.kind,d.origin,d.title FROM tri JOIN docs d ON d.path=tri.path "
                        "WHERE tri MATCH ? LIMIT 5", (f'"{t}"',)).fetchall():
                    if path not in seen:
                        seen.add(path)
                        results.append((100.0, path, kind, origin, title, "(fuzzy match)"))
    con.close()
    results.sort(key=lambda x: x[0])
    return results[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--roots", default=os.environ.get("BRAIN_ROOTS", ",".join(DEFAULT_ROOTS)))
    ap.add_argument("--db", default=os.environ.get("BRAIN_DB", DEFAULT_DB))
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--max-age", type=int, default=3600, help="rebuild if index older than N seconds")
    args = ap.parse_args()
    roots = [r for r in args.roots.split(",") if r.strip()]

    stale = not os.path.exists(args.db)
    if not stale and not args.build:
        try:
            con = sqlite3.connect(args.db)
            built = float(con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()[0])
            con.close()
            stale = (time.time() - built) > args.max_age
        except Exception:
            stale = True
    if args.build or stale:
        n, tri = build_index(roots, args.db)
        print(f"[indexed {n} docs from {len(roots)} roots; trigram={'on' if tri else 'off'}]", file=sys.stderr)
        if args.build and not args.query:
            return

    if not args.query:
        ap.error("provide a query (or --build)")
    res = search(args.db, args.query, args.top)
    if not res:
        print("No matches. Try other keywords or `--build` to refresh the index.")
        return
    for i, (score, path, kind, origin, title, snip) in enumerate(res, 1):
        print(f"{i}. [{kind}/{origin}] {title}")
        print(f"   {path}")
        if snip and snip != "(fuzzy match)":
            print(f"   … {snip}")
        elif snip:
            print(f"   {snip}")


if __name__ == "__main__":
    main()
