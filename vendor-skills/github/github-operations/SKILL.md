---
name: github-operations
description: "Use when working with GitHub end-to-end: auth, repos, issues, code review, PR lifecycle, CI triage, releases, and repository inspection."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, git, gh, pull-requests, issues, code-review, ci]
    related_skills: []
---

# GitHub Operations

## Overview

One class-level GitHub workflow covering the full repository lifecycle. Prefer `gh` when authenticated; fall back to REST/GraphQL with `GITHUB_TOKEN`; always ground claims in live `git`/`gh` output.

## When to Use

- Authenticate or repair GitHub/`gh` access.
- Clone, fork, create, archive, or release repositories.
- Inspect codebase size/language composition before planning work.
- Create/triage issues and labels.
- Review PRs, post comments, request changes, or approve.
- Branch, commit, open PRs, monitor CI, merge, and clean up.

## Standard Discovery

```bash
git status --short --branch
REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
gh auth status || true
gh repo view --json nameWithOwner,defaultBranchRef || true
```

Extract `OWNER/REPO` from `gh repo view` or the remote before API calls.

## Subworkflows

### Authentication

Check `gh auth status` first. If unavailable, look for configured token sources without printing secrets. Never paste tokens in output.

### Repository Management

For clone/create/fork/release work, verify the target repo and remote URLs before mutating. For destructive repo settings, require explicit user confirmation.

### Codebase Inspection

Use language/LOC tools (for example `pygount` when available) to shape a plan. Report generated files/vendor exclusions explicitly.

### Issues

Search for existing issues before creating duplicates. Use templates for bug reports and feature requests when available. Include reproduction, expected/actual behavior, and acceptance criteria.

### Pull Requests and CI

Branch from updated base, commit focused changes, push, create PR, then monitor checks. For failing CI, fetch failed logs, fix, push, and re-check until green or blocked.

### Code Review

Review diffs against the correct base. Prioritize correctness/security/data-loss issues over style. Quote file paths/lines and provide actionable fixes.

## Pitfalls

- Putting a numeric task/PR id in a text search when a direct lookup is available.
- Claiming CI is green without `gh pr checks`, `gh run`, or API output.
- Posting review comments before verifying the diff base.
- Leaking tokens from env files or git credential helpers.

## Verification Checklist

- [ ] Repo and branch identified.
- [ ] Auth method verified.
- [ ] Target issue/PR/repo disambiguated.
- [ ] Side effects checked with `gh`/API/git output.
