#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brain_search.py — one hybrid search across BOTH of the agent's knowledge trees:
  1. the versioned brain  (agent-knowledge/: docs + our custom skills)
  2. Hermes' bundled skill library (/root/.hermes/skills/: research, devops, ...)

Run this BEFORE concluding "I don't know" or picking a skill. It returns the most
relevant *passages* (section-level chunks), not whole files — so the agent reads a
paragraph, not a document. This is the token-frugal way to load instructions/skills.

Retrieval = HYBRID:
  - lexical  : SQLite FTS5 (bm25, field-weighted) over chunks  (exact terms, fast)
  - semantic : Voyage embeddings (voyage-3.5, multilingual RU+EN) + cosine  (meaning/synonyms)
  - fused with Reciprocal Rank Fusion, then re-ranked by kind + exact title/path hits.

Embeddings are HOSTED (Voyage) → zero RAM on the box. Vectors live in the same SQLite
file (float32 blobs); cosine is brute-force (corpus is small → instant). Re-embedding is
INCREMENTAL — only chunks whose text changed are sent to the API. If the Voyage key or
network is unavailable, search degrades gracefully to lexical-only (never breaks).

Usage:
  python brain_search.py "участки росреестр в радиусе"     # query (auto-builds if stale)
  python brain_search.py --build                            # (re)build the index
  python brain_search.py --build --no-embed                 # rebuild lexical only (skip API)
  python brain_search.py --roots /a,/b "query" --top 8
"""
import argparse, hashlib, json, math, os, re, sqlite3, struct, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_ROOTS = [
    "/root/.hermes/agent-knowledge",   # tree 1: versioned brain (docs + custom skills)
    "/root/.hermes/skills",            # tree 2: Hermes bundled skill library
]
DEFAULT_DB = "/root/.hermes/cache/brain_index.sqlite"
SKIP_DIRS = {".git", "node_modules", "__pycache__", "archive", ".obsidian",
             "vendor-skills"}  # vendor-skills/ = backup mirror of the bundled library → skip (dedup)
DOC_EXT = (".md", ".yaml", ".yml")

# Common RU/EN stop-words: dropped from LEXICAL query terms so BM25 focuses on content
# words (the full query is still used verbatim for the semantic embedding).
STOPWORDS = set("""
и в во не что он на я с со как а то все всё она так его но да ты к у же вы за бы по только
ее её мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть
был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть надо
ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под будет тогда кто этот того
потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем
всех никогда можно при наконец два об другой хоть после над больше тот через эти нас про всего
них какая много разве эту моя впрочем хорошо свою этой перед иногда лучше чуть том нельзя такой
им более всегда конечно всю между делать сделать нужно надо чтобы если когда где это эти этот
the a an of to in is it for on with as at by be this that or and from your you our we how do does
not what when where which can should will would make need use using
""".split())


def query_terms(query):
    return [t for t in re.split(r"[\s,/]+", query.strip())
            if len(t) >= 2 and t.lower() not in STOPWORDS]


# Embedding provider — "gemini" (free, generous, multilingual) or "voyage".
EMBED_PROVIDER = os.environ.get("EMBED_PROVIDER", "gemini")
VOYAGE_KEY_FILE = os.environ.get("VOYAGE_KEY_FILE", "/root/.hermes/secure/voyage_api_key")
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-3.5")
VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
GEMINI_KEY_FILE = os.environ.get("GEMINI_KEY_FILE", "/root/.hermes/secure/gemini_api_key")
GEMINI_KEYS_FILE = os.environ.get("GEMINI_KEYS_FILE", "/root/.hermes/secure/gemini_api_keys")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-embedding-001")
GEMINI_DIM = int(os.environ.get("GEMINI_DIM", "1536"))
CHUNK_MAX = 1800          # max chars per chunk before windowing
EMBED_BATCH = int(os.environ.get("EMBED_BATCH", "64"))            # texts per request
EMBED_THROTTLE = float(os.environ.get("EMBED_THROTTLE", "0.4"))   # seconds between batches
EMBED_MODEL_NAME = GEMINI_MODEL if EMBED_PROVIDER == "gemini" else VOYAGE_MODEL

try:
    import numpy as _np
except Exception:
    _np = None


# ---------------- parsing & chunking ----------------

def classify(path, root):
    low = path.replace("\\", "/").lower()
    name = os.path.basename(path)
    if name.lower() == "skill.md":
        kind = "skill"
    elif "/references/" in low:
        kind = "reference"
    elif "/skills/" in low:
        kind = "skill-file"
    elif name in ("INDEX.md", "CLAUDE.md", "MEMORY.md"):
        kind = "index"
    elif "/logs/" in low:
        kind = "log"
    else:
        kind = "doc"
    versioned = "/agent-knowledge/" in low or os.path.basename(root.rstrip("/")) != "skills"
    return kind, ("versioned" if versioned else "bundled")


def parse_frontmatter(raw):
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
        title = h.group(1).strip() if h else ""
    return title, tags, desc, body


def _windows(text, size=CHUNK_MAX):
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size
    return out


def chunk_doc(path):
    """Yield (section_heading, chunk_text) split by H2/H3; long sections windowed."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except Exception:
        return None
    title, tags, desc, body = parse_frontmatter(raw)
    if not title:
        title = os.path.basename(path)
    # split into sections by markdown headings (## / ###); keep H1 intro too
    sections, cur_head, cur_lines = [], "", []
    for line in body.splitlines():
        hm = re.match(r"^(#{1,3})\s+(.+)$", line)
        if hm:
            if cur_lines:
                sections.append((cur_head, "\n".join(cur_lines).strip()))
            cur_head = hm.group(2).strip()
            cur_lines = []
        else:
            cur_lines.append(line)
    if cur_lines:
        sections.append((cur_head, "\n".join(cur_lines).strip()))
    if not sections:
        sections = [("", body.strip())]
    chunks = []
    for head, text in sections:
        if not text and not head:
            continue
        for w in _windows(text) or ([""] if head else []):
            body_txt = (head + "\n" + w).strip() if head else w
            if len(body_txt) < 15:
                continue
            chunks.append((head, body_txt))
    return title, tags, desc, chunks


def iter_chunks(roots):
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if not fn.endswith(DOC_EXT):
                    continue
                p = os.path.join(dirpath, fn)
                parsed = chunk_doc(p)
                if not parsed:
                    continue
                title, tags, desc, chunks = parsed
                kind, origin = classify(p, root)
                for head, text in chunks:
                    yield (p, kind, origin, title, tags, head, text)


# ---------------- embeddings (Gemini / Voyage) ----------------

def _read_key():
    path = GEMINI_KEY_FILE if EMBED_PROVIDER == "gemini" else VOYAGE_KEY_FILE
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return os.environ.get("GEMINI_API_KEY" if EMBED_PROVIDER == "gemini" else "VOYAGE_API_KEY", "").strip()


def _read_keys():
    """Key POOL — multiple Gemini keys (one per line) multiply the free daily quota;
    the embedder rotates to the next key when one is quota-exhausted."""
    if EMBED_PROVIDER == "gemini":
        try:
            with open(GEMINI_KEYS_FILE) as f:
                ks = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
            if ks:
                return ks
        except Exception:
            pass
    k = _read_key()
    return [k] if k else []


def _voyage_call(batch, key, input_type, max_retries=8):
    """One batch with backoff on 429/5xx. Returns list of embeddings or None."""
    payload = json.dumps({"input": batch, "model": VOYAGE_MODEL,
                          "input_type": input_type}).encode("utf-8")
    delay = 6.0
    for attempt in range(max_retries):
        req = urllib.request.Request(VOYAGE_URL, data=payload, method="POST",
                                     headers={"Authorization": "Bearer " + key,
                                              "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read().decode("utf-8"))
            return [item["embedding"] for item in sorted(d.get("data", []), key=lambda x: x.get("index", 0))]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < max_retries - 1:
                ra = e.headers.get("Retry-After")
                wait = float(ra) if ra and ra.isdigit() else delay
                print(f"(voyage {e.code}; retry in {wait:.0f}s)", file=sys.stderr)
                time.sleep(wait); delay = min(delay * 2, 60); continue
            print(f"(voyage embed failed: HTTP {e.code})", file=sys.stderr)
            return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay); delay = min(delay * 2, 60); continue
            print(f"(voyage embed failed: {e})", file=sys.stderr)
            return None
    return None


def _gemini_call(batch, key, input_type, max_retries=6):
    """One batch via Gemini batchEmbedContents. Returns list of embeddings or None."""
    task = "RETRIEVAL_QUERY" if input_type == "query" else "RETRIEVAL_DOCUMENT"
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}"
           f":batchEmbedContents?key={key}")
    reqs = [{"model": f"models/{GEMINI_MODEL}", "content": {"parts": [{"text": t}]},
             "taskType": task, "outputDimensionality": GEMINI_DIM} for t in batch]
    payload = json.dumps({"requests": reqs}).encode("utf-8")
    delay = 4.0
    for attempt in range(max_retries):
        req = urllib.request.Request(url, data=payload, method="POST",
                                     headers={"content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode("utf-8"))
            return [e["values"] for e in d.get("embeddings", [])], False
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:200]
            except Exception:
                pass
            if e.code == 429 and "quota" in body.lower():
                return None, True   # daily quota exhausted → caller rotates to next key
            if e.code in (429, 500, 503) and attempt < max_retries - 1:
                print(f"(gemini {e.code}; retry in {delay:.0f}s)", file=sys.stderr)
                time.sleep(delay); delay = min(delay * 2, 45); continue
            print(f"(gemini embed failed: HTTP {e.code} {body})", file=sys.stderr)
            return None, False
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay); delay = min(delay * 2, 45); continue
            print(f"(gemini embed failed: {e})", file=sys.stderr)
            return None, False
    return None, False


def _provider_call(batch, key, input_type):
    if EMBED_PROVIDER == "gemini":
        return _gemini_call(batch, key, input_type)
    return _voyage_call(batch, key, input_type), False


def embed_texts(texts, key, input_type, throttle=EMBED_THROTTLE):
    """Unit-normalized vectors. Rotates across the key pool when a key is quota-exhausted.
    Returns AS MANY AS SUCCEEDED (partial → resume next build)."""
    keys = _read_keys() or ([key] if key else [])
    if not keys or not texts:
        return []
    out, ki = [], 0
    total = (len(texts) + EMBED_BATCH - 1) // EMBED_BATCH
    for bi, i in enumerate(range(0, len(texts), EMBED_BATCH)):
        batch = texts[i:i + EMBED_BATCH]
        embs = None
        while ki < len(keys):
            embs, quota = _provider_call(batch, keys[ki], input_type)
            if embs or not quota:
                break
            print(f"(key #{ki + 1} quota exhausted → switching to key #{ki + 2})", file=sys.stderr)
            ki += 1
        if not embs:
            break  # stop and keep what we have
        for v in embs:
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        if total > 1:
            print(f"(embedded batch {bi + 1}/{total} [key #{ki + 1}])", file=sys.stderr)
            if bi + 1 < total:
                time.sleep(throttle)
    return out


def pack_vec(vec):
    return struct.pack("<%df" % len(vec), *vec)


def unpack_vec(blob):
    return list(struct.unpack("<%df" % (len(blob) // 4), blob))


# ---------------- index build (incremental embeddings) ----------------

def build_index(roots, db_path, do_embed=True):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    key = _read_key() if do_embed else ""

    # reuse existing embeddings for unchanged chunk text
    old_vecs = {}
    if os.path.exists(db_path):
        try:
            oc = sqlite3.connect(db_path)
            for h, vec in oc.execute("SELECT thash, vec FROM chunk WHERE vec IS NOT NULL"):
                old_vecs[h] = vec
            oc.close()
        except Exception:
            old_vecs = {}

    rows = []          # (path, kind, origin, title, tags, head, text, thash)
    for (p, kind, origin, title, tags, head, text) in iter_chunks(roots):
        thash = hashlib.sha1((title + "\x1f" + head + "\x1f" + text).encode("utf-8")).hexdigest()
        rows.append((p, kind, origin, title, tags, head, text, thash))

    # ALWAYS carry forward existing vectors for unchanged chunks (so a lexical-only refresh
    # never loses embeddings). Only NEW versioned chunks get sent to the embedding API.
    vec_by_hash = {}
    for r in rows:
        if r[7] in old_vecs:
            vec_by_hash[r[7]] = old_vecs[r[7]]
    if do_embed and key:
        need, need_texts, seen = [], [], set()
        for r in rows:
            thash = r[7]
            if r[2] != "versioned" or thash in vec_by_hash or thash in seen:
                continue   # bundled library stays lexical; already-embedded reused above
            seen.add(thash)
            need.append(thash)
            need_texts.append((r[3] + " / " + r[5] + "\n" + r[6]).strip())  # title+section context
        if need:
            embs = embed_texts(need_texts, key, "document")
            for thash, e in zip(need, embs):
                vec_by_hash[thash] = pack_vec(e)
            if len(embs) < len(need):
                print(f"(embedded {len(embs)}/{len(need)} new chunks — rerun --build to finish the rest)",
                      file=sys.stderr)

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS chunk;
        CREATE TABLE chunk(
            id INTEGER PRIMARY KEY, path TEXT, kind TEXT, origin TEXT,
            title TEXT, tags TEXT, head TEXT, text TEXT, thash TEXT, vec BLOB);
        DROP TABLE IF EXISTS cfts;
        CREATE VIRTUAL TABLE cfts USING fts5(
            title, tags, head, text, cid UNINDEXED,
            tokenize='unicode61 remove_diacritics 2');
        DROP TABLE IF EXISTS meta;
        CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
    """)
    cid = 0
    embedded = 0
    for (p, kind, origin, title, tags, head, text, thash) in rows:
        cid += 1
        vec = vec_by_hash.get(thash)
        if vec:
            embedded += 1
        cur.execute("INSERT INTO chunk(id,path,kind,origin,title,tags,head,text,thash,vec) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (cid, p, kind, origin, title, tags, head, text, thash, vec))
        cur.execute("INSERT INTO cfts(rowid,title,tags,head,text,cid) VALUES (?,?,?,?,?,?)",
                    (cid, title, tags, head, text, cid))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('built_at',?)", (str(time.time()),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('chunks',?)", (str(cid),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('embedded',?)", (str(embedded),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('model',?)", (EMBED_MODEL_NAME if embedded else "",))
    cur.execute("INSERT OR REPLACE INTO meta VALUES('roots',?)", (";".join(roots),))
    con.commit(); con.close()
    return cid, embedded


# ---------------- search (hybrid) ----------------

def _fts_query(terms):
    parts = [f'"{t}"' for t in (t.replace('"', '') for t in terms) if t]
    return " OR ".join(parts)


def _cosine_topn(qvec, ids, vecs, n):
    if _np is not None:
        q = _np.asarray(qvec, dtype=_np.float32)
        M = _np.frombuffer(b"".join(vecs), dtype=_np.float32).reshape(len(vecs), -1)
        sims = M @ q
        order = _np.argsort(-sims)[:n]
        return [(ids[i], float(sims[i])) for i in order]
    scored = []
    for cid, blob in zip(ids, vecs):
        v = unpack_vec(blob)
        scored.append((cid, sum(a * b for a, b in zip(qvec, v))))
    scored.sort(key=lambda x: -x[1])
    return scored[:n]


KIND_W = {"skill": 3.0, "reference": 2.5, "skill-file": 2.0, "doc": 1.0, "index": 0.3, "log": -1.5}


def search(db_path, query, top=8, cand=40):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    terms = query_terms(query)

    # lexical candidates
    lex = []
    try:
        rows = cur.execute(
            "SELECT cid, bm25(cfts, 8.0, 6.0, 4.0, 1.0) AS r FROM cfts WHERE cfts MATCH ? "
            "ORDER BY r LIMIT ?", (_fts_query(terms), cand)).fetchall()
        lex = [cid for (cid, r) in rows]
    except sqlite3.OperationalError as e:
        print(f"(fts error: {e})", file=sys.stderr)

    # semantic candidates
    sem = []
    key = _read_key()
    has_vecs = cur.execute("SELECT COUNT(*) FROM chunk WHERE vec IS NOT NULL").fetchone()[0]
    if key and has_vecs:
        qe = embed_texts([query], key, "query")
        if qe:
            allv = cur.execute("SELECT id, vec FROM chunk WHERE vec IS NOT NULL").fetchall()
            ids = [r[0] for r in allv]
            vecs = [r[1] for r in allv]
            sem = [cid for (cid, s) in _cosine_topn(qe[0], ids, vecs, cand)]

    # Reciprocal Rank Fusion
    K = 60.0
    fused = {}
    for rank, cid in enumerate(lex):
        fused[cid] = fused.get(cid, 0.0) + 1.0 / (K + rank)
    for rank, cid in enumerate(sem):
        fused[cid] = fused.get(cid, 0.0) + 1.0 / (K + rank)
    if not fused:
        con.close()
        return [], bool(sem)

    # re-rank with kind weight + exact title/path bonus
    out = []
    for cid, base in fused.items():
        row = cur.execute("SELECT path,kind,origin,title,head,text FROM chunk WHERE id=?", (cid,)).fetchone()
        if not row:
            continue
        path, kind, origin, title, head, text = row
        bonus = sum(1 for t in terms if t.lower() in (title or "").lower() or t.lower() in path.lower())
        score = base * 100 + KIND_W.get(kind, 0.0) + bonus * 1.5
        out.append((score, path, kind, origin, title, head, text))
    out.sort(key=lambda x: -x[0])
    con.close()
    # diversity: at most 2 passages from the same document in the final list
    per_path, diverse = {}, []
    for item in out:
        p = item[1]
        if per_path.get(p, 0) >= 2:
            continue
        per_path[p] = per_path.get(p, 0) + 1
        diverse.append(item)
        if len(diverse) >= top:
            break
    return diverse, bool(sem)


def _snippet(text, terms, width=240):
    low = text.lower()
    pos = -1
    for t in terms:
        pos = low.find(t.lower())
        if pos >= 0:
            break
    if pos < 0:
        return re.sub(r"\s+", " ", text[:width]).strip()
    start = max(0, pos - width // 3)
    return ("… " if start else "") + re.sub(r"\s+", " ", text[start:start + width]).strip() + " …"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--no-embed", action="store_true", help="build lexical only, skip the embedding API")
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
        # Only an explicit --build calls the embedding API; a stale auto-refresh stays lexical
        # (existing vectors are preserved) so searches never burn embedding quota or block on it.
        do_embed = args.build and not args.no_embed
        n, emb = build_index(roots, args.db, do_embed=do_embed)
        print(f"[indexed {n} chunks; embedded {emb}; model={EMBED_MODEL_NAME if emb else 'lexical-only'}]",
              file=sys.stderr)
        if args.build and not args.query:
            return

    if not args.query:
        ap.error("provide a query (or --build)")
    res, used_sem = search(args.db, args.query, args.top)
    terms = query_terms(args.query)
    if not res:
        print("No matches. Try other keywords or `--build` to refresh the index.")
        return
    print(f"[hybrid: lexical+{'semantic' if used_sem else 'lexical-only'}]", file=sys.stderr)
    for i, (score, path, kind, origin, title, head, text) in enumerate(res, 1):
        loc = f"{title}" + (f" › {head}" if head else "")
        print(f"{i}. [{kind}/{origin}] {loc}")
        print(f"   {path}")
        print(f"   … {_snippet(text, terms)}")


if __name__ == "__main__":
    main()
