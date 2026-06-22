---
name: secure-project-server-ops
description: "Safely operate user project servers using the secure per-project secrets store without leaking credentials."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [devops, ssh, secrets, production, project-servers]
---

# Secure Project Server Ops

Use this skill when the user asks to connect to a project server, inspect a deployed app, make a small production fix, check services/logs, or use credentials from the “secret/secure folder”.

## Core rules

1. **Never print secrets** — no passwords, tokens, connection strings, full `.env` values, or credential URLs in chat or logs.
2. **Use project slug discovery** — look for `/opt/hermes/secure/projects/<slug>/` first, then other documented secure stores if needed.
3. **Redact before output** — when showing environment structure, print only key names and `[REDACTED]` values.
4. **Avoid shell-sourcing unknown secret files** — parse `KEY=VALUE` lines in Python. Secret files may contain human notes or malformed lines that `source` would execute or error on.
5. **Prefer narrow changes** — for small production text/config fixes, patch only the exact file/strings and restart only the affected service.
6. **Verify after acting** — confirm the old value is gone, the new value exists, and the service/process is healthy.

## Safe connection pattern

Parse the project `.env` without echoing values:

```python
from pathlib import Path

vals = {}
for line in Path('/opt/hermes/secure/projects/<slug>/.env').read_text(errors='ignore').splitlines():
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    key, value = line.split('=', 1)
    vals[key.strip()] = value.strip().strip('"\'')
```

Then pass credentials through the environment, not through visible command arguments. If `sshpass` is used, set `SSHPASS` in the subprocess environment. If a Python SSH library is available and appropriate, keep the password in memory only.

## Discovery checklist on the server

Run read-only checks first:

```bash
hostname
systemctl list-units --type=service --all --no-pager | grep -Ei '<project>|bot|api|node|python|pm2' || true
ps -eo pid,comm,args --sort=pid | grep -Ei '<project>|bot|api|node|python|pm2' | grep -v grep || true
docker ps --format '{{.Names}} {{.Image}} {{.Status}}' 2>/dev/null || true
```

Find the app directory via services/process args before editing. Common locations are `/var/www/<app>`, `/opt/<app>`, and `/srv/<app>`.

## Network/VPN reachability triage

When an external resource returns 403/451, times out, or behaves differently from the user's local browser, do not assume the resource is down. First check whether the server's VPN route is the cause — either because the resource requires VPN egress, or because it blocks VPN egress and needs the direct Russian IP.

Read-only checks:

```bash
ip -br addr
ip rule show
ip route show default
curl -s --max-time 15 https://ifconfig.me || true
getent ahostsv4 <domain> | awk 'NR<=5{print $1}'
ip route get <resolved-ip>
curl -I --max-time 20 -A 'Mozilla/5.0' https://<domain>/
curl -I --max-time 20 --interface eth0 -A 'Mozilla/5.0' https://<domain>/
```

If the default route fails but `--interface eth0` succeeds, do not disable the VPN. Add a narrow destination bypass rule in the VPN policy-routing script and verify: (1) the rule is idempotent and not duplicated, (2) the resource opens, (3) the default external IP is still the VPN. For the Albery server, the concrete runbook is in `/root/.hermes/agent-knowledge/projects/albery/vpn-gateway.md`; hh.ru is permanently bypassed via the direct RU IP because it rejects the Estonia VPN egress.

## Per-destination VPN bypass without touching the VPN

Use this when the owner explicitly says a site must be reached from the server's original IP while the VPN must stay enabled. Do not stop, restart, or reconfigure the VPN unless explicitly approved. Prefer a narrow route/rule exception for the specific destination.

1. First do read-only discovery:
   ```bash
   ip -br addr
   ip route show default
   ip rule show
   ip route show table 200 2>/dev/null || true
   getent ahostsv4 <host> | awk '{print $1}' | sort -u
   curl -s --max-time 15 https://ifconfig.me || true
   ```
2. Verify the direct/original interface works without changing routes:
   ```bash
   curl -sS -I --max-time 20 --interface <main-iface> -A 'Mozilla/5.0' https://<host>/
   curl -s --max-time 15 --interface <main-iface> https://ifconfig.me
   ```
3. If a VPN catch-all `ip rule` sends ordinary traffic into a VPN table, add a higher-priority destination exception to the main table for only the resolved host/network:
   ```bash
   ip rule add priority 950 to <dest-ip-or-cidr> lookup main
   ip route get <dest-ip>
   ```
   Keep this as narrow as practical. For DDoS/CDN-fronted sites, the resolved address may be a CDN netblock; document the exact exception and verify after DNS changes.
4. Verify both sides:
   - the target host now returns a normal response and source IP/cookies show the original server IP;
   - default external IP is still the VPN IP, proving the VPN remains active.
   - if `curl -I` is inconclusive or a browser-facing WAF/block page is suspected, open the site with the browser tool after the route exception and read the block page fields (many Russian retail/WAF pages print the detected IP). This confirms whether the request is really leaving via the original server IP.
5. If the target still blocks after the page itself shows the original server IP, stop network-route tuning: the site is likely rejecting the server/datacenter ASN or IP reputation, not the VPN egress. Report that practical conclusion and suggest a residential/mobile/local-browser route rather than adding broader bypasses.
6. Tell the owner whether the rule is temporary. `ip rule add` is normally not persistent across reboot/network/VPN restart; make it persistent only after explicit approval.

## Simple remote PC access / MeshCentral pattern

Use this when the owner wants the agent/operator to connect to arbitrary PCs with minimal user friction: "send a link → install an agent → PC appears". Prefer a self-hosted remote-management agent such as MeshCentral over custom Windows PowerShell/`.cmd` connector stacks with Tailscale auth keys, OpenSSH, local users, watchdogs, and firewall rules.

Operational checklist:

1. Run the server preflight first and protect live services; small production VPS boxes are memory-constrained.
2. Put MeshCentral behind nginx/HTTPS with the service bound to localhost; disable unnecessary public AMT/MPS ports unless explicitly needed.
3. Preserve existing routes such as Hermes Vault paths when reusing a domain/vhost.
4. Create a device group and a short onboarding link for Windows agent install.
5. After local MeshCentral recovery commands (`--createaccount`, `--resetaccount`, `--adminaccount`, `--hashpassword`), fix ownership of `meshcentral-data` back to the service user before restarting; root-owned NeDB files cause nginx 502 / MeshCentral `EACCES` loops.
6. Verify registration by the web UI or, if needed, by redacted NeDB/event inspection for `mesh` and `node` records. Tell the user only the practical result: device name, online/offline state, and what to click next.
7. If the owner asks what is open on the remote PC, prefer passive observation first: use MeshCentral `RunCommand` to list visible window titles, and only then take a single screenshot if needed. Do not click, type, or move the mouse unless the owner explicitly asks for control.
8. For MeshCentral CLI automation, remember `meshctrl.js --url` requires `wss://...`, not `https://...`. Use a temporary operator account only when needed, remove it afterward, and verify the normal owner account/device access still works.

User-facing guidance after install should be short: open the panel, go to Devices → group, click the PC, then use Desktop / Terminal / Files. Do not dump server logs, IDs, screenshots, or window text beyond what the owner asked to know.

Detailed runbook: `references/meshcentral-remote-pc-access.md`.

## External messaging bridge MVPs

Use this when adding a lightweight non-native messaging platform bridge (for example VK) without modifying the existing Hermes gateway. Prefer a separate localhost-bound service behind nginx, strict user allowlists for personal MVPs, root-only secret config, immediate Callback acknowledgements with asynchronous Hermes processing, and explicit cleanup of old platform-bot leftovers. For VK specifically, see `references/vk-hermes-bridge-mvp.md` for the Callback API, Long Poll, old-keyboard, and `hermes chat --continue <name>` first-run pitfalls.

### Remote LLM Telegram bridge silence / limit-burn triage

When a Telegram bot bridge accepts prompts, spends Claude/OpenAI/provider quota, but appears to “do nothing”, do not stop at process health. Inspect whether the bridge uses the wrong model/effort for its job, only sends `typing` until final completion, hides provider errors/rate limits in local logs, or lacks per-request spend/time guardrails. Also check the transport layer: for long-poll Telegram bots, `pm2`/systemd can show `online` while the HTTP poll is hung and the update offset no longer advances. Compare Telegram `getWebhookInfo.pending_update_count` with the bridge state offset, then add a poll/request timeout and network/JSON error logging before restarting only that bridge. Fix for visible behavior: role-appropriate model defaults (do **not** downgrade a coding-agent from Opus just to save quota; reduce effort and add guardrails/preflight instead), streaming/progress messages, clear rate-limit messages, separate wording for real provider/account limits vs local per-response budget caps, per-request limits, early session/context persistence, no automatic conversation reset based only on cumulative cached-token counters, restart only the affected bridge, verify process/logs, queue drain, and offset advance, and persist PM2 state if applicable. Detailed checklists: `references/remote-llm-telegram-bridge-triage.md`, `references/telegram-long-poll-bridge-hang.md`, and `references/claude-code-telegram-bridge.md` for Claude Code-specific stream parsing, false limit detection, and two-step `/switch` state handling.

## Remote project env secret retrieval pattern

Use this when the local secure project file contains only connection credentials, while the operational secret (MCP path token, webhook secret, app token) lives in the remote app's `.env`.

### MCP/API side-effect timeout triage

When an MCP tool that creates external side effects times out (for example a project tool that creates Bitrix tasks), do not retry blindly. First verify whether the side effect happened using the project’s read-only search/list tools or DB-backed status: check the pending queue, search for created external objects by title/date/id, and only then decide whether retry is safe. If the side effect did not happen and the queue remains open, inspect the production service logs around the timestamp; MCP client timeouts often hide the real internal exception. Keep output redacted. For Albery Zoom → Bitrix dispatch, see `references/albery-bitrix-rest-dispatch.md`.

### Albery Google Sheets quality guard

When the Albery Bitrix AI agent creates or edits a Google Sheet and the owner says the result is “плохой”, do not stop at checking that a link was created. Read the bot session, locate the generated sheet, inspect the server-side Sheets write path, and verify formulas in the actual spreadsheet. Russian-locale spreadsheets can require semicolon formula separators; English comma-separated examples may create broken formulas. Fix the generated sheet if possible, then harden the tool so it locale-normalizes formulas and fails loudly if post-write formula verification finds errors. Detailed runbook: `references/albery-google-sheets-formula-locale.md`.

**Do not assume credential key names.** Secure project env files may use variants like `IP`/`USER`/`PASSWORD` instead of `Host_IP`/`Host_User`/`Host_Password`. If a connection fails or the schema is unknown, inspect and report only the available key names, never values, then map the correct keys in memory for the command.

### Remote Hermes cron inspection

When the owner asks to inspect Hermes Agent automations on a project server, keep it read-only: preflight resources, find `hermes-gateway.service`/Hermes home, run `hermes cron list`, read the cron jobs JSON for structured fields, redact prompts/scripts, and list system cron separately as non-Hermes. See `references/hermes-cron-remote-inspection.md`.

### Remote Hermes `openai-codex` auth repair

When a remote Hermes gateway reports provider authentication failure for `openai-codex`, distinguish three cases before changing anything:

1. Inspect only auth shape/key presence, not token values: `providers.openai-codex.tokens.access_token`, `refresh_token`, and `credential_pool.openai-codex` entries. Hermes may fail with “missing access_token” if only `id_token` remains in `providers`, even if old metadata exists.
2. Check logs for the concrete cause: `token_expired`, `token_invalidated`, `refresh_token_reused`, or `missing access_token`. Also test the model from the remote Hermes home with a one-line `PING-OK` prompt before restarting the gateway.
3. If the real model ping returns an OpenAI/Cloudflare 403 or an HTML “Unable to load site” page from a Russian/server IP, verify routing before blaming the OAuth token. On Albery specifically run `/usr/local/sbin/vpn-healthcheck.sh`: the AmneziaWG service can be active while policy-routing rules are missing, causing outbound traffic to bypass the VPN. If healthcheck shows direct outbound IP / OpenAI 403 and `/root/vpn_apply.sh` exists, apply the existing routing script, re-run healthcheck, then clear stale `last_status`/`exhausted` auth markers and retry `PING-OK`.
4. Prefer an independent re-auth/device-code session for that remote agent. Do **not** casually copy the same OAuth refresh token used by another live agent: two processes sharing one refresh token can invalidate each other. If an emergency temporary restore is explicitly needed, back up `/root/.hermes/auth.json`, update only the `openai-codex` provider/pool fields, clear stale error markers, verify with a real model ping, restart only `hermes-gateway.service`, then check fresh logs for auth errors. Plan a later clean re-auth to give the remote agent its own session.
4. If the owner later asks to remove a shared OAuth account from the remote agent, remove it from **all** places, not just active `auth.json`: scrub `openai-codex` provider/pool entries from `auth.json` and every `auth.json*` backup, remove/disable Codex CLI OAuth files such as `~/.codex/auth.json*`, restart the gateway, and verify that no auth file still contains `openai-codex`, `access_token`, or `refresh_token`. Do not leave a backup containing the shared account.

### Remote Hermes Telegram routing / notification-chat migration

When the owner asks to make a project Hermes bot behave like the main assistant — dialog in the normal chat, but service notifications, approvals, cron outputs, and background prompts in a dedicated notifications chat/topic — treat it as a remote production config migration. Do server preflight first, discover the active Hermes home/profile from systemd rather than assuming a profile name, back up the active config, edit only the routing/noise-control keys needed, restart only that Hermes gateway service, and verify with real Telegram delivery tests. If the documented SSH `.env` or secure credential file is absent, inspect candidate files for key names only and then stop for the credential location; do not guess access or claim the agent was reconfigured. Before pinning cron jobs or approvals to an explicit chat ID, prove that the active bot can access the destination with `getChat` and a harmless `sendMessage`; if it cannot, revert explicit delivery targets to the previous safe route and ask the owner to add/mention the correct bot. Detailed checklist and pitfalls: `references/hermes-gateway-telegram-routing.md`. For Albery specifically, also use `references/albery-hermes-gateway-routing.md` before touching the Telegram bot/gateway so you do not operate on the wrong host/profile.

1. Parse `/opt/hermes/secure/projects/<slug>/.env` locally without printing values.
2. Run a read-only preflight on the remote host before doing any server work; if the host is constrained, keep the operation to light reads and config writes only.
3. Connect with secrets passed through environment variables (for example `SSHPASS`), never command arguments.
4. On the remote host, parse the app `.env` with Python and print only key names / booleans like `url_built=yes`; never print the secret value or full URL.
5. Prefer returning the constructed secret URL directly over stdout to the parent process and immediately consuming it in memory. If a temporary file is unavoidable on the remote host, delete it before finishing and verify it is gone.
6. After using the secret to configure a local tool (for example an MCP server), verify with the tool's safe test/list commands using redacted output.

See `references/remote-env-mcp-secret-retrieval.md` for a concrete redacted MCP connection recipe.

## Production text fix workflow

1. Locate the exact source string, excluding bulky/generated directories where possible:
   ```bash
   grep -RIn --exclude-dir=node_modules --exclude-dir=.git "old text or unique username" /path/to/app
   ```
2. If matches include generated bundles and source files, patch the source/runtime file that the running service uses.
3. Replace all intentional occurrences of the user-facing message, not just the first occurrence.
4. Re-run search:
   - old text should be absent from the relevant runtime source
   - new text should be present in the expected count
5. Restart only the affected service, for example a bot service rather than the whole app stack.
6. Verify status/process after restart.

## Low-downtime Node/Vite release workflow

Use this for production-sensitive Node/Vite apps where the user explicitly requires the site/API/bot to remain available.

1. **Build and test away from the live working directory first.** Use a fresh local clone or a server-side release directory, never edit `/var/www/.../app` in place until checks are clean.
2. **Run local gates before upload:** typecheck/lint, the full relevant test suite, and `npm run build`. If unrelated pre-existing failures appear, fix narrow obvious regressions only when they block a clean deployment gate.
3. **Upload to a timestamped release directory** such as `/var/www/<app>/releases/<timestamp>` and copy the existing `.env.local`/runtime secrets into that release without printing values.
4. **Avoid building on small production hosts if memory is tight.** If server-side `vite build`/bundle work is killed (for example exit 137/OOM), keep the live app untouched, build `dist/` locally from the already-tested commit, archive it with the release, and on the server only run `npm ci`, typecheck/targeted tests, and `test -f dist/index.html`.
5. **Do not switch while management access is unstable.** If SSH/systemctl checks start timing out, stop at the safe point; do not rename/symlink the live app or restart services until the server responds reliably.
6. **Make switching atomic and reversible:** keep a timestamped backup of the previous live app path or symlink target, switch to the prepared release, restart only the affected systemd services, and have a rollback command ready before restarting.
7. **Bound release retention:** keep the active release, the immediately previous rollback release, and only a small bounded history (normally the last 3–5 timestamped releases). After a successful deploy and verification, prune older releases so `/releases` does not grow forever. Before pruning, resolve the active symlink/current app path and explicitly exclude it plus the rollback target; delete only older timestamped release directories, never the live path.
8. **Verify after switch:** `systemctl is-active` for API and bot services, local HTTP health check through nginx, a process/log smoke check, and an MCP/CLI smoke test that does not reveal secrets or token values.

## Communication style

For the user, report practical capability and result, not secret paths or credential details. Good summary:

- “Подключился к серверу”
- “Нашёл работающий бот”
- “Текст встречается в N местах”
- “Могу/исправил безопасно: заменил, перезапустил только бота, проверил что поднялся”

Avoid dumping commands, IPs, usernames, `.env` content, or unrelated grep noise unless the user explicitly asks for technical detail.

## References

- `references/vk-hermes-bridge-voice-attachments.md` — VK Hermes bridge pitfall/fix for outbound TTS MP3 failing as `file is undefined`; convert to OGG/Opus and upload as `audio_message`, then verify through `send_vk_attachment()`.

- `references/gov-exams-app-liteexams.md` — concrete non-secret notes from the Gov Exams / LiteExams bot inspection
- `references/liteexams-payment-checks.md` — read-only Moscow-time workflow for checking LiteExams YooKassa subscription payments without leaking secrets
- `references/hermes-gateway-telegram-routing.md` — checklist for migrating a remote Hermes Telegram bot to a split dialog vs notifications/approvals chat model
