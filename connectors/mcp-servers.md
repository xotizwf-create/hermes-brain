---
id: mcp-servers
type: connector
tags: [mcp, connectors, config, switching, model]
updated: 2026-05-30
secret_refs: []
---

# MCP servers — how Hermes connects, remembers, and switches

The model behind the `connect-mcp` skill. Read once to understand *where* MCP connections live and
*why* the procedure is shaped this way.

## The picture
- Hermes (prod `217.198.12.236`, systemd `hermes-gateway`) is an MCP **client**. It reads servers
  from the `mcp_servers` section of `~/.hermes/config.yaml`, connects at startup, discovers tools,
  and injects them into every conversation as `mcp_<name>_<tool>`.
- The brain (this repo) is the **memory**: `connectors/registry.yaml` lists every connector
  (secret-free). The **live truth** is `config.yaml` on the server. `connect-mcp` keeps them in sync.
- Config changes are picked up **automatically**: a gateway patch
  (`skills/connect-mcp/patches/mcp_autoreload_patch.py`) detects a changed `mcp_servers` block and
  runs the gateway's own MCP reload before the next turn, so the live session gets the new tools with
  no `/reload-mcp` and no restart. `/reload-mcp` (manual) and `systemctl restart` remain fallbacks.

## Canonical entry schema (HTTP)
The authoritative reference ships inside Hermes:
`/usr/local/lib/hermes-agent/skills/mcp/native-mcp/SKILL.md`. HTTP transport:
```yaml
mcp_servers:
  <name>:
    url: "https://host/mcp/..."                 # required (secret may be in the path)
    headers: {Authorization: "Bearer ${ENV}"}   # optional — token referenced from ~/.hermes/.env
    enabled: true                               # native on/off switch
    timeout: 120                                # optional, per-call seconds
    connect_timeout: 60                         # optional
```
Stdio transport uses `command` + `args` (+ `env`) instead of `url`. An entry has either `url` or
`command`, never both.

## Where things live
| Thing | Location | Secret? |
|---|---|---|
| Live MCP entries (with secrets) | `~/.hermes/config.yaml` → `mcp_servers` (600, server only) | yes — never leaves the server |
| Bearer tokens (referenced) | `~/.hermes/.env` as `${ENV}` (600) | yes |
| Remembered list (secret-free) | `connectors/registry.yaml` (git) | no — references only |
| Per-connector usage rules | `connectors/<name>.md` (git) | no |
| Manager script | `skills/connect-mcp/scripts/hermes_mcp.py` → prod `/root/.hermes/agent-knowledge/...` | no |

## Two connector mechanisms (don't mix them)
1. **MCP servers** — HTTP/stdio entries in `config.yaml` `mcp_servers` (e.g. Albery). Connected and
   switched by `connect-mcp`. This is what "throw me a URL" means.
2. **OAuth MCP connectors** — Gmail / Calendar / Drive, authenticated **per session** via the MCP
   layer (`authenticate` → `complete_authentication`, or `hermes mcp login`), not via `config.yaml`.
   See `connectors/gmail.md`, `connectors/google-calendar.md`, `connectors/google-drive.md`.

## Switching = the native `enabled` flag
All `enabled` servers load at startup; their tools merge into one set. To "switch", flip
`enabled: true|false` (the manager's `enable`/`disable`). Disabled entries stay in the file but are
skipped by discovery and `hermes mcp list`. Use this to shrink the active toolset (saves the Codex
context budget, avoids tool-name clashes). Keep `enabled:` in `registry.yaml` matching reality.

## Adding a server safely (summary; full steps in skill `connect-mcp`)
1. Owner pastes the MCP URL in Telegram.
2. `hermes_mcp.py probe --url "<url>"` — connect + list tools WITHOUT saving, so Hermes can report
   "connected, N tools" and **ask what to name it**.
3. On the name: `hermes_mcp.py add <name> --url "<url>"` (dry-run) → confirm → `--apply` (backup →
   write canonical `{url, enabled: true}`).
4. Owner sends `/reload-mcp` to make it live (`hermes_mcp.py test <name>` re-validates).
5. `registry-snippet <name>` → paste the secret-free entry into `registry.yaml`, add
   `connectors/<name>.md`, commit via `update-knowledge`.

If a connection breaks the gateway: `hermes_mcp.py rollback` restores the last good config + restarts.

## Refreshing tools — owner says "обнови" (no LLM reasoning)
Hermes discovers each server's tools at gateway **startup**. To pick up tools a server added upstream,
the gateway must re-discover them → it must restart. When the owner says "обнови" / "подтяни новые
инструменты", run `hermes_mcp.py refresh --apply`, relay its Russian line, and stop.

**Why the restart is detached.** Restarting the gateway directly from a chat turn kills the cgroup
that includes the process answering the owner — the turn dies mid-reply ("Gateway shutting down —
task interrupted") and the answer is garbage. That was the old bug behind "обнови" producing weird
messages. `refresh --apply` now dispatches the restart to a **separate transient unit**
(`systemd-run --on-active`, a few seconds' delay) so the reply is delivered first and nothing is cut
off. The model must **never** add its own `systemctl restart` / `systemd-run` / post-restart check —
the script owns that.

The same command also runs daily via the **systemd timer** `hermes-mcp-refresh.timer`
(`skills/connect-mcp/systemd/`, default 04:10 UTC) — its own unit, so it never races the in-process
cron scheduler. `/reload-mcp` (in chat) is the on-demand, no-restart equivalent for a single config
change.

## Native CLI parity
`hermes mcp {list,add,remove,test,configure,login,catalog,install}` is the underlying CLI (used
directly by a human over SSH). `add` is interactive; the wrapper exists for the non-interactive
Telegram/cron path and to keep the brain registry in sync. `configure <name>` toggles a server's
*individual* tools (finer than enable/disable).
