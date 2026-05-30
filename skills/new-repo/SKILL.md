---
name: new-repo
description: Use to create a new git repository — local and on GitHub (private by default) — and wire the remote. Covers the automated gh-CLI path and a manual fallback. Use when starting a new project or extracting code into its own repo.
---

# Skill: new-repo

## Goal
Create a repo locally, create it on GitHub (private), connect the remote, push the first commit.

## Prerequisites (one-time)
- `git` installed.
- GitHub CLI `gh` installed: `winget install --id GitHub.cli` (Windows).
- Authenticated: `gh auth login` (interactive — user completes browser/device flow once).
  Verify: `gh auth status`.
- **On the Hermes server this is already done** (2026-05-30): `gh` is installed and authed as
  `xotizwf-create` (scope `repo`), git credential helper wired. So Hermes can run this skill itself —
  `gh repo create`, clone, push, list. Details + the broad-token caveat: `engineering/secrets-access.md`
  → "Server GitHub access".

## Automated path (preferred — gh CLI)
From the project folder:
```powershell
# 1. local repo
git init -b main
git add .
git commit -m "Initial commit"

# 2. create on GitHub + push in one step (private)
gh repo create <owner>/<name> --private --source=. --remote=origin --push
```
- For public: `--public`. To create empty (no push yet): drop `--source/--push`.
- Verify: `gh repo view <owner>/<name> --json url,visibility`.

## Manual fallback (no gh / no auth)
1. Create an empty **private** repo on github.com (no README/.gitignore to avoid conflicts).
2. Wire and push:
```powershell
git init -b main
git add .; git commit -m "Initial commit"
git remote add origin https://github.com/<owner>/<name>.git
git push -u origin main
```

## Rules
- Private by default unless the user says public.
- `.gitignore` must exclude secrets before the first commit (`.env*`, keys, `*.secret.*`).
- Never commit secrets; run a quick scan of the diff before the first push.
- One repo per logical project; the brain is its own repo, separate from project repos.

## After creating
- If it's a project, register it with the `add-project` skill.
- Record the repo URL in the project manifest `github.repo`.
