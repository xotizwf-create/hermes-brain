---
name: ai-coding-agent-delegation
description: "Use when delegating coding work to autonomous coding CLIs such as Codex, Claude Code, OpenCode, or a Kanban-lane coding agent."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agent, codex, claude-code, opencode, delegation, worktrees]
    related_skills: [subagent-driven-development]
---

# AI Coding Agent Delegation

## Overview

Class-level instructions for using external autonomous coding CLIs as implementation/review lanes while Hermes retains responsibility for scope, verification, and user-facing reporting.

## When to Use

- The user wants a feature, refactor, bug fix, PR review, or batch issue work delegated to Codex/Claude Code/OpenCode.
- You need isolated implementation lanes in git worktrees or Kanban workers.
- You need to monitor a long-running coding agent and reconcile its output.

## Common Workflow

1. Verify repo state and create an isolated branch/worktree for the lane.
2. Choose the agent based on availability and task fit.
3. Run interactive CLIs with `pty=true`; long jobs use `background=true` plus `notify_on_complete=true` or polling.
4. Give the coding agent exact scope, files, acceptance tests, and commit/PR expectations.
5. Do not trust self-reports: inspect diffs, run tests, and verify artifacts yourself.
6. Reconcile agent output into the main branch/PR only after review.

## Agent-Specific Notes

### Codex

Requires a git repo; standalone CLI commonly runs as `codex exec ...` and should use PTY. Hermes OpenAI-Codex account onboarding/limit monitoring belongs under Hermes provider operations; never print OAuth tokens.

### Claude Code

Good for broad codebase reasoning and implementation. Keep prompts bounded and require tests/commits when appropriate.

### OpenCode

Useful for implementation and PR review where OpenCode is installed/configured. Treat it like any other external agent: verify diffs and tests.

### Kanban Codex Lane

Use when a Kanban worker wants Codex as an isolated implementation lane while Hermes owns task lifecycle, comments, blocking, completion, and handoff.

## Pitfalls

- Letting an external agent modify the user's active workspace without a branch/worktree.
- Ending after the agent says "done" without running tests or reading the diff.
- Forgetting PTY for interactive CLIs.
- Using an agent when a direct file edit/test loop would be faster and clearer.

## Verification Checklist

- [ ] Worktree/branch isolation established.
- [ ] Agent command actually ran and output was captured.
- [ ] Diffs reviewed by Hermes.
- [ ] Tests/builds run by Hermes after the agent.
- [ ] User report names real outputs, not agent self-report only.
