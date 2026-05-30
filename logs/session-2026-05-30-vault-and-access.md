---
id: session-2026-05-30-vault-and-access
type: log
tags: [session, handoff, vault, secrets, github, google, ux, mcp]
updated: 2026-05-30
secret_refs: []
---

# Session digest (2026-05-30, part 2) — UX, access & the secret Vault

Handoff for the next chat. This repo (`C:\hermes-brain`) is **Hermes' brain** (knowledge in git,
mirrored to prod `217.198.12.236:/root/.hermes/agent-knowledge`). Hermes = the always-on Telegram
agent (model gpt-5.5) running as **root** on prod host `andigital` (Ubuntu 22.04). The owner talks to
Hermes in Russian via Telegram. Full secret model: `engineering/secrets-access.md`.

## How work gets to the server (the operational pattern used all session)
- No SSH key on the PC yet → connect with **Paramiko**, creds from `C:\hermes-brain\.env` (gitignored;
  Russian keys: `IP сервера агента`, `Пользователь`, `Пароль`). Throwaway helper script in TEMP:
  reads `.env`, `exec_command`. Cyrillic console = cp1251 → always `sys.stdout.reconfigure(utf-8)`.
- Brain change flow: edit → `python scripts/validate.py` → commit → `git push` → on server
  `cd /root/.hermes/agent-knowledge && git pull --ff-only`. End every commit msg with the Claude
  Co-Authored-By line. **Never** commit secrets (validator enforces; `.env*`, `*.local.txt` gitignored).
- Gotchas hit: `python -c` with literal `\n` breaks → use heredoc `python3 - <<'PY'`. `pkill -f 'git…'`
  can match your own SSH command and kill the session. nginx includes **all** of `sites-enabled/` → keep
  `.bak` files OUT of it (put backups in `/root/nginx-backups/`).

## What was done this session (newest first; details in logs/changelog.md)

1. **MCP "обнови" fixed.** Refresh restarted the gateway *in-process*, killing the live turn →
   "Gateway shutting down" garbage. `skills/connect-mcp/scripts/hermes_mcp.py` now has
   `detached_restart()` (restart via `systemd-run --on-active`, off the gateway's cgroup);
   `cmd_refresh`+`apply_live` use it. "обнови" is an explicit trigger.

2. **UX made clean & honest (config, no run.py patch).** In `~/.hermes/config.yaml`:
   `display.platforms.telegram.tool_progress: off` (the `📚 skill_view`/`💻 terminal:"…"` bubbles were
   the "technical noise" the owner hated). `long_running_notifications: false` (the `⏳ Working — N min`
   heartbeat is hardcoded English + leaks the tool name). **The real live-progress signal = the model's
   own Russian narration** (`interim_assistant_messages: true`, already on) — driven by the
   **system_prompt**, which was expanded with hard rules: only Russian; narrate steps briefly ~every
   30s («Проверяю токен…»); honest "не нашёл" instead of made-up answers; no tool names/commands/paths;
   business tone. Mirrored in `profile/communication.md`. Knobs documented in
   `engineering/hermes-gateway-ux.md`. (`show_reasoning` stays OFF — EN block fights Russian-only;
   no `ru` UI locale ships. Native Telegram "печатает…" indicator already auto-resumes = "Думаю…".)
   Note: `display.personality: kawaii` left as-is (system_prompt tone should dominate); flip if needed.

3. **GitHub account access on prod.** Installed `gh` (`/usr/bin/gh` 2.93). Authed as **`xotizwf-create`**
   by **reusing the PC's gh OAuth token** (owner's choice; scopes `repo, read:org, gist` = r/w to ALL
   repos). Token at `/root/.hermes/secure/github_token` (600) + `/root/.config/gh/hosts.yml`;
   `gh auth setup-git` wired git creds. Hermes can list/clone/edit/push/create. ⚠ Same token as the PC —
   PC re-login may rotate it → server breaks (re-run the reuse step). `engineering/secrets-access.md`
   → "Server GitHub access".

4. **Google Calendar → read/write.** Changed the Calendar scope in
   `skills/read-links/scripts/google_oauth_login.py` (`calendar.readonly` → `calendar`), re-ran the PC
   browser consent (owner clicks Allow), delivered the new token to BOTH
   `/root/.hermes/secure/google_oauth_token.json` and the bundled-tool compat path
   `/root/.hermes/google_token.json` (600). Owner **published the OAuth app to Production**, so re-minted
   → long-lived token (no 7-day expiry). Hermes reads + creates/deletes events via
   `/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py calendar list|create|delete`
   (ISO+TZ; edit = delete+create). Verified end-to-end. Cloud project `gen-lang-client-0802797266`.

5. **Project-secrets capability** (`skills/store-project-secrets/`). Owner workflow: find a repo via
   `gh`, store its `.env` / prod-server password, remember the project (repo, prod host/user, var NAMES,
   refs) secret-free in `projects/<slug>/`. Helper `skills/secure-access/scripts/save_project_secrets.py`
   (stdin/`--from`, shreds temp paste, prints NAMES only). **Secure intake principle (owner pushed
   hard):** a secret pasted into Telegram already leaks to Telegram **and** the LLM provider. So the
   PRIMARY path is `skills/secure-access/scripts/secret_push.py <slug> <path>` (run on the PC → SFTPs the
   `.env` straight into the server vault over SSH, never through chat/LLM). Chat-paste is a discouraged
   fallback → "treat as exposed, rotate".

6. **Hermes Vault — web UI for per-project secrets** (the big build; `skills/secure-access/vault/`).
   - Dependency-free **stdlib** app `secrets_ui.py` (no pip on the box — uses `hashlib.scrypt`, `hmac`,
     `http.server`, `urllib`). Lists the owner's GitHub repos (REST), per-project `.env` CRUD, tied to
     repos. Restyled to the **andidigital site look** (light theme, ink `#0f172a`, lime `#c0fc41`/
     `#a3e635`, soft shadows, brand header + site favicon, repo search filter, 120s repo cache).
   - **Live:** `https://www.andigital.ru/andigital/secret/<URL_TOKEN>/` over the existing Let's Encrypt
     TLS. The full URL (with token) is in `C:\hermes-brain\hermes-vault-url.local.txt` (gitignored via
     `*.local.txt`) — token was NEVER sent through chat/LLM (generated server-side, SFTP-pulled).
   - **Security:** 2 factors = unguessable URL token in the path (wrong/missing → 404) + a password
     stored only as **scrypt** hash; HMAC `httponly`+`Secure`+`SameSite` session (1h); CSRF on forms;
     per-IP login lockout; `access_log off` so the token isn't logged. Owner already set the password
     (first-run done → now shows the styled login).
   - **Least privilege:** runs as unprivileged system user **`hermesvault`** (group `hermessec`), bound
     `127.0.0.1:8787`, behind nginx; systemd-hardened (`ProtectSystem=strict`, `ProtectHome`,
     `ReadWritePaths` = only the store + data dir, syscall filter). If popped → not root.
   - **Unified secret store (relocated):** `/opt/hermes/secure/projects/<slug>/` —
     `2770 hermesvault:hermessec` (setgid), files 660. Shared by the **root agent** and the **web UI**.
     `save_project_secrets.py` + `secret_push.py` repointed here (were `/root/.hermes/secure/projects`).
   - **Turnkey/resale:** all branding in `config.json` + nginx `base_path`; one codebase, many instances.
     Install steps + operate/rotate in `skills/secure-access/vault/README.md`. systemd unit
     (`hermes-vault.service`) + nginx snippet (`nginx-location.conf`) versioned in the brain.

## Where things live on the server (no secrets here)
| Thing | Path |
|---|---|
| Brain clone (synced) | `/root/.hermes/agent-knowledge` |
| Agent secrets (google/gmail/github tokens, access-map, secrets.yaml) | `/root/.hermes/secure/` (root 600) |
| **Project secret vault (shared)** | `/opt/hermes/secure/projects/<slug>/` (2770 hermesvault:hermessec) |
| Vault app + data | `/opt/hermes/vault/secrets_ui.py`, `/opt/hermes/vault/data/{config.json,gh_token,PUBLIC_URL.txt}` |
| Vault service / nginx | `/etc/systemd/system/hermes-vault.service`; location in `/etc/nginx/sites-enabled/andidigital` |
| Hermes config | `/root/.hermes/config.yaml` (system_prompt, display.*) |
| The website (andidigital) | `/var/www/andidigital` (React/Tailwind), backend `127.0.0.1:3000`, domain `www.andigital.ru` |

## Open / pending (next steps)
- **SSH key vs password (chosen, NOT done yet).** Owner picked "SSH key instead of the root password";
  I explained how it works but we pivoted to the Vault. To do: generate an ed25519 key on the PC, put the
  pubkey in `217:/root/.ssh/authorized_keys`, keep the password as a temporary fallback, then drop the
  plaintext password from `C:\hermes-brain\.env` (and optionally disable password auth). Also a server-side
  agent key in the vault for connecting to project prod servers.
- **Rotate chat-exposed secrets** (anything the owner ever pasted into Telegram; the reused gh token is
  broad). Consider a dedicated fine-grained GitHub PAT for the server (currently coupled to the PC).
- **Optional vault hardening:** `age` encryption-at-rest of `/opt/hermes/secure` (protects backups/disk
  theft; not against live root). Per-variable edit/delete in the UI. Add a "change password" page.
- Older threads still open from session 1: reconcile legacy `186.246.7.32` refs in albery docs; add the
  2nd project; re-wire Albery MCP (`mcp.m4s.ru`, secret not on 217).

## Owner preferences reaffirmed this session
Russian only, max brevity, honest "не нашёл", business tone (no kawaii/emoji spam), no technical/English
strings in chat, think years ahead + build production-grade ("аккуратно максимально", resaleable).
Security-first: secrets must never transit chat/LLM; one secure place the agent can reach.
