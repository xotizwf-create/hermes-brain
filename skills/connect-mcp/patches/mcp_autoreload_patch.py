#!/usr/bin/env python3
"""Idempotent gateway patch: auto-reload MCP when config.yaml's mcp_servers changes.

After the owner adds/enables/disables an MCP server (the connect-mcp manager writes
~/.hermes/config.yaml), the running gateway must re-discover tools for the live session to see
them — normally that needs the owner to type /reload-mcp. This patch removes that step: before
each agent turn, the gateway checks whether the `mcp_servers` section changed since last seen and,
if so, calls the gateway's own `_execute_mcp_reload(event)` (the same path /reload-mcp uses, which
also refreshes cached agents so the active session picks up the new tools on its next turn).

Design (mirrors the existing self-healing patch convention on prod):
  * Idempotent — re-running is a no-op once patched.
  * Anchor-based; if the anchors are gone (new Hermes version), prints SKIP and leaves the file
    untouched. NEVER breaks the file: writes via temp + py_compile + atomic os.replace; on any
    error it restores nothing (original is untouched) and exits 0 so gateway start is never blocked.
  * Re-applied on every gateway start via the systemd drop-in
    skills/connect-mcp/systemd/20-mcp-autoreload.conf (ExecStartPre), because `hermes update`
    overwrites gateway/run.py.

Target file: /usr/local/lib/hermes-agent/gateway/run.py  (override with HERMES_GATEWAY_RUN).
Always exits 0.
"""
from __future__ import annotations

import datetime as dt
import os
import py_compile
import sys
import tempfile
from pathlib import Path

TARGET = Path(os.environ.get(
    "HERMES_GATEWAY_RUN", "/usr/local/lib/hermes-agent/gateway/run.py"))

MARKER = "_connect_mcp_autoreload"

# Method inserted into the gateway class (4-space indent, sits right before _execute_mcp_reload).
METHOD = '''    async def _connect_mcp_autoreload(self, event) -> None:
        """[connect-mcp] Auto-reload MCP tools when config.yaml's mcp_servers
        section changed since last seen, so a freshly added/removed/toggled
        server is picked up in the live session without the owner sending
        /reload-mcp. Cheap on the no-change path (stat, then hash a small block).
        """
        try:
            from hermes_cli.config import get_config_path
            import hashlib as _hashlib
            import yaml as _yaml
            path = get_config_path()
            st = os.stat(path)
            mtime_sig = (st.st_mtime_ns, st.st_size)
            if getattr(self, "_connect_mcp_mtime", None) == mtime_sig:
                return
            with open(path, encoding="utf-8") as _fh:
                data = _yaml.safe_load(_fh) or {}
            block = data.get("mcp_servers") or {}
            sig = _hashlib.sha256(
                _yaml.safe_dump(block, sort_keys=True, allow_unicode=True).encode("utf-8")
            ).hexdigest()
        except Exception:
            return
        prev = getattr(self, "_connect_mcp_sig", None)
        self._connect_mcp_mtime = mtime_sig
        if prev is None:
            self._connect_mcp_sig = sig
            return
        if sig == prev:
            return
        self._connect_mcp_sig = sig
        try:
            await self._execute_mcp_reload(event)
            logger.info("connect-mcp: mcp_servers changed -> auto-reloaded MCP tools")
        except Exception as _exc:
            logger.warning("connect-mcp: MCP auto-reload failed: %s", _exc)

'''

METHOD_ANCHOR = "    async def _execute_mcp_reload(self, event: MessageEvent) -> str:\n"

HOOK_ANCHOR = (
    "            # Run the agent\n"
    "            agent_result = await self._run_agent(\n"
)
HOOK = (
    "            # [connect-mcp] pick up mcp_servers changes before running the\n"
    "            # agent, so the live session sees newly added/removed tools.\n"
    "            try:\n"
    "                await self._connect_mcp_autoreload(event)\n"
    "            except Exception:\n"
    "                pass\n\n"
    + HOOK_ANCHOR
)


def main() -> int:
    if not TARGET.exists():
        print(f"[mcp-autoreload] target not found, skip: {TARGET}")
        return 0
    src = TARGET.read_text(encoding="utf-8")

    if MARKER in src:
        print("[mcp-autoreload] already applied")
        return 0

    if METHOD_ANCHOR not in src or HOOK_ANCHOR not in src:
        print("[mcp-autoreload] SKIP (anchors changed) — file left untouched")
        return 0
    if src.count(METHOD_ANCHOR) != 1 or src.count(HOOK_ANCHOR) != 1:
        print("[mcp-autoreload] SKIP (anchor not unique) — file left untouched")
        return 0

    patched = src.replace(METHOD_ANCHOR, METHOD + METHOD_ANCHOR, 1)
    patched = patched.replace(HOOK_ANCHOR, HOOK, 1)

    # Validate by compiling a temp copy; only swap in on success.
    try:
        fd, tmp = tempfile.mkstemp(dir=str(TARGET.parent), suffix=".tmp")
        os.close(fd)
        Path(tmp).write_text(patched, encoding="utf-8")
        py_compile.compile(tmp, doraise=True)
    except Exception as exc:
        print(f"[mcp-autoreload] compile failed, not applying: {exc}")
        try:
            os.unlink(tmp)
        except Exception:
            pass
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        bak = TARGET.with_suffix(TARGET.suffix + f".bak.{stamp}")
        if not bak.exists():
            bak.write_text(src, encoding="utf-8")
        os.replace(tmp, TARGET)
    except Exception as exc:
        print(f"[mcp-autoreload] swap failed: {exc}")
        try:
            os.unlink(tmp)
        except Exception:
            pass
        return 0

    print("[mcp-autoreload] applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
