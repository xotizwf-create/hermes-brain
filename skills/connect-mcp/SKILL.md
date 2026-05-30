---
name: connect-mcp
description: Use when the owner wants to connect, switch, or remove an MCP server for Hermes — e.g. pastes an MCP URL ("подключи этот mcp <url>", "добавь коннектор"), asks to switch connectors on/off ("включи albery", "выключи research mcp"), or list what's connected. Hermes writes the canonical mcp_servers entry into its own ~/.hermes/config.yaml via the bundled hermes_mcp.py, validates with `hermes mcp test`, applies live with /reload-mcp, and records the connector secret-free in connectors/registry.yaml.
---

# Skill: connect-mcp

Connect MCP servers to Hermes safely from chat. The owner throws a URL → Hermes remembers it →
connects → and switches connectors on/off. Hermes reads MCP servers from the `mcp_servers` section
of `~/.hermes/config.yaml` and discovers their tools.

**Why a wrapper instead of `hermes mcp add`:** the native `hermes mcp add` is *interactive* (it
prompts "Enable all tools? [Y/n/select]" and, for header auth, asks for the token on a TTY), so it
can't be driven from a Telegram tool call. The bundled manager writes the **same canonical schema**
non-interactively:
`skills/connect-mcp/scripts/hermes_mcp.py` → on prod `/root/.hermes/agent-knowledge/skills/connect-mcp/scripts/hermes_mcp.py`.
Default is **dry-run**; nothing is written until `--apply`. Every write backs up `config.yaml` first;
`rollback` restores the latest backup.

## Golden rules (safety)
1. **The URL often contains the secret** (e.g. `https://host/mcp/<SECRET>`). Treat the whole URL as a
   secret: it lives only in `config.yaml` (mode 600) on the server. **Never** commit it to the brain,
   **never** echo it back in full — the manager redacts it. When constructing the URL from a
   server-side secret, read it on the server (e.g. from `/var/www/<app>/.env`) so it never transits
   chat or a workstation.
2. **Approval-gated.** Applying to `config.yaml` is an operational change: show the dry-run, get the
   owner's "да", then `--apply`. Committing the registry entry follows `update-knowledge` (diff → approve).
3. **No raw secret in `connectors/registry.yaml`** — only a redacted `url_template` with a
   `{proj/<slug>/<service>/secret}` reference. `scripts/validate.py` must pass.

## Applying changes live — `/reload-mcp` (no restart)
After any `--apply`, make Hermes pick up the change by sending **`/reload-mcp`** in the Telegram chat:
the gateway reconnects servers and reports the new tool count, **without restarting and without
losing the session**. The heavy fallback is `--restart` (systemctl restart hermes-gateway + `/reset`),
only needed if `/reload-mcp` misbehaves.

## Connect a new MCP server — "подключи этот mcp: <url>"
1. Pick a short kebab-case `name` (used as the tool prefix `mcp_<name>_*`). Ask if unclear.
2. Dry-run (shows the exact entry, secret redacted):
   ```bash
   python3 .../hermes_mcp.py add <name> --url "<url>"
   ```
3. Owner confirms → apply:
   ```bash
   python3 .../hermes_mcp.py add <name> --url "<url>" --apply
   ```
   (backs up config, writes `{url, enabled: true}`).
4. Validate the connection + tool discovery:
   ```bash
   python3 .../hermes_mcp.py test <name>      # = hermes mcp test <name>
   ```
5. Apply live: tell the owner to send **`/reload-mcp`** in Telegram.
6. **Remember it in the brain:**
   ```bash
   python3 .../hermes_mcp.py registry-snippet <name>
   ```
   Paste the secret-free block into `connectors/registry.yaml`, fill `scope`, add `connectors/<name>.md`
   from `connectors/_template/SKILL.md`, commit via `update-knowledge`.

### Auth variants
- **Secret in the URL** (Albery-style `/mcp/<secret>`, auth none): just pass `--url`. Most common.
- **Bearer token**: `--url <base> --bearer-env MYTOKEN` writes `headers: {Authorization: "Bearer ${MYTOKEN}"}`
  and references the env var — put the real value in `~/.hermes/.env` as `MYTOKEN=...` (600), never in
  the brain. (This mirrors what native `hermes mcp add --auth header` does.)
- **Custom headers**: `--header "X-Api-Key: ${MYKEY}"` (repeatable).
- **OAuth** servers use a different mechanism (`hermes mcp login <name>` / per-session auth) — see
  `connectors/gmail.md` etc.; not handled by this manager.

## Switch connectors — enable / disable (native `enabled` flag)
"Switching" = the native `enabled: true|false` field on the entry. Disabled servers stay in the file
but Hermes' discovery and `hermes mcp list` skip them — fewer active tools = less context burned, no
tool-name clashes.
```bash
python3 .../hermes_mcp.py disable <name> --apply    # then /reload-mcp
python3 .../hermes_mcp.py enable  <name> --apply    # then /reload-mcp
python3 .../hermes_mcp.py list                      # 🟢 enabled / ⚪ disabled
```
Keep `enabled:` in `connectors/registry.yaml` in sync when you commit.

## Remove / rollback
```bash
python3 .../hermes_mcp.py remove <name> --apply      # backup kept
python3 .../hermes_mcp.py rollback                   # restore last config + restart gateway
```
Roll back first if a bad connector breaks the gateway (won't start / errors every message), then
debug the URL/auth offline.

## Native CLI (alternative, interactive — for a human on the server)
The wrapper matches the native CLI, which you can use directly over SSH:
`hermes mcp list | add <name> --url <url> | remove <name> | test <name> | configure <name>`
(`configure` toggles *individual* tools of a server). The wrapper exists for the non-interactive
Telegram/cron path and to keep the brain registry in sync.

## From the PC (secondary path)
Server SSH creds live **locally in `c:\hermes-brain\.env`** (gitignored: IP / root / password) — the
file `tmp_ssh.py` pattern (Paramiko) drives the same script on the server. The primary, intended flow
is the owner pasting a URL to the Telegram bot and Hermes running the manager on itself.

## Pointers
- Model & where things live: `connectors/mcp-servers.md`. What's connected now: `connectors/registry.yaml`.
- Canonical entry schema lives in Hermes itself: `/usr/local/lib/hermes-agent/skills/mcp/native-mcp/SKILL.md`.
- Secrets handling: `engineering/secrets-access.md` + skill `secure-access`.
