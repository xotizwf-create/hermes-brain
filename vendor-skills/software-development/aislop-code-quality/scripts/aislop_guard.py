#!/usr/bin/env python3
"""Run aislop with safe defaults for Hermes code quality checks."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run scanaislop/aislop with agent-safe defaults.")
    p.add_argument("command", choices=("scan", "fix", "ci", "rules"), help="aislop command")
    p.add_argument("target", nargs="?", default=None, help="file or directory target")
    p.add_argument("--changes", action="store_true", help="scan/fix changed files from HEAD")
    p.add_argument("--staged", action="store_true", help="scan/fix staged files only")
    p.add_argument("--json", action="store_true", help="ask aislop for JSON output when supported")
    p.add_argument(
        "--allow-aggressive",
        action="store_true",
        help="allow aggressive fix mode; use only after explicit user approval",
    )
    return p.parse_args()


def base_cmd() -> list[str]:
    if os.name == "nt":
        cmd = shutil.which("aislop.cmd")
        if cmd:
            return [cmd]
    local = shutil.which("aislop")
    if local:
        return [local]
    return ["npx", "-y", "aislop@latest"]


def build_cmd(args: argparse.Namespace) -> list[str]:
    cmd = base_cmd() + [args.command]
    if args.target:
        cmd.append(args.target)
    if args.changes:
        cmd.append("--changes")
    if args.staged:
        cmd.append("--staged")
    if args.json and args.command in {"scan", "ci"}:
        cmd.append("--json")
    if args.allow_aggressive:
        if args.command != "fix":
            raise SystemExit("--allow-aggressive only applies to fix")
        cmd.append("-f")
    return cmd


def main() -> int:
    args = parse_args()
    if args.changes and args.staged:
        raise SystemExit("Use only one of --changes or --staged.")
    if args.command == "fix" and args.allow_aggressive:
        print(
            "AGGRESSIVE FIX ENABLED: confirm the user explicitly approved dependency/file deletion fixes.",
            file=sys.stderr,
        )

    cmd = build_cmd(args)
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
