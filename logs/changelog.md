---
id: changelog
type: log
tags: [changelog]
updated: 2026-05-29
secret_refs: []
---

# Changelog

Append-only, newest on top. Every approved change to the brain gets one line.

## 2026-05-30
- Task 1 (split): extracted two big subsystems out of `projects/albery/server-context.md` into
  focused docs — `vpn-gateway.md` (AmneziaWG outbound-via-Estonia) and `hermes.md` (Hermes agent:
  Codex provider, cron, Telegram, sessions, training, RBAC roadmap). `server-context.md` now holds
  the app/server reference + Bitrix MCP tools + fetch_url/bug notes. Updated its frontmatter/intro,
  `overview.md` "Full reference", added cross-links. IP `186.246.7.32` left in legacy commands with a
  banner (current prod `217.198.12.236`) — to reconcile live during brain sync (Task 2).

## 2026-05-29
- Fixed mojibake in `projects/albery/server-context.md`: 771 legacy lines were double-encoded
  (UTF-8 bytes read as CP1251 then re-encoded). Repaired in place via per-line round-trip
  (`cp1251.GetBytes` → `utf8.GetString`), kept already-clean lines, normalized CRLF→LF. 0 residual
  U+FFFD. Earlier "UTF-8 verified clean" claim was wrong (see mistakes.md).
- `scripts/validate.py`: also skip `CLAUDE.md` (landing/instruction file, no frontmatter needed).
- Created isolated `hermes-brain` repo. Built areas: profile, engineering (migrated + new
  coding-standards/code-review), projects (template, manifest schema, registry generator,
  validator), connectors (gmail/calendar/drive/bitrix/zoom), personal, skills, logs.
- Migrated albery as first reference project.
- Imported legacy `agent.md` (site repo) → `projects/albery/server-context.md` as the full
  operational reference (UTF-8 verified clean, scanned for secrets — none). Curated docs link to it.
- Hardened `scripts/validate.py`: skip README, expand secret-placeholder allowlist (getpass/env/...).
