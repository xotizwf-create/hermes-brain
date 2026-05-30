---
name: read-links
description: Use when the owner pastes a link or asks to read/open the content behind a URL — a web page, an article, a Google Doc, a Google Sheet, or Google Slides ("прочитай эту ссылку", "что в этом документе", "открой таблицу", "выжимку со страницы"). Hermes reads the content with the bundled fetch_url.py (direct, full, no LLM cost — handles Google share-link → export), and falls back to the native browser/web_search tools for JS-heavy or search cases.
---

# Skill: read-links

Read what's behind a link the owner sends. Pick the cheapest tool that returns the full content.

Manager: `skills/read-links/scripts/fetch_url.py` → prod
`/root/.hermes/agent-knowledge/skills/read-links/scripts/fetch_url.py`. Stdlib only, runs via the
terminal tool. All its messages are Russian and tech-noise-free.

## Default — `fetch_url.py` (full content, no token cost)
```bash
python3 .../fetch_url.py "<url>"
```
- **Google Docs / Sheets / Slides / Drive:** it converts the share link to the export URL
  (Docs→plain text, Sheets→CSV, Slides→text) and returns the **full** content. No browser, no LLM
  summarization. For a specific spreadsheet tab pass `--gid <N>` (or include `#gid=N` in the URL).
- **Normal web pages / articles / PDFs-as-HTML:** it fetches and reduces the page to readable text.
- Long content is capped (~20k chars) with a note; ask for `--max <N>` or a continuation if needed.

Prefer this for anything the owner pastes — it's deterministic and free. Read its output and answer
in the owner's language; don't dump raw HTML.

## When to use the native tools instead
- **JS-heavy / interactive / login-walled pages** (SPAs, dashboards) where `fetch_url.py` returns
  little or "лучше открыть через браузер": use `browser_navigate` then `browser_snapshot`
  (and `browser_click`/`browser_type`/`browser_scroll` to interact). The browser toolset is enabled.
- **"Найди в интернете…" / no URL yet:** use `web_search`, then read the best result with `fetch_url.py`.
- `web_extract` (Firecrawl) is also available but **summarizes** large pages (costs tokens, truncates)
  — use it only when you explicitly want a summary, not the full text.

## Google access — the agent's Google profile (service account)
The agent has its own Google identity: a **service account** whose key lives at
`/root/.hermes/secure/google_service_account.json` (600, not in git). `fetch_url.py` uses it
(`gauth_read.py`) for Google links, so it reads **both** public-by-link **and private** docs — as
long as the doc/folder is shared with the agent's service-account e-mail (read-only).
- If the key is present and the doc is shared → full content (Docs/Slides → text, Sheets → all tabs
  as CSV; `--gid` for one tab).
- If the doc is **not** shared with the agent → `fetch_url.py` prints the agent's e-mail and asks the
  owner to share it («Поделись им (доступ «Читатель») с агентом — его адрес: …»). Relay that.
- If there's **no key** yet → it falls back to the public export (works only for «доступ по ссылке»).
- Setup details (one-time, in Google Cloud) + how to deliver the key: `connectors/google-workspace.md`.

## Rules
- Owner-facing replies in Russian, no technical noise (paths, commands, stack traces) — the manager
  already prints clean Russian; relay it. (`profile/communication.md`.)
- Treat a pasted URL as content to read, not as something to "click around" unless asked.
- Respect `security.website_blocklist` in `config.yaml` if set.

## Pointers
- Connectors & MCP servers (a different mechanism): `connectors/mcp-servers.md`, skill `connect-mcp`.
- Google Drive/Docs via the OAuth MCP layer (future, for private docs): `connectors/google-drive.md`.
