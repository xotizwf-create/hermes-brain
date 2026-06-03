---
id: andigital-remote-pc-access
type: project
tags: [andigital, meshcentral, remote-access, security, windows, consent]
updated: 2026-06-03
secret_refs: []
---

# Andigital remote PC access — secure MeshCentral baseline

## Purpose

Andigital remote-PC access is the owner's simple support channel: send a link, the PC owner installs the MeshCentral agent, and the PC appears in the self-hosted panel. It is for explicitly consented access only.

## Live public entry points

- Panel: `https://www.andigital.ru/`
- New-PC onboarding shortcut: `https://www.andigital.ru/pc`
- Default device group: `My PCs`
- Current known personal PC: `DESKTOP-FSKTPR4`

No passwords, invite tokens, enrollment keys, private keys, or session keys belong in this repository.

## Server shape

- MeshCentral runs as `meshcentral.service` from `/opt/meshcentral`.
- It is reverse-proxied by nginx over HTTPS.
- MeshCentral binds locally to `127.0.0.1:3001`.
- Extra technical AMT/MPS exposure is disabled; do not open additional public ports unless the owner explicitly approves a new use case.
- Nginx must keep the Hermes Vault path under `/andigital/secret/` working.

## Mandatory safety baseline

The remote-access system must remain visible and consent-based:

1. Public self-registration stays disabled.
2. Guest device sharing stays disabled.
3. Only expected owner/admin accounts remain; temporary diagnostic users must be deleted before finishing a task.
4. MeshCentral sessions use a short idle timeout and logout on idle.
5. Password requirements must be enforced for future password changes.
6. Desktop, Terminal, and Files access must require local consent on the PC.
7. Desktop access must show the local privacy bar / notification that a remote connection is active.
8. The notification text must clearly say that remote access is active and tell the local user what to do if it is unexpected.

Current intended consent flags:

- Desktop notify
- Desktop prompt
- Desktop privacy bar
- Terminal notify
- Terminal prompt
- Files notify
- Files prompt

## Operator rules

- Never bypass the local-consent prompt. If the PC owner does not approve the prompt, stop and ask them to approve locally.
- Do not silently inspect private data. For “what do you see?” first list window titles; take a screenshot only when explicitly useful for the owner’s request.
- Do not click, type, move the mouse, upload/download files, execute commands, or change PC settings unless the owner explicitly asked for that exact action.
- Summaries to the owner should describe only the practical result. Do not dump logs, database ids, config secrets, screenshots, private message text, or credentials.
- If a temporary operator account is created for a diagnostic action, remove it before final response and verify that only the expected account(s) remain.

## Safe change workflow

Before changing the server:

1. Run the universal server preflight and keep the operation light; the host is memory-constrained.
2. Back up MeshCentral config and database before editing.
3. Make narrow config/database changes only.
4. Fix ownership of MeshCentral data back to the service user after any recovery/local admin command.
5. Restart only MeshCentral unless nginx config changed.
6. Verify:
   - `meshcentral` is active;
   - nginx is active;
   - `https://www.andigital.ru/` returns OK;
   - `https://www.andigital.ru/pc` returns OK;
   - expected users only;
   - expected device group/device still present;
   - all consent flags are enabled.

## Known pitfall

After local MeshCentral account-recovery commands, database files can become owned by `root`, causing a temporary proxy error even when the service looks active. Fix file ownership under the MeshCentral data directory and restart only MeshCentral.
