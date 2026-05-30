---
name: aislop-code-quality
description: "Use when working on code changes, reviewing AI-generated code, cleaning a repository after an agent edit, preparing a PR, or investigating suspicious code quality issues. Run scanaislop/aislop to detect AI slop patterns such as narrative/trivial comments, swallowed exceptions, unsafe casts, hallucinated imports, dead code, duplicated helpers, TODO stubs, and oversized functions; remove only safe mechanical issues without changing project behavior."
---

# Skill: aislop-code-quality

## Overview

Use `aislop` as a deterministic quality gate for code the agent writes or reviews. It scans code
without an LLM, scores the result, and can mechanically fix some low-risk issues such as unused
imports and trivial comments.

Source tool: `scanaislop/aislop` by the scanaislop/heavykenny project. It supports TypeScript,
JavaScript, Python, Go, Rust, Ruby, PHP, and Java. Official commands include `scan`, `fix`, `ci`,
`rules`, and agent handoff modes such as `fix --codex`.

Manager: `skills/aislop-code-quality/scripts/aislop_guard.py` -> prod
`/root/.hermes/agent-knowledge/skills/aislop-code-quality/scripts/aislop_guard.py`.

## Default workflow

1. Before or after code edits, scan the smallest useful scope:

```bash
python3 /root/.hermes/agent-knowledge/skills/aislop-code-quality/scripts/aislop_guard.py scan --changes
```

Use full-repo scan when preparing a PR or when the user asks for a broad cleanup:

```bash
python3 /root/.hermes/agent-knowledge/skills/aislop-code-quality/scripts/aislop_guard.py scan .
```

2. Read the findings. Treat errors as review blockers and warnings as cleanup candidates. Do not
blindly rewrite working code just to improve the score.

3. Apply safe mechanical fixes only when they do not change behavior:

```bash
python3 /root/.hermes/agent-knowledge/skills/aislop-code-quality/scripts/aislop_guard.py fix --changes
```

4. Re-run scan and the project's normal tests. If tests are absent, run the closest available
typecheck/lint/build command and say what could not be verified.

## Install prerequisite

Requires Node 20+. Install globally for faster repeated use:

```bash
npm install -g aislop
```

No install is required if network access is available:

```bash
npx -y aislop@latest scan
```

## Commands

Scan changed files:

```bash
python3 skills/aislop-code-quality/scripts/aislop_guard.py scan --changes
```

Scan staged files before commit:

```bash
python3 skills/aislop-code-quality/scripts/aislop_guard.py scan --staged
```

Run CI gate:

```bash
python3 skills/aislop-code-quality/scripts/aislop_guard.py ci .
```

Generate an agent handoff prompt for issues that need reasoning:

```bash
npx -y aislop@latest fix --codex
```

## Fix rules

- Safe by default: allow `aislop fix` only for mechanical cleanup. Review the diff afterwards.
- Never run `aislop fix -f` or dependency/file deletion fixes without explicit user approval.
- Never remove code solely because it looks AI-generated. Remove it only when it is demonstrably
  unused, duplicated, trivial, or harmful and project tests or local reasoning support the change.
- Preserve public APIs, migrations, generated files, snapshots, lockfiles, and vendored code unless
  the user explicitly asks to include them.
- If `aislop` flags a pattern but the code is intentionally defensive or domain-specific, document why
  it stays instead of forcing the score.
- Always re-run the relevant scan after fixes and include the before/after result in the final answer.
