#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent patch: MCP must never silently disappear from agents.

Two related hermes 0.17 defects (box 186, incident 2026-07-06 — «агенты не
видят свои инструменты»):

1. GATEWAY: the MCP client keeps ONE reconnect budget for the whole process
   lifetime (`_MAX_RECONNECT_RETRIES = 5`) and never resets it after a
   successful reconnect; on the 6th connection loss the run-task returned and
   the server stayed DEAD until a gateway restart (14:31:32 — all 8 albery
   connectors "giving up", crons improvised via terminal for hours).

2. ONE-SHOT `hermes -z` (every Bitrix agent turn): `run_oneshot`/`_run_agent`
   bypasses `HermesCLI._init_agent()`, the only interactive-path caller of
   `wait_for_mcp_discovery()`. Background MCP discovery (spawned at CLI
   startup) RACED the agent's tool snapshot: idle box — discovery (~1s) wins;
   loaded box — snapshot wins and the turn runs with ZERO MCP tools, rc=0,
   the warning goes to a discarded stderr. Employees saw «в этом ходе у меня
   нет инструмента search_tasks» / «нет функций Google Sheets» from an agent
   whose connector serves 79 tools.

Fixes (anchored edits):
  mcp_tool.py:
  a. Stamp a LOCAL `_conn_started` before each transport attempt (the class
     uses __slots__ — new instance attributes raise AttributeError; both the
     stamp and the check live in the same run() scope anyway).
  b. Before bleeding the budget: if the previous connection served >300s, this
     is a NEW outage -> reset retries/backoff (deploy restarts stop
     accumulating forever).
  c. The give-up branch no longer returns: it logs and switches to a slow
     retry every 120s (never giving up) so MCP recovers as soon as the app is
     back, without a manual gateway restart.
  d. `_MAX_INITIAL_CONNECT_RETRIES` 3 -> 8: a reboot where albery warms up
     slower than the gateway no longer permanently strips the gateway of MCP.
  hermes_cli/oneshot.py:
  e. `_run_agent` joins background MCP discovery (bounded by
     `mcp_discovery_timeout`, config = 20s on this box) BEFORE building the
     agent, so every `-z` turn takes its tool snapshot AFTER the connectors
     are up. Idle cost ~0s (join returns the instant discovery completes).

Runs as ExecStartPre of hermes-gateway.service (same contract as the media
rescue / provider error patches): py_compile-validated on a temp copy, swapped
in atomically, always exits 0 so gateway startup is never blocked. Idempotent
(per-file MARKER guards). oneshot.py is read at every `hermes -z` launch, so
edit (e) needs no restarts at all.

Source of truth in git: hermes-brain scripts/hermes_mcp_resilience_patch.py
"""
import pathlib
import py_compile

MCP_TOOL = pathlib.Path("/usr/local/lib/hermes-agent/tools/mcp_tool.py")
ONESHOT = pathlib.Path("/usr/local/lib/hermes-agent/hermes_cli/oneshot.py")
MARKER = "PATCH mcp-resilience"
MARKER_ONESHOT = "PATCH mcp-resilience-oneshot"

OLD_STAMP = """        while True:
            try:
                if self._is_http():
                    await self._run_http(config)
                else:
"""

NEW_STAMP = """        while True:
            try:
                _conn_started = time.monotonic()  # PATCH mcp-resilience
                if self._is_http():
                    await self._run_http(config)
                else:
"""

OLD_GIVEUP = """                retries += 1
                if retries > _MAX_RECONNECT_RETRIES:
                    logger.warning(
                        "MCP server '%s' failed after %d reconnection attempts, "
                        "giving up: %s",
                        self.name, _MAX_RECONNECT_RETRIES, exc,
                    )
                    return
"""

NEW_GIVEUP = """                # PATCH mcp-resilience: a connection that served long enough means
                # the outage is NEW - refill the reconnect budget instead of bleeding
                # the process-lifetime counter one albery deploy at a time.
                if time.monotonic() - _conn_started > 300.0:
                    retries = 0
                    backoff = 1.0
                retries += 1
                if retries > _MAX_RECONNECT_RETRIES:
                    logger.warning(
                        "MCP server '%s' still down after %d fast reconnection "
                        "attempts; switching to slow retry every 120s "
                        "(never giving up): %s",
                        self.name, _MAX_RECONNECT_RETRIES, exc,
                    )
                    await asyncio.sleep(120)
                    if self._shutdown_event.is_set():
                        return
                    continue
"""

OLD_INITIAL = "_MAX_INITIAL_CONNECT_RETRIES = 3 # retries for the very first connection attempt"
NEW_INITIAL = "_MAX_INITIAL_CONNECT_RETRIES = 8 # PATCH mcp-resilience: tolerate slow albery warm-up at boot"

OLD_ONESHOT = """    from hermes_cli.tools_config import _get_platform_tools
    from run_agent import AIAgent

    cfg = load_config()
"""

NEW_ONESHOT = """    from hermes_cli.tools_config import _get_platform_tools
    from run_agent import AIAgent

    # PATCH mcp-resilience-oneshot: oneshot bypasses HermesCLI._init_agent(), the
    # only path that waited for background MCP discovery. Without this join the
    # agent's tool snapshot RACES connector setup and a loaded box produces turns
    # with ZERO MCP tools (rc=0, stderr discarded by callers). Bounded by
    # mcp_discovery_timeout from config; returns instantly once discovery is done.
    try:
        from hermes_cli.mcp_startup import wait_for_mcp_discovery

        wait_for_mcp_discovery()
    except Exception:
        pass

    cfg = load_config()
"""


def _safe_write(path: pathlib.Path, text: str) -> bool:
    tmp = pathlib.Path(str(path) + ".tmp.mcp_resilience")
    tmp.write_text(text, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except Exception as exc:
        print("mcp_resilience_patch: py_compile failed, leaving original:", exc)
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(path)
    return True


def _patch_file(path: pathlib.Path, marker: str, edits: list) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"mcp_resilience_patch: cannot read {path.name}:", exc)
        return
    if marker in text:
        print(f"mcp_resilience_patch: {path.name} already patched")
        return
    missing = [name for name, old, _ in edits if old not in text]
    if missing:
        print(f"mcp_resilience_patch: {path.name} anchor(s) not found, skipping "
              f"({path.name} changed): " + ", ".join(missing))
        return
    for _, old, new in edits:
        text = text.replace(old, new, 1)
    if _safe_write(path, text):
        print(f"mcp_resilience_patch: {path.name} patched")


def main() -> None:
    _patch_file(MCP_TOOL, MARKER, [
        ("stamp", OLD_STAMP, NEW_STAMP),
        ("giveup", OLD_GIVEUP, NEW_GIVEUP),
        ("initial", OLD_INITIAL, NEW_INITIAL),
    ])
    _patch_file(ONESHOT, MARKER_ONESHOT, [
        ("oneshot-wait", OLD_ONESHOT, NEW_ONESHOT),
    ])


if __name__ == "__main__":
    main()
