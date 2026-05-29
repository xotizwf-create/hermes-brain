---
id: security
type: engineering
tags: [security,auth,webhooks,hardening]
updated: 2026-05-29
secret_refs: []
---

# Security Standards

Use this guide for auth, authorization, secrets, webhooks, network exposure, dependency risk, and production changes.

## Baseline

- Treat production credentials, customer data, tokens, private keys, cookies, and logs as sensitive.
- Apply least privilege for users, service accounts, API tokens, SSH keys, and database roles.
- Validate inputs at trust boundaries.
- Keep authorization checks server-side.
- Use TLS for public endpoints.
- Do not log secrets or full auth headers.

## Webhooks And APIs

- Use per-provider secrets.
- Verify signatures when the provider supports them.
- Make handlers idempotent.
- Return success only after the event is durably accepted or safely ignored.
- Avoid exposing internal errors to callers.

## Server Hardening

- Disable password SSH where feasible after keys are confirmed.
- Use project-specific users where practical; avoid running public services as root.
- Restrict open ports.
- Keep system packages and runtime dependencies patched.
- Back up before hardening changes that can lock out access.

## Dependency Changes

- Prefer maintained packages.
- Check license and install surface for new dependencies.
- Avoid adding packages for trivial helpers.
- Run tests or smoke checks after dependency upgrades.
