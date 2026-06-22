# MeshCentral stale-docs / 502 runbook

Use this reference when Andigital PC remote-access documentation says MeshCentral exists, but the user sees a 502 or the secret PC page fails.

## Incident pattern observed 2026-06

Symptoms:
- Secret `/andigital/pc/<secret>/...` page or agent-download flow returns `502 Bad Gateway`.
- `andigital-pc-gate.service` can still be active and listening on its local gate port.
- `meshcentral.service` may be inactive/dead for weeks while still enabled and with files remaining under `/opt/meshcentral`.
- The brain/skill may still describe MeshCentral as live because no retirement note was committed.

Interpretation:
- This is a stale-docs / partial-retirement state, not proof that the user should install anything.
- Do not repair or restart automatically unless the owner explicitly wants the remote-PC feature restored.
- Do not tell the owner the link is ready until the backend has been verified live end-to-end.

## Safe workflow

1. Acknowledge the mismatch directly: docs said the feature existed, but live state shows the backend is not serving it.
2. Read-only checks only before confirmation:
   - service status for `meshcentral.service`, `andigital-pc-gate.service`, `nginx.service`;
   - local listening ports for the gate and MeshCentral backend;
   - current project brain entry for Andigital remote PC;
   - git/session history for explicit words like `retired`, `removed`, `disabled`, `убрали`, `отключили`.
3. If MeshCentral is stopped and there is no explicit removal note, ask the owner which direction is intended:
   - restore/re-enable MeshCentral remote PC access; or
   - mark it retired and remove it from active instructions.
4. If the owner confirms retirement, update the class-level skill/project brain so future sessions do not offer the stale URL.
5. If the owner confirms restore, follow production preflight first, then repair with explicit service/config verification and test the actual secret-path flow before sharing the URL again.

## Response style lesson

When the owner points out “we вроде убрали this” with frustration, do not defend the old docs. Say plainly that the docs and server state disagree, identify what was verified, and propose either restoring or retiring the feature.
