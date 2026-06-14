---
name: software-development-workflows
description: "Use when planning, debugging, testing, reviewing, or implementing software changes: plans, spikes, TDD, systematic debugging, code review, subagent development, and language/runtime debuggers."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [software-development, planning, debugging, testing, code-review, subagents]
    related_skills: []
---

# Software Development Workflows

## Overview

Umbrella for core engineering practices independent of a single repo or tool. Choose the workflow mode (plan, spike, TDD, debug, review, delegate) and keep evidence from real commands/tests at the center.

## When to Use

- Writing implementation plans.
- Running throwaway spikes before committing to a design.
- Practicing TDD / RED-GREEN-REFACTOR.
- Systematic root-cause debugging.
- Pre-commit code review and quality gates.
- Subagent-driven development and review.
- Python `pdb`/`debugpy` or Node Inspector debugging.

## Router

| Situation | Workflow |
|---|---|
| User asks for a plan only | Write a bounded plan; do not execute. |
| Uncertain technical approach | Spike in isolation; keep/delete artifacts intentionally. |
| New behavior or bug fix with clear spec | TDD: failing test, implementation, refactor. |
| Mysterious failure | Systematic debugging: reproduce, localize, fix, verify. |
| Changes ready or AI-generated code | Code review gates: security, correctness, tests. |
| Large implementation | Subagent-driven development with parent verification. |
| Runtime inspection needed | Python/Node debugger workflow. |

## Common Discipline

1. Understand current state from files, tests, logs, and git.
2. Make the smallest scoped change that satisfies the requirement.
3. Run targeted tests first, then broader checks when warranted.
4. Inspect diffs before finalizing.
5. Report exact commands and outcomes.

## Pitfalls

- Planning forever when the user asked to build.
- Fixing symptoms before reproducing the bug.
- Trusting subagent or debugger hypotheses without verifying.
- Skipping tests because a change is "obvious".

## Verification Checklist

- [ ] Workflow mode selected.
- [ ] Evidence gathered before changing code.
- [ ] Changes made with file tools/patches.
- [ ] Tests/checks run and results reported.
