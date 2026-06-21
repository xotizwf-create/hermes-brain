---
name: headscale-remote-pc-connector
description: "Run Codex/Hermes agent on andigital.ru and connect to consented remote PCs over self-hosted Headscale/Tailscale mesh via SSH."
version: 1.0.0
author: Hermes
license: MIT
platforms: [linux, windows, macos]
metadata:
  hermes:
    tags: [devops, headscale, tailscale, ssh, remote-access, windows, codex]
---

# Remote PC Access for Andigital

Use this skill when Александр asks to set up, inspect, troubleshoot, or reason about the scheme where the agent/operator connects to remote user PCs from `andigital.ru`.

## Current status — old MeshCentral flow is retired

As of 2026-06-21, the previous “simple MeshCentral invite link” flow on `www.andigital.ru` is **not operational and must not be offered to the owner as a ready connection method**. MeshCentral files and gateway leftovers may still exist, but `meshcentral.service` was found stopped since 2026-06-03, and the old agent-download path can return 502. Treat this as a retired/stale feature unless Александр explicitly asks to revive it.

When Александр asks “can you connect to my PC?”, answer: yes, a future connection is possible, but a remote-access method must be selected/rebuilt and verified first. Depending on the task, choose rebuilt MeshCentral, Headscale/Tailscale+SSH for technical machines, RustDesk/AnyDesk, or a one-off consent-based support agent. Do not send the old secret MeshCentral URL as if it works.

## Historical simple scheme

Previously, for “максимально просто подключаться к любому ПК”, MeshCentral on `www.andigital.ru` was preferred over custom PowerShell/Headscale/OpenSSH connector scripts. This is now historical context only.

Historical setup:
- MeshCentral is installed in `/opt/meshcentral` and previously ran as `meshcentral.service`.
- Public human UI is **not** exposed at `https://www.andigital.ru/`. Use only the secret-path entry `https://www.andigital.ru/andigital/pc/<secret>/`; the concrete URL lives in the secure per-project env store as `ANDIGITAL_REMOTE_PC_ACCESS_URL` / `ANDIGITAL_PC_ACCESS_URL`, never in chat or docs.
- Nginx keeps `/andigital/secret/` routed to Hermes Vault and routes `/andigital/pc/<secret>/` through `andigital-pc-gate.service` before proxying to MeshCentral on `127.0.0.1:3001`.
- `andigital-pc-gate.service` stores only the SHA-256 hash of the high-entropy URL key for auth checks; do not put the raw key in nginx config or committed docs. Nginx access logging is disabled for secret-token paths.
- MeshCentral is configured with `mpsPort: 0` and `portBind: 127.0.0.1`; do not expose extra technical ports. Keep only the minimal root-level MeshCentral agent transport endpoints needed by already-installed agents.
- The post-login MeshCentral UI is themed only through MeshCentral's official custom static files: `public/styles/custom.css` and `public/scripts/custom.js`. Use them for cosmetic styling of the header, device list, cards, buttons, forms, menus, and login shell; do not modify authentication, websocket/agent paths, cookies, permissions, local consent prompts, or remote-control logic.
- Admin user is `alexander`; the temporary password is stored only in the secure server store, not in this skill.
- Default device group: `My PCs`.
- Security baseline: no public self-registration, no guest device sharing, short idle logout, strong future password policy, and domain-wide local consent/notification for Desktop, Terminal, and Files. Desktop access must also show the MeshCentral privacy bar on the PC.
- Current consent model: remote screen/terminal/files require local approval on the PC; if the user does not approve the local prompt, the operator must stop and ask for approval rather than bypass it.
- For owner requests like “подключись к моему ПК и скажи, что открыто”, use the read-only MeshCtrl window-title workflow first: list visible window titles without clicks, typing, screenshots, file reads, uploads/downloads, or setting changes. See `references/meshcentral-read-only-window-inspection.md`.

Historical operational flow for a new PC — do not use without rebuilding/verifying:
1. Send Александр/the PC owner the MeshCentral invite link generated from the `My PCs` group.
2. They open the link, download/install the agent, and approve the Windows prompt.
3. The PC appears in MeshCentral; use the web UI for desktop, terminal, files, and support.
4. Avoid custom `.cmd`/PowerShell installers unless MeshCentral is unsuitable for that конкретный кейс.

This replaced the earlier Headscale/OpenSSH connector attempt because it was too fragile for Windows and not simple enough for non-technical users.

## Architecture

- Coordinator/server: `andigital.ru` / `vpn.andigital.ru` with Headscale behind Caddy.
- Agent runtime: Codex/Hermes runs on the server, not on target PCs.
- Server also runs Tailscale client as `tag:agent` and keeps Amnezia enabled for OpenAI access.
- Target PCs join the mesh as `tag:target` via `--login-server https://vpn.andigital.ru`.
- Linux/macOS targets: Tailscale SSH, user `codex`, no SSH key distribution.
- Windows targets: OpenSSH Server + local `codex` user + agent public key + watchdog.

## Key security model

- Use only with explicit consent from the PC owner.
- Agent can reach targets over SSH; targets cannot reach each other.
- ACL baseline:
  - `tag:agent` → `tag:target:22`
  - Headscale SSH policy allows user `codex`.
- Use reusable ephemeral target pre-auth key with short TTL; revoke/delete node as kill switch.
- Prefer a separate `codex` account with minimal privileges; Windows admin only when operationally necessary.
- Never print auth keys, private keys, passwords, or secrets in chat.

## Server prerequisites

Before setup on production server, run the server preflight protocol from `/root/.hermes/agent-knowledge/engineering/server-preflight.md`.

### DNS for `andigital.ru`

The `andigital.ru` DNS zone is managed through Reg.ru. Mechanism for coordinator subdomains: open the domain control panel, go to DNS servers / zone management, add a resource record, choose type `A`, set the subdomain label (for example `vpn`), and point it to the server IP (`217.198.12.236` for the current `andigital` host). Wait for propagation before issuing TLS or joining nodes.

Required public ports:
- `80/tcp` for TLS issuance.
- `443/tcp` for Headscale API/coordination through Caddy.
- `3478/udp` for embedded DERP/STUN.
- `41641/udp` for Tailscale direct P2P when possible.

Server stack:
- Docker Compose runs Headscale `0.23.0` and Caddy.
- Headscale data is SQLite under the mounted data volume.
- Config uses `server_url: https://vpn.andigital.ru`, MagicDNS base domain `mesh.andigital`, embedded DERP region, ACL file policy.

## Server setup outline

1. Ensure DNS `vpn.andigital.ru` points to the server IP.
2. Choose deployment mode:
   - Fresh/empty host: Headscale behind Caddy with Docker Compose is fine.
   - Existing `andigital` production host where nginx already owns ports 80/443: **do not install Caddy/Docker for this**. Install the Headscale `.deb`, run it as the systemd service on `127.0.0.1:8080`, expose it through an nginx `server_name vpn.andigital.ru` block, and keep embedded DERP/STUN on UDP 3478.
3. Verify `/health` locally both directly (`127.0.0.1:8080`) and through nginx with Host `vpn.andigital.ru` before touching TLS.
4. Create Headscale user `andigital`.
5. Restart Headscale to apply ACL.
6. Create two pre-auth keys:
   - agent key: short-lived, `tag:agent`.
   - target key: reusable, ephemeral, about 30 days, `tag:target` or `tag:personal-target` for personal-PC two-role mode.
7. Install Tailscale on the server and join it to the self-hosted coordinator as hostname `agent-andigital`, `tag:agent`, `--ssh=false` only after DNS and HTTPS are working.
8. For Windows targets, create `~/.ssh/agent_to_windows` and embed only its public key in the Windows enrollment script.

### Existing nginx/certbot pitfall on `andigital`

On the live `andigital` host, certbot may fail because `/usr/local/lib/python3.10/dist-packages` shadows Ubuntu packages (seen with local `cryptography`/`urllib3`). Fix by moving only the conflicting local duplicate packages to a root backup directory, then re-test `certbot --version`. Do not remove system packages and do not reload nginx until `nginx -t` passes.

## Delivery rule for generated Windows files

When generating a Windows enrollment script or any other file that Александр must download, never rely on a plain local path in the final text. Before saying the file is ready:

1. Verify the file exists on disk.
2. Prefer sending a `.zip` archive containing the script, because Telegram/gateway may render a bare `.ps1` local path as text instead of a downloadable document.
3. Attach the file in the final answer with a standalone `MEDIA:/absolute/path/to/file` line, not inside explanatory prose.
4. If a prior attempt produced visible `MEDIA:/...` text in Telegram, do not repeat the same transport. Repackage as `.zip` or another safe document format and attach that.
5. Only after the user visibly receives a downloadable attachment or confirms receipt, say that the file is attached.
6. Do not write instructions like “download this file” unless the attachment is actually visible to the user as a file.

This rule exists because Telegram may show text while dropping/stripping a local file path if it was not delivered as a native attachment.

## Windows script robustness rule

Generated Windows enrollment scripts must not silently close on failure. They should:

- Check that PowerShell is running as Administrator before doing anything else.
- Write a transcript/log to a predictable path such as the Desktop or `C:\ProgramData\CodexConnector`.
- Wrap the main body in try/catch and print the error clearly.
- Pause at the end when launched interactively, so a double-clicked or newly opened console does not disappear before the user can read the result.
- Prefer instructions that run the script from an already-open Administrator PowerShell window instead of double-clicking the `.ps1`.
- Do not use ad-hoc `.cmd` launchers with non-ASCII/Russian text and complex nested PowerShell quoting. In practice this broke by splitting quoted Russian text into bogus commands like fragments of “Открой/PowerShell/пусти”. If a launcher is necessary, keep it ASCII-only and test it locally before sending.

This rule exists because a Windows `.ps1` launched from Explorer can blink and close, hiding admin/winget/OpenSSH/Tailscale errors, and a fragile `.cmd` wrapper can fail before PowerShell even starts.

## Windows target enrollment

Run PowerShell as Administrator:

1. Install Tailscale.
2. Join with:
   - `--login-server https://vpn.andigital.ru`
   - target pre-auth key
   - `--advertise-tags=tag:target`
   - `--accept-dns=true`
   - `--unattended`
3. Install and start OpenSSH Server.
4. Make OpenSSH firewall rule enabled for any profile.
5. Create local user `codex`.
6. If `codex` is administrator, put the agent public key into `C:\ProgramData\ssh\administrators_authorized_keys` and set strict ACLs for SYSTEM and local Administrators SID.
7. If `codex` is not administrator, use `C:\Users\codex\.ssh\authorized_keys`.
8. Add watchdog scheduled task as SYSTEM to keep Tailscale, sshd, firewall rule, and routing metrics healthy.

## Windows Amnezia routing fix

If Amnezia is present on the target PC, keep Tailscale route priority above Amnezia for the mesh and make Amnezia win default internet routing:

- Tailscale IPv4 metric: `1`
- AmneziaVPN IPv4/IPv6 metric: `5`
- AmneziaVPN `IgnoreDefaultRoutes`: disabled
- Broadband metric: higher, e.g. `35`

The watchdog should repeat this because Amnezia may recreate interfaces after reconnect/reboot.

## Linux/macOS target enrollment

- Install Tailscale.
- Create `codex` user.
- Join with self-hosted login server, target key, `tag:target`, DNS accepted, and `--ssh` enabled.
- Agent connects as `ssh codex@<magicdns-name>`.

## Agent command pattern

- Linux/macOS targets: `ssh codex@<target-name> ...`
- Windows targets: use the Windows private key from `~/.ssh/agent_to_windows` and PowerShell commands.
- For complex Windows diagnostics, send PowerShell script over stdin to avoid quoting issues.

## Diagnostics checklist

If node is missing:
- Check Headscale nodes and pre-auth key status.
- Check Headscale/Caddy logs and DNS/TLS/firewall.

If MeshCentral shows a public `ip` for a Windows PC, do **not** assume SSH to that public IP reaches the same PC. First compare SSH host-key fingerprints:
- Local scan from the agent host: `ssh-keyscan <public-ip> | ssh-keygen -lf -`.
- Remote PC host keys via MeshCentral command: `ssh-keygen.exe -lf C:\ProgramData\ssh\ssh_host_*_key.pub`.
If fingerprints differ, the public IP/port is NAT, router, or another host; direct SSH will be slow/impossible regardless of authorized keys. Use MeshCentral for diagnostics or set up a real private overlay/tunnel (Headscale/Tailscale, reverse SSH, or MeshCentral relay workflow) before trying to optimize command speed.

If mesh works but SSH fails:
- Verify local sshd is running and port 22 is listening.
- Verify firewall profile is not restricted to Private.
- Check Tailscale shields-up.
- Check ACL allows `tag:agent` to `tag:target:22` and SSH user `codex`.
- On Windows, if the account is in Administrators, OpenSSH may ignore `%USERPROFILE%\.ssh\authorized_keys` and require `C:\ProgramData\ssh\administrators_authorized_keys`. Use well-known SIDs for ACLs to avoid localized group-name issues: SYSTEM `S-1-5-18`, Administrators `S-1-5-32-544`.

If routing is wrong:
- On Linux server, route to `100.64.0.0/10` must go through Tailscale, not Amnezia.
- On Windows target, mesh route must prefer Tailscale; default internet may prefer Amnezia when needed.

## Operational opinion

This design is strong because it keeps model/API access centralized on the server, avoids installing Codex on customer PCs, gives stable NAT traversal, and supports a hard kill switch through Headscale node deletion. Main risks are consent/audit, Windows OpenSSH key placement, reusable target key leakage, overly broad admin privileges, and Headscale/SQLite backup/monitoring. Add logging, key rotation, backups, and per-client tags/users if the fleet grows.
