---
id: hermes-brain-servers
type: project
project: hermes-brain
tags: [servers, access]
updated: 2026-05-31
secret_refs: [proj/hermes-brain/server/env, proj/hermes-brain/github/deploy-key, proj/hermes-brain/hermes/config, proj/hermes-brain/hermes/env]
---

# Hermes Brain — servers & access

> Credentials are referenced by NAME only. Real values live in the secure zone. Never print or commit secrets.

## Current production/runtime host
- Host alias: `current-hermes-host`
- Host: `217.198.12.236`
- Brain path: `/root/.hermes/agent-knowledge`
- Hermes home: `/root/.hermes`
- Hermes code/runtime path in current session: `/usr/local/lib/hermes-agent`
- Messaging: Telegram gateway connected to Александр.

## Secure references
- `proj/hermes-brain/server/env` — server/runtime access bundle.
- `proj/hermes-brain/github/deploy-key` — git sync access if used.
- `proj/hermes-brain/hermes/config` — Hermes configuration references.
- `proj/hermes-brain/hermes/env` — Hermes environment secrets.

## Safety rules
- Do not commit secrets.
- Do not edit another Hermes profile's skills/plugins/cron/memories unless explicitly requested.
- Before gateway/service changes, understand restart impact and keep rollback path.
- Before heavy server work, follow `engineering/server-preflight.md`.
