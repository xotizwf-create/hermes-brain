---
id: example-project-deploy
type: project
project: example-project
tags: [deploy]
updated: 2026-05-29
secret_refs: []
---

# {Project name} — deploy

> General deploy principles: `engineering/deployment.md`. This file = project-specific steps.

## Flow
1. Push code to GitHub (`default_branch`).
2. Connect to prod (see `servers.md`).
3. Pull, install deps, run migrations, restart service.

## Commands
```bash
# project-specific deploy commands
```

## Post-deploy checks
```bash
# health endpoint / service status / logs tail
```

## Rollback
How to revert safely.
