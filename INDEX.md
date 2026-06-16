---
id: index
type: schema
tags: [root, routing, entrypoint]
updated: 2026-06-16
secret_refs: []
---

# Hermes Brain — Index

This repository is the agent's brain. It is the **single source of truth** for what the
agent knows and how it acts across all projects. It is isolated from any single project repo.

**Read this file first in every new session.** Then load only the files relevant to the
current task — never load the whole brain unless asked for a full audit.

**Finding things — search BEFORE you decide you don't know or pick a skill.** Run:
`python3 /root/.hermes/agent-knowledge/scripts/brain_search.py "<keywords>"`. This is the one
unified search across **both** trees the agent has — the versioned brain (docs + our custom
skills in `agent-knowledge/`) AND Hermes' bundled skill library (`/root/.hermes/skills/`, e.g.
`research`, `devops`). It returns ranked `path · title · snippet` (lexical FTS + fuzzy fallback);
open the top hit and load that. The index self-rebuilds when stale; force with `--build`.
*Why this exists:* knowledge and skills live in separate trees, and the agent used to miss the
right skill entirely (e.g. the 2026-06-14 Росреестр task) — always search first.

**For an in-file anchor**, also grep [`section-index.md`](section-index.md) — a generated map of
every brain doc → its H2/H3 sections (`path#anchor`). Regenerate after edits:
`python scripts/build_section_index.py`.

## Core principles

1. **Canonical store = files in git.** Versioned, diffable, reviewable. No database for content.
2. **Secrets never live here.** Only *references* (names) live in `secrets-templates/` and project
   manifests. Real values live on the server under `/root/.hermes/secure/` (root-only, mode 700/600).
3. **Knowledge = what to know. Skills = how to act.** Logs = what changed & what was learned.
4. **Mutations are approval-gated.** The agent proposes a diff; the user confirms; then it commits
   and writes to `logs/changelog.md`.
5. **Every doc carries frontmatter** (`id`, `type`, `tags`, `updated`, `secret_refs`) per
   `schema/frontmatter.schema.yaml`. This is the hook for future search/RAG without rewriting content.
6. **Assess any server before you act on it — never crash it.** Before ANY server work (deploy,
   build, migration, bulk job, long-running process), run the universal preflight in fixed order:
   **assess resources → plan a memory budget from current headroom → protect the live services →
   only then execute within that budget.** Scales identically from a 512 MB VPS to a big dedicated
   box: reason from headroom, never from habit. Heavy steps that don't fit run **off the box**; ones
   that do are capped (`systemd-run -p MemoryMax=…` + `nice`/`ionice`) so a runaway dies, not the app.
   **Never run a build/test/migration against the live prod DB.** Procedure (mandatory first step):
   `engineering/server-preflight.md`. (Skipping this caused the 2026-05-31 LiteExams OOM → DB drops →
   "another device" lockouts.)

## Areas

| Area | Path | Purpose |
|---|---|---|
| Profile | `profile/` | Who the user is, preferences, communication, hard rules |
| Engineering | `engineering/` | Universal how-to-build: standards, security, testing, db, deploy, optimization |
| Projects | `projects/` | One isolated folder per project + machine-readable `registry.yaml` |
| Connectors | `connectors/` | MCP connectors (Gmail, Calendar, Drive, Bitrix…) + `registry.yaml` + usage rules |
| Personal | `personal/` | Education, side-jobs, life knowledge that helps the agent act |
| Skills | `skills/` | Repeatable procedures the agent executes |
| Logs | `logs/` | changelog, decisions (ADR), learning-log, mistakes |
| Inbox | `inbox/` | Unsorted buffer awaiting classification |
| Archive | `archive/` | Retired material (archived, not deleted) |

## Routing

- **Project work / "connect to X" / deploy X** → read `projects/registry.yaml`, find the project,
  load only `projects/<slug>/`. For credentials use the `secure-access` skill.
- **Add a new project** → use skill `skills/add-project/`.
- **Audit / document / "разбери" an existing project — full dossier по полочкам (plain-language human
  summary + structure, architecture, database, API & integrations, runbook) with Mermaid diagrams** →
  skill `skills/project-audit/` (inspects repo + prod read-only, flags unknowns, then registers via add-project).
- **Securely take a project's secrets** (owner pastes a `.env` / prod-server password → store in the
  secure zone, never echoed; remember repo + prod host) → skill `skills/store-project-secrets/`.
- **Secret-manager web UI** (browser, tied to GitHub repos; install/operate/resell) → `skills/secure-access/vault/` (README).
- **Onboard a project to work in** (repo + prod access + git access + env, then write code) → skill `skills/project-onboarding/`.
- **Reminders / recurring tasks / watch mail** → skill `skills/reminders-and-watchers/`.
- **Connect / switch / remove an MCP server (owner pastes a URL)** → skill `skills/connect-mcp/`;
  model in `connectors/mcp-servers.md`; what's connected in `connectors/registry.yaml`.
- **VK: общение с Hermes через VK-сообщество (Callback-мост), починка/расширение моста** →
  skill `skills/vk-hermes-bridge-mvp/`; live: `vk-hermes-bridge.service` на 217 (`/opt/vk-hermes-bridge`).
- **Отправить письмо / email / переслать файл-подборку на почту (кому угодно, с почты владельца)** →
  skill `skills/send-email/` (Gmail API по HTTPS; himalaya/SMTP для отправки НЕ работают — порты
  заблокированы хостером 217).
- **Read a link / web page / Google Doc / Sheet / Slides (owner pastes a URL)** → skill `skills/read-links/`.
- **Вакансии hh.ru: поиск + автоотклики (внедрение ИИ/автоматизаций в бизнес)** → skill
  `skills/hh-auto-apply/` (залогиненный браузер `/opt/hh-browser`, LLM-фильтр + человечные
  письма, журнал без повторов, отчёт в Telegram; cron `hh-auto-apply`). Полуавтоматический
  разовый поиск/черновики — старый `skills/.../hh-ru-semiauto-job-search` (нативный хаб).
- **Изометрия / аксонометрия / «начерти деталь по ГОСТ» (владелец присылает чертёж)** →
  skill `skills/iso-drawing/` (библиотека `iso_gost.py`: ГОСТ 2.317 на А4 с рамкой,
  основной надписью и размерами; эталон — `detail22_demo.py`; результат PDF в outbox).
- **Read local PDF / Word / Excel / PowerPoint files** → skill `skills/markitdown-docs/`;
  convert with Microsoft MarkItDown first, then inspect the generated Markdown.
- **Google account access (Calendar / Drive / Docs / Sheets / Gmail), re-auth, scopes** → skill
  `skills/google-account/`; connector ref `connectors/google-workspace.md`.
- **Create/fix Google Sheets dashboards, calculators, charts, formulas, dropdowns, or bound Apps Script** →
  skill `skills/google-sheets-dashboard-automation/` (readable formulas, visual dashboard structure,
  and mechanical chart/data verification).
- **Add/manage a GitHub repo** → use skill `skills/new-repo/`.
- **Credentials, SSH, tokens, DB URLs** → `engineering/secrets-access.md` + skill `secure-access`.
- **Database / migrations / Postgres** → `engineering/database.md` + skill `postgres-production`.
- **Any work on a server — FIRST assess resources so you don't crash it** → `engineering/server-preflight.md`
  (mandatory before deploy/build/migration/bulk job; scale-adaptive: assess → plan budget → protect → execute).
- **Deploy / systemd / nginx** → `engineering/deployment.md` (build/test off-box, never OOM prod,
  never touch the live DB with a trial/test process; runs the preflight above first).
- **Security / auth / webhooks** → `engineering/security.md`.
- **Tests / CI** → `engineering/testing.md`.
- **Performance** → `engineering/optimization.md`.
- **Code style / review** → `engineering/coding-standards.md`, `engineering/code-review.md`.
- **Writing/changing code, refactors, debugging, feature work — make Hermes code like Codex** →
  `engineering/agentic-coding.md`; delegate the actual coding to the Codex CLI via skill
  `skills/codex-delegation/`.
- **Tiny live prod change (one support-text string, a config flag, one line)** → skill
  `skills/small-prod-edit/` (backup → exact replace → verify → restart only that service; no
  subsystem fishing).
- **Hermes gateway itself is broken/suspect (bloated or duplicated `run.py`, duplicated config
  blocks, restart hangs/kills the bot, looping self-patcher, missing code-task classifier)** → skill
  `skills/hermes-self-repair/` (diagnose first, restart last, rollback ready).
- **AI-generated code cleanup / slop detection before PR or after agent edits** → skill
  `skills/aislop-code-quality/`.
- **Coding behavior rules to avoid LLM pitfalls (don't assume, simplicity first, surgical edits,
  verifiable goals) — apply when writing/reviewing/refactoring code** → skill `skills/karpathy-guidelines/`
  (Karpathy-derived, MIT; pairs with `engineering/agentic-coding.md` + `aislop-code-quality`).
- **How the agent should answer/communicate** → `profile/`.
- **Hermes UX: "Думаю…"/typing, live step progress, reasoning, tone — config knobs** → `engineering/hermes-gateway-ux.md`.
- **Build a team of agents / split into multiple agents / multi-agent design / when to add an agent**
  → `engineering/agent-team.md` (grounded in 12-factor-agents + Anthropic "Building Effective Agents":
  one workflow = one agent, orchestrator+workers, own your context; checklist before adding an agent).
- **Change the brain itself / how Hermes scales itself** → skill `skills/update-knowledge/`.
- **How Hermes was built & how it's taught (orientation)** → `logs/session-2026-05-30.md`.

## Secret model (summary)

- `secrets-templates/access-map.template.yaml` → non-secret routing: project → service → credential
  *name* + allowed actions. Deployed to `/root/.hermes/secure/access-map.yaml` (mode 600).
- `secrets-templates/secrets.template.yaml` → real values or `value_path`. Deployed to
  `/root/.hermes/secure/secrets.yaml` (mode 600). **Never committed.**
- Secret references use the namespace `proj/<slug>/<service>/<credential>`.

## Hermes sync

This repo is mirrored to the server at `/root/.hermes/agent-knowledge`. After changing the brain,
sync before expecting Hermes to use the new content. See `skills/update-knowledge/`.
