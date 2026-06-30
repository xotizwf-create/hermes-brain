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

When doing a sequence of small cleanup PRs and the next change depends on an earlier not-yet-merged PR (or `main` is currently red for a problem already fixed in that earlier PR), create the next PR as a stacked PR with `--base <previous-branch>` instead of piling unrelated fixes onto `main`. Verify locally against the stacked base, explain the stack in the PR body, and expect a small rebase/conflict if both cleanup steps touched nearby imports or module headers.

After pushing multiple quick commits, `gh pr checks --watch` can briefly show checks from the previous head. Before reporting final CI, re-read `gh pr view <PR> --json headRefOid,statusCheckRollup,mergeStateStatus,url` and verify the `headRefOid` matches the just-pushed commit; if checks are still queued/in progress for that head, wait again.

### Code Review

Review diffs against the correct base. Prioritize correctness/security/data-loss issues over style. Quote file paths/lines and provide actionable fixes.

## Pitfalls

- Putting a numeric task/PR id in a text search when a direct lookup is available.
- Claiming CI is green without `gh pr checks`, `gh run`, or API output.
- Posting review comments before verifying the diff base.
- Leaking tokens from env files or git credential helpers.
- Passing a PR/issue body with Markdown backticks, `$()`, or shell-sensitive text directly inside a quoted `gh pr create --body "..."` command. The shell can still expand command substitutions inside double quotes and corrupt the body. Write the body to a temporary Markdown file and use `--body-file`, then verify it with `gh pr view --json body`.

## Verification Checklist

- [ ] Repo and branch identified.
- [ ] Auth method verified.
- [ ] Target issue/PR/repo disambiguated.
- [ ] Side effects checked with `gh`/API/git output.
