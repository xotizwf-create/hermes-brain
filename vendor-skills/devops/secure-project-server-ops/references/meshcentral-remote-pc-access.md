# MeshCentral remote PC access runbook

Use this when Александр wants a very simple way for an agent/operator to connect to arbitrary Windows PCs: "send link → user installs agent → PC appears".

## Preferred class-level approach

Prefer a managed remote-access agent (MeshCentral) over custom Windows connector scripts when the goal is human/operator access to screen, files, or terminal. Avoid building a PowerShell/.cmd stack with Tailscale auth keys, OpenSSH, local Windows users, watchdogs, and firewall rules unless the user explicitly needs SSH-style machine access.

Why MeshCentral fits this class:
- self-hosted server, not a third-party remote desktop SaaS;
- small per-PC agent;
- devices appear in a web panel/group;
- browser access to Desktop, Files, and Terminal;
- onboarding UX is one link/invite, not copy-pasting scripts.

## Server-side safety pattern

1. Run the normal server preflight first (`free -m`, swap, running services, disk, load). Small VPS boxes can run MeshCentral, but installation/restarts should be bounded and verified.
2. Put MeshCentral behind nginx/HTTPS. Keep the Node service bound to localhost, expose only the reverse-proxied HTTPS endpoint.
3. For Andigital specifically, do **not** expose the human MeshCentral UI at domain root. Route it only through `/andigital/pc/<secret>/` via `andigital-pc-gate.service`, which verifies the high-entropy URL key by hash. Keep the raw URL key only in the secure project env store; never in nginx config, committed docs, or chat.
4. For Andigital's internal panel look, use the official MeshCentral custom static files only: `/opt/meshcentral/node_modules/meshcentral/public/styles/custom.css` and `/opt/meshcentral/node_modules/meshcentral/public/scripts/custom.js`. This is a cosmetic layer for the header/sidebar/device cards/forms/modals/login shell. Do **not** edit remote-control/authentication/websocket logic, do not weaken consent prompts, and do not move agent transport paths just to improve visuals. See `references/meshcentral-ui-theming.md` for the safe theming workflow and verification checklist.
5. If a public domain already has nginx/TLS and an unused vhost, reuse it only after checking existing paths/services. Do not break existing secret/vault routes.
6. Use a dedicated unprivileged system user and systemd service with memory limits on constrained boxes.
7. Disable unnecessary AMT/MPS public ports if not needed; leave only web access via nginx.
8. Create a device group such as `My PCs` and a short onboarding URL that points to the group invite/download page.

## Account/recovery pitfalls

MeshCentral recovery commands (`--createaccount`, `--resetaccount`, `--adminaccount`, `--hashpassword`) are intended to run while MeshCentral is stopped. Running them as root can leave NeDB files owned by root. After any local recovery command:

```bash
systemctl stop meshcentral
# run recovery command(s)
chown -R meshcentral:meshcentral /opt/meshcentral/meshcentral-data
systemctl start meshcentral
curl -skI https://<host>/ | head
systemctl is-active meshcentral nginx
```

If nginx returns 502 after recovery, check `journalctl -u meshcentral` for `EACCES` on `meshcentral-data/*.db`; fix ownership and restart.

## Verifying that a Windows PC registered

If CLI login is flaky or not yet working, the NeDB data can still show whether an agent registered. Redact secrets; only report device/group names.

Look for:
- `type == "mesh"` records: device groups;
- `type == "node"` records: registered PCs;
- events like `Added device <PC> to device group <group>` in `meshcentral-events.db`.

A registered device record proves the install reached the server. If the node is present but grey/offline in the web UI, tell the user to keep the agent running, approve Windows prompts, or reboot the PC so the service reconnects.

## Passive remote observation workflow

When the owner asks “what do you see on this PC?” prefer passive reads over interactive remote control.

1. Do the usual server preflight first (`free -m`, swap, disk, load, `systemctl is-active nginx meshcentral`) because the VPS may be memory-constrained.
2. Use MeshCentral CLI with a WebSocket URL, not the browser URL:
   ```bash
   node /opt/meshcentral/node_modules/meshcentral/meshctrl.js ListDevices \
     --url wss://<host> --loginuser <user> --loginpass "$PASS" --json
   ```
   `https://<host>` produces `Invalid url`; `wss://<host>` is the expected form.
3. To list visible open windows without taking over the PC:
   ```powershell
   $OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::UTF8
   Get-Process |
     Where-Object { $_.MainWindowTitle -and $_.MainWindowTitle.Trim().Length -gt 0 } |
     Sort-Object ProcessName |
     Select-Object ProcessName,MainWindowTitle |
     Format-List
   ```
   Run it through `meshctrl.js RunCommand --powershell --runasuser --reply`.
4. If the owner specifically wants a visual check, take a single screenshot via the logged-in user session, download it, inspect it, and do not click/type:
   ```powershell
   Add-Type -AssemblyName System.Windows.Forms
   Add-Type -AssemblyName System.Drawing
   $p=Join-Path $env:TEMP "hermes-screen.png"
   $b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds
   $bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height
   $g=[System.Drawing.Graphics]::FromImage($bmp)
   $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size)
   $bmp.Save($p,[System.Drawing.Imaging.ImageFormat]::Png)
   $g.Dispose(); $bmp.Dispose()
   Write-Output $p
   ```
5. For searches on a connected PC, do not browse visually or open Desktop first. Use the fastest narrow command path through MeshCentral Terminal/RunCommand: list window titles, running processes, target folders, or specific filename/text matches with focused PowerShell; force UTF-8 and short per-line output so Russian text is readable and not truncated. Use screenshots or interactive desktop control only after the command search is insufficient or the owner asks for a visual check.
6. Summarize only the open apps/active window or direct search result and avoid transcribing private message contents unless necessary for the user's request.
7. If a temporary operator account was created for CLI work, remove it before finalizing and verify: panel HTTP 200, `meshcentral` active, expected device still visible to the normal owner account.

## User-facing next step after install

Keep it short and practical:

1. Open the MeshCentral URL.
2. Log in.
3. Go to Devices → the device group.
4. Click the PC name.
5. Use Desktop / Terminal / Files.

Do not dump server logs, database IDs, key values, or long command output to the user.

## Security notes

- Never print or store MeshCentral passwords, invite tokens, enrollment keys, auth keys, or private key material in summaries or skill docs. Replace values with `[REDACTED]` if needed.
- If any one-time enrollment/auth key appears in chat or a script the user pasted, treat it as compromised and rotate/revoke it before future use.
- Do not send local `MEDIA:/tmp/...` paths as a substitute for an actual downloadable file. If a Windows installer/script must be delivered and `.ps1` delivery fails, package it as ZIP and verify delivery.

## Full-safety MeshCentral baseline for Александр's personal/consented PCs

Treat remote-PC access as privacy-sensitive even when Александр owns the PC. The default posture is **visible, consented, least-privilege observation/control** — never hidden administration.

Required server/domain settings for this setup:

- Self-registration is disabled (`newAccounts: false`).
- Guest device sharing is disabled (`guestdevicesharing: false`).
- User sessions have a short idle timeout and logout on idle.
- Password requirements are enforced for any future password changes: long password, mixed case, digit, symbol, old-password reuse ban.
- 2FA setup is a manual owner step: do not generate or store the owner's TOTP/2FA secret in automation. Tell Александр to enable 2FA in his MeshCentral profile after login; only he should see/save the QR/secret.
- Domain-wide `userconsentflags` must include all of these:
  - Desktop notify
  - Desktop prompt
  - Desktop privacy bar
  - Terminal notify
  - Terminal prompt
  - Files notify
  - Files prompt
- `desktopprivacybartext` must clearly tell the local user that a remote connection is active and what to do if it is unexpected.

Operational rules:

1. Do not create persistent extra admin/operator users for automation. If a temporary diagnostic account is unavoidable, remove it before finalizing and verify that only expected users remain.
2. Do not bypass the local-consent prompt to inspect screen, terminal, or files. If the agent cannot proceed because the PC owner has not accepted the prompt, ask them to approve it locally.
3. For Александр's personal PC, do not use silent unattended MeshCentral commands to inspect private data. Use passive reads only after the owner asks, and prefer window-title listing before screenshots.
4. Do not click, type, upload, download, execute commands, or change PC settings unless the owner explicitly asks for that action.
5. After any MeshCentral config/user recovery command, fix ownership of `meshcentral-data`, restart only MeshCentral, then verify HTTPS 200, `meshcentral` active, expected users, and expected device presence.
6. If MeshCentral returns nginx 502 after changes, check service readiness and NeDB ownership first; do not broaden nginx exposure or open extra ports as a workaround.

## Windows launcher lessons

For this class of task, avoid `.cmd` launchers with Russian text, complex quoting, or codepage-sensitive content. They can split text into broken commands and close immediately. If a Windows script is unavoidable, prefer a signed/simple installer or a `.ps1` inside a ZIP with logging and a visible pause, but MeshCentral agent delivery is the preferred default.
