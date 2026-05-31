---
id: hermes-brain-overview
type: project
project: hermes-brain
tags: [overview]
updated: 2026-05-31
secret_refs: []
---

# Hermes Brain — overview

## What it is
Hermes Brain is the canonical knowledge base for the current Hermes agent: project registry, instructions, reusable skills, operational rules, decisions and changelog. It is critical because it controls how the agent automates Александр's routine and how it safely works across all other projects.

## Criticality
Extremely high. Changes here affect the assistant itself. Edit carefully, validate before applying, avoid secrets, and keep everything versioned in git.

## Core capabilities
- Project map and per-project runbooks.
- Engineering/security/deploy instructions.
- Skills for repeatable workflows.
- User preferences and communication rules.
- Changelog/decisions/incident memory.

## Stack / storage
- Files in git, not a database.
- Local active copy on this server: `/root/.hermes/agent-knowledge`.
- GitHub repo: https://github.com/xotizwf-create/hermes-brain
- Current Hermes runtime/code exists separately from this knowledge repo.

## Current state
Active and loaded into the current Hermes system prompt. Any modification should be made as a small diff, validated, then committed/pushed after approval or explicit instruction.
