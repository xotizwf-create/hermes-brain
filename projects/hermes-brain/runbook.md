---
id: hermes-brain-runbook
type: project
project: hermes-brain
tags: [runbook, ops]
updated: 2026-05-31
secret_refs: []
---

# Hermes Brain — runbook

## Adding/updating projects
Use the brain skill `skills/add-project/`: create/update `projects/<slug>/`, regenerate `projects/registry.yaml`, validate, then commit after approval/explicit instruction.

## Updating instructions
Prefer the nearest existing instruction/skill. If no close instruction exists, create a small new one. Keep durable procedures in skills/instructions, not in chat memory.

## Validation
Run the repository validation script before finalizing changes. Fix frontmatter and secret-leak warnings before committing.

## Troubleshooting
- Bad project registry → regenerate from manifests, do not hand-edit registry.
- Missing project context → load `projects/registry.yaml`, then the specific project folder only.
- Risky Hermes config/gateway change → use the Hermes Agent skill and avoid changes that could disconnect Telegram without rollback.
