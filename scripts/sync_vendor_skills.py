#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_vendor_skills.py — mirror Hermes' BUNDLED skill library (/root/.hermes/skills)
into the versioned brain under vendor-skills/, so our edits to bundled skills (e.g. the
cadastral one) and the whole library are backed up to GitHub and can't be lost when
Hermes is reinstalled/updated.

Run on the SERVER (that's where the bundled library lives). After it runs, commit
vendor-skills/ (or let the brain-dirty-watchdog auto-commit it). Re-run anytime to refresh.

Excludes noise: backup tarballs, the .archive templates, caches.
"""
import os, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = os.environ.get("HERMES_SKILLS_DIR", "/root/.hermes/skills")
DST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor-skills")
EXCLUDES = [".curator_backups", ".archive", "__pycache__", "*.pyc", "*.tar.gz", "*.gz", ".git"]


def main():
    if not os.path.isdir(SRC):
        sys.exit(f"sync_vendor_skills: source not found ({SRC}); run this on the server.")
    os.makedirs(DST, exist_ok=True)
    cmd = ["rsync", "-a", "--delete"] + [f"--exclude={e}" for e in EXCLUDES] + \
          [SRC.rstrip("/") + "/", DST.rstrip("/") + "/"]
    subprocess.run(cmd, check=True)
    files = sum(len(fs) for _, _, fs in os.walk(DST))
    skills = sum(1 for r, _, fs in os.walk(DST) for f in fs if f == "SKILL.md")
    print(f"mirrored {SRC} -> {DST}: {files} files, {skills} SKILL.md")


if __name__ == "__main__":
    main()
