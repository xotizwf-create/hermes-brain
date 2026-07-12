# CLAUDE.md — working instructions for this repo

This repository **is the agent's brain**: the single, versioned source of truth for what the
agent knows and how it acts across all of the user's projects. It is isolated from any individual
project repo. Read this file first, then `INDEX.md`.

## What this is / why it exists
- Built 2026-05-29 by extracting the agent's knowledge out of the website repo ("Сайт мой")
  into its own private repo so it can scale across many projects for years.
- GitHub: https://github.com/xotizwf-create/hermes-brain (PRIVATE, branch `main`).
- Local working copy: `g:\OneDrive\Рабочий стол\Мои проекты\Hermes Brain` (the old `C:\hermes-brain`
  clone went stale at 2026-05-31 and was removed 2026-07-02). Mirrored to server `/root/.hermes/agent-knowledge`.

## Architecture (the design we committed to)
- **Canonical store = files in git.** No database for content. Versioned, diffable, reviewable.
- **Retrieval is layered & upgradeable:** today `INDEX.md` routing + frontmatter tags + grep;
  later a generated registry / RAG over the *same* files. So every doc carries strict frontmatter
  (`schema/frontmatter.schema.yaml`) from day one — those fields are the future search hooks.
- **Secrets never live here** — only references `proj/<slug>/<service>/<credential>`. Real values
  stay server-side in `/root/.hermes/secure/` (`access-map.yaml` + `secrets.yaml`, root-only 600/700).

## Areas
`profile/` (preferences, communication, do-not-do) · `engineering/` (standards, security, testing,
database, deployment, optimization, secrets-access, code-review) · `projects/` (one folder per
project + generated `registry.yaml`) · `connectors/` (gmail, calendar, drive, bitrix, zoom) ·
`personal/` · `skills/` · `logs/` (changelog, decisions, learning-log, mistakes) · `inbox/` · `archive/`.

## Hard rules
1. **Approval-gated mutations.** To change the brain: propose the edit → show a diff → wait for the
   user's confirmation → commit → append one line to `logs/changelog.md`. If the owner explicitly says
   to update without showing the diff, that counts as approval. No silent unapproved edits.
   **Standing approval (owner, 2026-06-11): working-tree leftovers in the server brain clone are
   auto-committed by the `brain-dirty-watchdog` cron** (source: `scripts/brain_dirty_watchdog.py`) —
   only after the dirty state is stable ≥25 min AND `scripts/validate.py` passes (frontmatter +
   secret scan); otherwise it alerts instead of committing. Уведомление «база знаний не в чистом
   состоянии» больше не требует ручных действий — вотчдог разберётся сам или позовёт.
2. **No secrets in any committed file.** References only. `scripts/validate.py` enforces this.
3. **Every doc needs valid frontmatter.** Skills use the `name`/`description` format instead.
4. **`projects/registry.yaml` is generated** — run `python scripts/build_registry.py`, never hand-edit.
5. **Validate before committing:** `python scripts/validate.py` must pass.
6. Keep LF line endings (`.gitattributes`); the brain syncs to a Linux server.
7. **Never overload a production host — treat every prod box as fragile and memory-constrained.**
   Before any memory-heavy step (build/bundle, typecheck, full test suite, a long-running or trial
   app instance, a bulk migration) run a preflight: `free -m` + `swapon --show`. If RAM is small
   (≈1 GB) or there is no swap, **do not run it on the box.** Build `dist/` and run tests/typecheck
   **off the box** (locally or CI), upload only the prebuilt, already-tested release, and on the
   server do only `npm ci` + light smoke checks + one atomic release switch with rollback ready.
   **Never point a trial/dev instance, a test run, or a migration at the LIVE production database.**
   An OOM-kill on prod is never acceptable: a killed Node process cascades into DB connection drops
   and user-facing failures (this is what broke LiteExams device-binding on 2026-05-30/31). The
   universal, scale-adaptive procedure (assess → plan budget → protect → execute, same for a 512 MB
   VPS or a big box) is the mandatory first step for any server work: `engineering/server-preflight.md`.

## Key skills
- `add-project` — register a new project safely (no secrets, refs only).
- `project-onboarding` — make a project workable by the agent: repo + prod access + git access + env
  (via the server secure store), then write code per the brain's standards.
- `reminders-and-watchers` — one-shot/recurring reminders & watchers (mail, etc.) via `hermes cron` → Telegram.
- `connect-mcp` — connect/switch/remove MCP servers for Hermes safely (owner pastes a URL → Hermes
  edits its own `config.yaml`, restarts gateway, records a secret-free entry in `connectors/registry.yaml`).
- `read-links` — read the content behind a link: web pages + Google Docs/Sheets/Slides (share-link →
  export), via `fetch_url.py`; native `browser`/`web_search` for JS/search.
- `markitdown-docs` — convert local PDF/Word/Excel/PowerPoint files to compact Markdown with
  Microsoft MarkItDown before analysis, so binary documents do not burn model context.
- `aislop-code-quality` — run scanaislop/aislop after AI code edits or during review to catch
  narrative comments, dead code, unsafe casts, swallowed exceptions, duplicate helpers, and other
  agentic code slop; use only safe mechanical fixes unless explicitly approved.
- `google-account` — the agent's Google profile (owner's account, OAuth read-only): Calendar/Drive/
  Docs/Sheets/Gmail; how it was connected, keep-alive (publish to Production), rotation, adding write.
- `update-knowledge` — the workflow for changing the brain + two-way git sync (Hermes self-scaling);
  includes the standing preference to document new non-trivial procedures in the nearest instruction,
  or create one if none exists.
- `new-repo` — create a git repo + private GitHub repo (gh CLI is installed & authed as `xotizwf-create`).
- `store-project-secrets` — owner pastes a project's `.env` / prod-server password → Hermes finds the
  repo (gh), stores values in the secure zone (`/opt/hermes/secure/projects/<slug>/`, 600, never
  echoed/committed), and remembers the project (repo + prod host) secret-free in `projects/<slug>/`.
- `secure-access/vault/` — **Hermes Vault**: dependency-free web UI (scrypt password + URL-token + TLS)
  to manage per-project secrets in a browser, tied to GitHub repos; runs as unprivileged `hermesvault`,
  shared store `/opt/hermes/secure/projects`. Live at `www.andigital.ru/andigital/secret/<token>/`. Turnkey/resaleable (README).
- `secure-access`, `postgres-production` — credentials & Postgres ops.
- `leadgen-watch` — поиск ПРОЕКТОВ (не вакансий) для лидгена владельца: FL.ru + freelance.ru +
  TG-каналы → LLM-фильтр → кандидаты с черновиком отклика в TG (review-only); там же план
  холодного email-аутрича (Фаза 3).

## Current state (2026-07-02)
- Brain lives in two checkouts of the GitHub repo: this local working copy + prod clone
  `217.198.12.236:/root/.hermes/agent-knowledge` (two-way git sync, see `skills/update-knowledge/`).
- **Projects registered (5):** `albery`, `andigital`, `gov-exams-app`, `prostye-postavki`, `hermes-brain`
  (see `projects/registry.yaml`).
- **Hermes on 217 = v0.17.0** (config v30). After-update lessons live in `logs/changelog.md` (June):
  Telegram adapter moved to `plugins/platforms/telegram/adapter.py` (old anchor patches under
  `/root/.hermes/patches` no longer apply); `compression.codex_gpt55_autoraise` disabled 2026-06-22
  (it burned Plus limits 3.6× and dumbed answers). Always diff migrated config vs backup after `hermes update`.
- **Second agent on 217:** Claude Code Telegram bot `@GoogleDeck_Bot` (coder/maintenance) —
  `engineering/claude-code-tg-agent.md`.
- **Dedicated Albery Hermes lives on 186.246.7.32** (NOT 217) — `projects/albery/servers.md`.
- Server connection (no SSH key on PC): `python _deploy_helper.py new "<cmd>"` from the "Сайт мой"
  repo (Paramiko, password from `.env.local`, never printed). Targets: new=217.198.12.236, estonia=95.85.243.43, prod(old)=186.246.7.32.
- **Repo hygiene (2026-07-02):** the root was cleaned of ~30 ad-hoc leftovers. One-off scripts and
  task outputs go ONLY to `tmp/` (gitignored), never the repo root — `.gitignore` now also blocks
  `_*_tmp.*` / `.tmp_*` / root `*.xlsx` patterns.

## Done (2026-05-30) — full session retrospective in `logs/session-2026-05-30.md`
1. ✅ Split `server-context.md` → `vpn-gateway.md` + `hermes.md` (+ encoding repair).
2. ✅ Synced brain to the server.
3. ✅ Switched pointer / archived legacy `agent.md` + `agent-knowledge/` in the site repo.
4. ✅ Phase B skills written: `project-onboarding`, `reminders-and-watchers`, `update-knowledge` (v2).
5. ✅ **Two-way git self-scaling live** — server brain is a git clone with a read-write deploy key;
   Hermes edits → validate → approve in Telegram → commit/push; local pulls. Telegram toolsets enabled.
6. ✅ **Automations live:** reminders → Telegram; `mail-watch` (himalaya, every 2h); `chatgpt-sub-watch`
   (daily 10:00 МСК, warns + auto-removes expired ChatGPT accounts). Clean deliveries (`cron.wrap_response=false`).
7. ✅ Prefs in `profile/`: max-brevity-by-default; no technical text in auto-deliveries; default TZ = MSK.
8. ✅ Security: removed leaked `.env` copies from server backups; secrets only in local `.env` + `/root/.hermes/secure/`.

## Live cron automations (server)
- `mail-watch` — every 2h, important non-newsletter Gmail → Telegram.
- `chatgpt-sub-watch` — daily, ChatGPT subscription expiry warnings + auto-disable; dates in
  `/root/.hermes/chatgpt_accounts.json`.
- `self-review` — weekly (Mon 10:00 МСК), digest of the agent's own errors from the gateway
  journal → owner in Telegram + proposed `logs/mistakes.md`/skill edits via the approval flow.
- `self-check` — **hourly** (job `e473bdb3d674`, `scripts/hermes_selfcheck.py`, no-agent): scans the
  gateway journal for silent degradations (SOUL-blocked / codex `token_invalidated` / aux-provider
  unhealthy / compression-fail / media-drop) → Telegram **only if** something crossed a threshold
  (quiet otherwise). Catches "the model got dumb" before the owner has to notice.
- `hh-auto-apply` — **hourly** (job `cfbbc44317be`): поиск вакансий hh.ru — внедрение ИИ/агентов,
  вся Россия, ЗП от 100к; письма (Groq `openai/gpt-oss-120b`); мониторинг ЛС (новые сообщения → TG,
  отказы — молча). **Сейчас `mode: review`** — кандидаты идут владельцу в TG на одобрение
  («норм» → `--apply-ids`, «не норм» → `hh_feedback.json` в промпт); автоотклики включатся после
  «фильтр норм» (`mode: apply`). Ночью (вне 8–23 МСК) автоотклики не шлются, review/ЛС работают.
  Skill: `hh-auto-apply`. Старый `hh-ai-business-automation-watch` (every 2h) живёт отдельно.
- `leadgen-watch` — **hourly** (с 2026-07-12, no-agent): мониторинг проектов на FL.ru +
  freelance.ru + 6 публичных TG-каналов → Groq-фильтр + черновик отклика → кандидаты
  владельцу в TG (review-only, ночью 23–8 МСК копит pending). Skill: `leadgen-watch`.

## Open tasks (next steps, not yet done)
- **Re-auth Codex CLI on 217 (BLOCKER for coding delegation):** discovered 2026-07-09 — `codex login
  status` says "Logged in" but real calls die with «access token could not be refreshed» (token
  invalidated by a login elsewhere). Needs owner: `codex login` on 217 or fresh `auth.json` from the
  PC (600). Until then coding delegation on 217 is down. On 186 codex CLI (0.134.0) is **not logged
  in at all**. After re-auth: run one real `xhigh` job and confirm the effort in the `codex exec`
  header (backend must not silently downgrade). Mode policy: `engineering/agentic-coding.md`.
- **Albery refactor (owner-approved plan, 2026-07-02):** split the monoliths — `app.py` (23.5k lines),
  `mcp/context_server.py` (5.9k), `Интерфейс/src/App.tsx` (9.2k). Full staged plan:
  `projects/albery/refactor-plan.md`. Do NOT add new code to `app.py`.
- Reconcile legacy `186.246.7.32` references in `vpn-gateway.md`/`hermes.md` against the live host
  (host truth corrected 2026-06-11 in `projects/albery/servers.md`; sweep the older docs).
- Skills revision pass: 25 custom skills — check for dead paths/hosts after the June changes.
- Re-wire Albery MCP on 217 if ever needed: `MCP_SHARED_SECRET` is not on 217; get it from the
  owner / the Albery box (186), then `connect-mcp` add albery. See `connectors/mcp-servers.md`.
- **Leadgen Фаза 2/3 (ждёт владельца, план в `skills/leadgen-watch/SKILL.md`):** аккаунты на
  биржах (Kwork-продавец, профиль подрядчика Workspace → email-дайджесты тендеров), для
  email-аутрича — отдельный домен + выбор 2–3 ниш; дальше агент строит аутрич-машину
  (SPF/DKIM/прогрев, парсинг компаний, персональные письма в review). Фаза 4: кейс Albery
  на vc.ru + TenChat + партнёрка Битрикс24.

Keep this section current as tasks complete.
