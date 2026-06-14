---
name: kanban-operations
description: "Use when orchestrating or working inside Hermes Kanban: decomposition, worker lifecycle, comments, blocking, completion, retries, and review handoffs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, workers, task-lifecycle]
    related_skills: [ai-coding-agent-delegation]
---

# Hermes Kanban Operations

## Overview

Umbrella for both Kanban orchestrators and workers. The orchestrator decomposes and routes work; workers operate inside assigned workspaces, heartbeat/block/complete clearly, and leave machine-readable handoffs.

## When to Use

- Creating or decomposing Kanban task graphs.
- Running as a Kanban worker that needs lifecycle/pitfall detail.
- Debugging retries, blocked tasks, stale workspaces, or notification routing.
- Coordinating coding/research/review lanes across profiles.

## Orchestrator Responsibilities

- Decompose into small, independently verifiable tasks.
- Assign to the right profile; do not do specialist work in the orchestrator lane.
- Use dependencies and review gates instead of prose-only coordination.
- Keep task titles/result criteria concrete.

## Worker Responsibilities

- Start by showing the task/comment thread and current status.
- Respect `$HERMES_KANBAN_WORKSPACE` and tenant isolation.
- Send useful heartbeats for long tasks.
- Block with a concise decision request when input is needed; put detail in comments.
- Complete only with real evidence and structured metadata.

## Handoff Shapes

Coding work should include changed files, tests run/pass/fail, decisions, and diff/PR location. Review-required work should block with `review-required:` and place structured details in a comment.

## Pitfalls

- Calling `clarify` from a headless worker instead of blocking.
- Completing tasks that need human review.
- Claiming created cards without captured IDs.
- Modifying files outside the task workspace.
- Retrying without reading prior run outcomes.

## Verification Checklist

- [ ] Orchestrator created actionable cards with owners and dependencies.
- [ ] Worker read task state before acting.
- [ ] Block/complete calls include enough context for the next actor.
- [ ] Human-review gates are explicit where needed.
