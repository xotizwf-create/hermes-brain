---
name: connect-mcp
description: Use when the owner wants to connect, switch, remove, or REFRESH an MCP server for Hermes — e.g. pastes an MCP URL ("подключи этот mcp <url>", "добавь коннектор"), asks to switch connectors on/off ("включи albery", "выключи research mcp"), says "обнови" / "обнови коннектор" / "подтяни новые инструменты" (→ refresh, pick up new upstream tools), or list what's connected. Hermes writes the canonical mcp_servers entry into its own ~/.hermes/config.yaml via the bundled hermes_mcp.py, validates with `hermes mcp test`, applies live (auto-reload), and records the connector secret-free in connectors/registry.yaml.
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

## Golden rules (HARD — not suggestions)
0. **НИКОГДА не придумывай имя коннектора сам.** После `probe` ОБЯЗАТЕЛЬНО остановись и спроси
   владельца: «Как назовём этот сервер?». Не бери имя из URL, домена или названия сервера. Сохраняй
   (`add`) **только** после явного ответа владельца. (Менеджер сам превратит человеческое название,
   напр. «Простые поставки», в безопасный id `prostye_postavki` — тебе не нужно это делать руками.)
1. **Общение с владельцем — только по-русски и без техники.** Никаких команд, путей, id вида
   `mcp_*`, стек-трейсов, «exit code». Ошибку/предупреждение объясняй по-русски одной фразой + что
   делать. Менеджер уже печатает всё по-русски — относи его вывод как есть, не добавляй техническую
   обвязку. (Глобально: `profile/communication.md`.)
2. **The URL often contains the secret** (e.g. `https://host/mcp/<SECRET>`). Treat the whole URL as a
   secret: it lives only in `config.yaml` (mode 600) on the server. **Never** commit it to the brain,
   **never** echo it back in full — the manager redacts it. When constructing the URL from a
   server-side secret, read it on the server so it never transits chat or a workstation.
3. **Approval-gated.** Applying to `config.yaml` is an operational change: get the owner's "да" before
   `--apply`. Committing the registry entry follows `update-knowledge` (diff → approve).
4. **No raw secret in `connectors/registry.yaml`** — only a redacted `url_template` with a
   `{proj/<slug>/<service>/secret}` reference. `scripts/validate.py` must pass.

## Applying changes live — automatic (no `/reload-mcp` needed)
After any `--apply`, the change is picked up **automatically**: a small gateway patch
(`skills/connect-mcp/patches/mcp_autoreload_patch.py`) notices that `mcp_servers` changed and runs
the same reload `/reload-mcp` does — so the live session sees the new/removed tools on the owner's
**next message**. **Do not ask the owner to send `/reload-mcp`.** It stays as a manual fallback only
if the patch is somehow not applied (then `/reload-mcp`, or `--restart`). See "Auto-reload" below for
how it works and how to (re)install it.

## Connect a new MCP server — owner pastes a URL (the main flow)
Strict order. **Step 2 is a hard stop — do not skip it.**
1. **Probe** the URL (connect + list tools, nothing saved):
   ```bash
   python3 .../hermes_mcp.py probe --url "<url>"
   ```
   It prints `✅ Подключился. Инструментов: N`, the list, and ends with `Как назовём этот сервер?`.
   Relay that to the owner as-is. If it can't connect, relay the Russian error and stop.
2. **STOP and wait for the owner's name.** Do not invent one, do not derive it from the URL/domain.
   The owner's answer can be a human phrase ("Простые поставки") — pass it straight to `add`; the
   manager slugifies it to a safe id and tells you the final name.
3. Only after the owner answered, **save** (preview, then `--apply`):
   ```bash
   python3 .../hermes_mcp.py add "<owner's name>" --url "<url>"           # preview
   python3 .../hermes_mcp.py add "<owner's name>" --url "<url>" --apply   # backup + write {url, enabled: true}
   ```
4. **Готово — ничего больше делать не надо.** Tools are picked up automatically on the owner's next
   message (auto-reload patch). Do **not** ask for `/reload-mcp`. `hermes_mcp.py test <name>`
   re-validates the connection if you want to double-check.
5. **Remember it in the brain:**
   ```bash
   python3 .../hermes_mcp.py registry-snippet <name>
   ```
   Paste the secret-free block into `connectors/registry.yaml`, add the human label (`label:`) + `scope`,
   add `connectors/<name>.md` from `connectors/_template/SKILL.md`, commit via `update-knowledge`. The
   `label` lets the owner say "выключи Простые поставки" and you map it to the id.

## List the connected MCP servers — "покажи mcp / список серверов"
```bash
python3 .../hermes_mcp.py list      # 🟢 enabled / ⚪ disabled, names + redacted URLs
```
(`hermes mcp list` is the native equivalent.) Report names + on/off state to the owner; never print
the full secret URL.

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

## Auto-reload after a change (so the owner never types `/reload-mcp`)
A gateway patch makes Hermes refresh its own MCP session whenever `mcp_servers` changes:
- Source: `skills/connect-mcp/patches/mcp_autoreload_patch.py` — idempotent, anchor-based, never
  breaks `run.py` (temp + py_compile + atomic replace; SKIP if anchors change on a Hermes upgrade).
- Before each agent turn the gateway hashes the `mcp_servers` block; if it changed since last seen,
  it calls the gateway's own `_execute_mcp_reload(event)` (the `/reload-mcp` path) — which also
  refreshes cached agents so the **active** session gets the new tools on its next turn. Cheap on the
  no-change path (a stat). Fires once per change → no prompt-cache thrash.
- Self-heals across `hermes update` (which overwrites `run.py`) via the systemd drop-in
  `skills/connect-mcp/systemd/20-mcp-autoreload.conf` (`ExecStartPre` re-applies it on every start).

Install / re-install on prod:
```bash
mkdir -p /etc/systemd/system/hermes-gateway.service.d
cp /root/.hermes/agent-knowledge/skills/connect-mcp/systemd/20-mcp-autoreload.conf /etc/systemd/system/hermes-gateway.service.d/
systemctl daemon-reload
/usr/local/lib/hermes-agent/venv/bin/python /root/.hermes/agent-knowledge/skills/connect-mcp/patches/mcp_autoreload_patch.py
systemctl restart hermes-gateway
grep -c _connect_mcp_autoreload /usr/local/lib/hermes-agent/gateway/run.py   # 1 = applied
```

## Refresh tools — owner says "обнови" (and the daily timer)
When a connected MCP server gains new tools upstream, Hermes only sees them after it **re-discovers**
them, which happens on gateway start. So "refresh" = restart the gateway and re-read every server.

**Owner trigger:** when the owner says "обнови" / "обнови коннектор «Простые поставки»" / "подтяни
новые инструменты", run:
```bash
python3 .../hermes_mcp.py refresh --apply
```
Relay its Russian line as-is ("🔄 Обновляю инструменты — несколько секунд…") and **stop** — you're
done. New tools appear by themselves on the owner's next message.

**CRITICAL — never restart the gateway in-process from a chat turn.** `systemctl restart
hermes-gateway` tears down the cgroup that includes the turn answering the owner → the reply is cut
off ("Gateway shutting down — task interrupted") and looks like garbage. `refresh --apply` already
avoids this: it dispatches the restart to a **separate transient unit** (`systemd-run --on-active`,
see `detached_restart()`), delayed a few seconds so the reply flushes first. Do **not** "help" by
adding your own `systemctl restart`, `systemd-run`, or a post-restart check — the script handles it.

The same `refresh --apply` also runs automatically every day via a **systemd timer** (its own unit,
so it never races the in-process cron scheduler). Install it once on prod:
```bash
cp /root/.hermes/agent-knowledge/skills/connect-mcp/systemd/hermes-mcp-refresh.{service,timer} /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now hermes-mcp-refresh.timer
systemctl list-timers hermes-mcp-refresh.timer      # verify next run
```
Default schedule: `04:10 UTC` daily (just after the daily session reset, an idle window). Retune via
`OnCalendar` in the `.timer`. Do **not** drive this refresh from a `hermes cron` job — that scheduler
lives inside the gateway and would be killed by its own restart.

## Native CLI (alternative, interactive — for a human on the server)
The wrapper matches the native CLI, which you can use directly over SSH:
`hermes mcp list | add <name> --url <url> | remove <name> | test <name> | configure <name>`
(`configure` toggles *individual* tools of a server). The wrapper exists for the non-interactive
Telegram/cron path and to keep the brain registry in sync.

## From the PC (secondary path)
Server SSH creds live **locally in `c:\hermes-brain\.env`** (gitignored — IP / root user / password;
real values never leave that file). A small Paramiko script reading that `.env` can drive the same
manager on the server over SSH. The primary, intended flow is the owner pasting a URL to the Telegram
bot and Hermes running the manager on itself.

## Pointers
- Model & where things live: `connectors/mcp-servers.md`. What's connected now: `connectors/registry.yaml`.
- Canonical entry schema lives in Hermes itself: `/usr/local/lib/hermes-agent/skills/mcp/native-mcp/SKILL.md`.
- Secrets handling: `engineering/secrets-access.md` + skill `secure-access`.
