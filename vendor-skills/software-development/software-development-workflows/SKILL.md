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
2. Match the workflow to the user's ask before editing. If they ask to diagnose, explain why, review history, or find root cause, stay read-only unless they explicitly authorize a fix.
3. Make the smallest scoped change that satisfies the requirement.
4. Run targeted tests first, then broader checks when warranted.
5. If a repo path prevents command execution because of path encoding or filesystem-name constraints, create a temporary ASCII-safe symlink to the same directory and run the check through that link; keep the source path unchanged and remove/ignore the symlink afterward.
6. When a broad build/check is blocked by environment setup or resource pressure, do not treat that as code verification. Capture the blocker, run the strongest narrower checks available (for example targeted tests, compile/import checks, `tsc --noEmit`), and report both the successful checks and the blocked build honestly.
7. Inspect diffs before finalizing.
8. For audit/safety matrices, do not leave stale “open” risk items when the code already has handler-level gates and tests. Reconcile the matrix against actual handlers, registry/tool contracts, and regression tests, then mark items closed with the concrete mechanism.
9. Report exact commands and outcomes.

## Diagnostic-Only / Root-Cause Requests

Use this mode when the user asks “why did this happen?”, “how did the agent/system create this?”, “review what went wrong”, or otherwise frames the task as investigation rather than implementation. See `references/diagnostic-only-production-agent-incident.md` for a production/MCP-agent investigation checklist.

1. Treat production code, prompts, cron jobs, and persisted data as read-only by default.
2. Gather evidence from source, git history, live configuration, stored payloads, logs, and contracts/schemas. Prefer queries, diffs, and snapshots over patches.
3. Separate findings into: what happened, what component did it, what contract/instruction was expected, where behavior diverged, and what fix options exist.
4. Do not apply a “small obvious fix” just because the root cause looks clear. Ask or wait for explicit approval before modifying code, prompts, jobs, data, or reports.
5. If you accidentally changed something during a diagnostic-only task, immediately revert your own change, verify the revert in git and on the affected runtime if applicable, disclose it plainly, then continue diagnosis without further writes.

## Large Cleanup / Stacked Refactor PRs

Use this pattern when improving a large monolith or tangled module without changing behavior. See `references/stacked-monolith-cleanup.md` for a concrete checklist and reporting pattern from a successful stacked cleanup session.

1. Work in small stacked PRs: base each new cleanup branch on the previous cleanup branch, not directly on `main`, when earlier PRs are still open.
2. Extract only one cohesive class of helpers per PR (for example date helpers, LLM helpers, Google Sheets pure helpers). Avoid mixing refactor themes.
3. Preserve old call-site names with compatibility aliases when the goal is mechanical extraction; update call sites later only if that is the PR's explicit scope.
4. Add focused unit tests around the extracted pure helpers before opening the PR, especially for locale/formatting edge cases.
5. Verify with targeted tests, syntax/import checks, then the relevant broader suite. After opening the PR, wait for GitHub checks and fix failures before reporting done.
6. Do not touch production or merge stacked cleanup PRs unless the user explicitly asks.

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
