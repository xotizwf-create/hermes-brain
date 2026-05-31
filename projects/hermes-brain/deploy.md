---
id: hermes-brain-deploy
type: project
project: hermes-brain
tags: [deploy]
updated: 2026-05-31
secret_refs: []
---

# Hermes Brain — deploy / sync

## Principle
Hermes Brain is self-referential infrastructure. Prefer small, reviewable changes; validate the repository; commit and push only after approval or explicit instruction.

## Flow
1. Read `INDEX.md` and relevant instruction/skill files.
2. Modify only the needed files.
3. Run registry/build scripts if project manifests changed.
4. Run validation.
5. Show diff / summarize changes.
6. Commit and push when approved or explicitly instructed.

## Checks
- `projects/registry.yaml` regenerated after project manifest changes.
- Validation passes.
- Git diff contains no secrets.
- Changelog updated for material knowledge changes.

## Rollback
Use git history to revert a bad knowledge change. For broken Hermes runtime/config, avoid blind restarts and inspect logs first.
