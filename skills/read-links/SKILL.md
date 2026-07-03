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
- **Legacy dynamic forms** (university admissions rankings, old government forms): if browser snapshots
  show empty controls, inspect raw HTML and form query parameters. Some official Russian sites declare
  UTF-8 but serve option text in `cp1251`; retry that decoding before giving up. See
  `references/dynamic-admissions-pages.md`.
- `web_extract` (Firecrawl) is also available but **summarizes** large pages (costs tokens, truncates)
  — use it only when you explicitly want a summary, not the full text.

## Google access — the agent reads the owner's Drive (OAuth, read-only)
The agent's Google profile is the **owner's own account via OAuth** (read-only token at
`/root/.hermes/secure/google_oauth_token.json`, 600, not in git). So `fetch_url.py` (`gauth_read.py`)
reads **any** of the owner's Google Docs/Sheets/Slides — public or private — with **no per-doc
sharing**. Docs/Slides → text, Sheets → all tabs as CSV (`--gid` for one tab).
- If there's **no token** yet → it falls back to the public export (only «доступ по ссылке» works).
- One-time setup (Cloud OAuth client + browser login on the PC + token to server):
  `connectors/google-workspace.md`. Login script: `scripts/google_oauth_login.py` (run on the PC).
- A **service account** is supported as an alternative (then docs are shared with the agent's e-mail).

## Rules
- Owner-facing replies in Russian, no technical noise (paths, commands, stack traces) — the manager
  already prints clean Russian; relay it. (`profile/communication.md`.)
- Treat a pasted URL as content to read, not as something to "click around" unless asked.
- Respect `security.website_blocklist` in `config.yaml` if set.

## Pointers
- Connectors & MCP servers (a different mechanism): `connectors/mcp-servers.md`, skill `connect-mcp`.
- Google Drive/Docs via the OAuth MCP layer (future, for private docs): `connectors/google-drive.md`.
