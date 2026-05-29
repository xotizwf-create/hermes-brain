---
id: changelog
type: log
tags: [changelog]
updated: 2026-05-29
secret_refs: []
---

# Changelog

Append-only, newest on top. Every approved change to the brain gets one line.

## 2026-05-29
- Created isolated `hermes-brain` repo. Built areas: profile, engineering (migrated + new
  coding-standards/code-review), projects (template, manifest schema, registry generator,
  validator), connectors (gmail/calendar/drive/bitrix/zoom), personal, skills, logs.
- Migrated albery as first reference project.
- Imported legacy `agent.md` (site repo) → `projects/albery/server-context.md` as the full
  operational reference (UTF-8 verified clean, scanned for secrets — none). Curated docs link to it.
- Hardened `scripts/validate.py`: skip README, expand secret-placeholder allowlist (getpass/env/...).
