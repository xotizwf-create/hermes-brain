#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent patch: MCP client must never PERMANENTLY give up on a server.

Problem (2026-07-06, box 186): hermes 0.17's MCP client keeps one reconnect
budget for the whole process lifetime (`_MAX_RECONNECT_RETRIES = 5`) and NEVER
resets it after a successful reconnect. Every albery deploy restart (and, before
the albery-side ping fix, every failed 180s keepalive) burned attempts; after
the 5th the run-task returned and the server stayed DEAD until a full gateway
restart. Incident: 14:31:32 all 8 albery connectors "failed after 5
reconnection attempts, giving up" -> every agent lost its tools, crons
improvised via terminal, Bitrix agents refused basic actions for hours.

Fix (three anchored edits to tools/mcp_tool.py):
  1. Stamp a LOCAL `_conn_started` before each transport attempt (the class
     uses __slots__ — new instance attributes raise AttributeError; both the
     stamp and the check live in the same run() scope anyway).
  2. Before bleeding the budget: if the previous connection served >300s, this
     is a NEW outage -> reset retries/backoff (deploy restarts stop
     accumulating forever).
  3. The give-up branch no longer returns: it logs and switches to a slow
     retry every 120s (never giving up) so MCP recovers as soon as the app is
     back, without a manual gateway restart.
  4. `_MAX_INITIAL_CONNECT_RETRIES` 3 -> 8: a reboot where albery warms up
     slower than the gateway no longer permanently strips the gateway of MCP.

Runs as ExecStartPre of hermes-gateway.service (same contract as the media
rescue / provider error patches): py_compile-validated on a temp copy, swapped
in atomically, always exits 0 so gateway startup is never blocked. Idempotent
(MARKER guard). Also affects `hermes -z` one-shots (same installed tree).

Source of truth in git: hermes-brain scripts/hermes_mcp_resilience_patch.py
"""
import pathlib
import py_compile

BASE = pathlib.Path("/usr/local/lib/hermes-agent/tools/mcp_tool.py")
MARKER = "PATCH mcp-resilience"

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


def main() -> None:
    try:
        text = BASE.read_text(encoding="utf-8")
    except Exception as exc:
        print("mcp_resilience_patch: cannot read mcp_tool.py:", exc)
        return
    if MARKER in text:
        print("mcp_resilience_patch: already applied")
        return
    missing = [name for name, old in (
        ("stamp", OLD_STAMP), ("giveup", OLD_GIVEUP), ("initial", OLD_INITIAL),
    ) if old not in text]
    if missing:
        print("mcp_resilience_patch: anchor(s) not found, skipping (mcp_tool.py changed):",
              ", ".join(missing))
        return
    patched = (
        text.replace(OLD_STAMP, NEW_STAMP, 1)
            .replace(OLD_GIVEUP, NEW_GIVEUP, 1)
            .replace(OLD_INITIAL, NEW_INITIAL, 1)
    )
    if _safe_write(BASE, patched):
        print("mcp_resilience_patch: applied")


if __name__ == "__main__":
    main()
