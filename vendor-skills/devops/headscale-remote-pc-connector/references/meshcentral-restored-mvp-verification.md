# MeshCentral restored MVP verification — 2026-06-21

Use this as a pattern when an old Andigital MeshCentral remote-PC flow was documented as stale/retired but Александр explicitly asks to revive it and get an agent install link.

## Durable lesson

Do not treat an old secret URL as either definitely dead or definitely live. Reconcile three things before sending the link:

1. Project brain status (`projects/andigital/remote-pc-access.md` or nearest current entry).
2. Service state on the Andigital host: nginx, `andigital-pc-gate.service`, `meshcentral.service`, and local MeshCentral port `127.0.0.1:3001`.
3. External HTTPS behavior of the secret landing page and the presence of both MeshCentral actions: login and `meshagents` install/download.

## Safe restoration pattern

- If nginx and `andigital-pc-gate.service` are active but the page is 502 and `meshcentral.service` is stopped, restart MeshCentral only after Александр explicitly asks to restore/use this exact flow.
- Verify MeshCentral logs/port locally, then verify the secret public URL over HTTPS.
- Parse/check the landing page links; it is not enough that the page returns HTTP 200. Confirm there is a download/install entry such as `/meshagents`.
- Only then give Александр the human landing page URL and short install steps.
- After a successful restore, update the project brain from “retired/stale” to “restored MVP / operational”, without writing raw secrets or passwords into docs.

## Owner-facing wording

Keep the final message practical:

- Say the page was restored and verified.
- Provide the landing page link, not internal service details.
- Tell the user to open it, choose “Добавить новый ПК / Скачать агент”, install, approve Windows admin prompts, and reply “установил”.
- Mention the consent model briefly: access should require local approval on the PC; do not imply silent hidden control.
