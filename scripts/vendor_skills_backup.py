#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vendor_skills_backup.py — daily auto-backup of Hermes' bundled skill library into the
versioned brain, so GitHub ALWAYS holds every skill (incl. our edits) and nothing is
lost on a Hermes reinstall/update.

Designed as a no-agent cron: silent on no-change; on a real change it validates, commits
ONLY vendor-skills/, pushes, and prints a one-line summary; on error it prints the error.

Flow: rsync /root/.hermes/skills -> agent-knowledge/vendor-skills (noise excluded) ->
if changed: validate.py must pass -> git add vendor-skills -> commit -> push.
"""
import os, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = os.environ.get("HERMES_SKILLS_DIR", "/root/.hermes/skills")
REPO = os.environ.get("BRAIN_REPO", "/root/.hermes/agent-knowledge")
DST = os.path.join(REPO, "vendor-skills")
EXCLUDES = [".curator_backups", ".archive", "__pycache__", "*.pyc", "*.tar.gz", "*.gz", ".git"]
COMMIT_NAME = "hermes-server"
COMMIT_EMAIL = "hermes-server@users.noreply.github.com"


def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def main():
    if not os.path.isdir(SRC):
        print(f"vendor-backup ERROR: source not found ({SRC})"); sys.exit(1)
    if not os.path.isdir(os.path.join(REPO, ".git")):
        print(f"vendor-backup ERROR: brain repo not found ({REPO})"); sys.exit(1)
    os.makedirs(DST, exist_ok=True)

    rsync = ["rsync", "-a", "--delete"] + [f"--exclude={e}" for e in EXCLUDES] + \
            [SRC.rstrip("/") + "/", DST.rstrip("/") + "/"]
    try:
        run(rsync)
    except subprocess.CalledProcessError as e:
        print(f"vendor-backup ERROR: rsync failed: {e.stderr[:300]}"); sys.exit(1)

    # anything changed under vendor-skills?
    status = run(["git", "status", "--porcelain", "vendor-skills"], cwd=REPO).stdout.strip()
    if not status:
        return  # silent: backup already current

    # validate before committing (mirror the watchdog's safety gate)
    val = run([sys.executable, "scripts/validate.py"], cwd=REPO, check=False)
    if val.returncode != 0:
        print("vendor-backup: skills changed but validate FAILED — not committing:\n"
              + (val.stdout or val.stderr)[:400]); sys.exit(1)

    changed = len([l for l in status.splitlines() if l.strip()])
    run(["git", "add", "vendor-skills"], cwd=REPO)
    msg = f"vendor-skills: auto-backup of bundled skills ({changed} path(s) changed)"
    commit = run(["git", "-c", f"user.name={COMMIT_NAME}", "-c", f"user.email={COMMIT_EMAIL}",
                  "commit", "-m", msg], cwd=REPO, check=False)
    if commit.returncode != 0:
        print(f"vendor-backup ERROR: commit failed: {(commit.stdout + commit.stderr)[:300]}"); sys.exit(1)
    push = run(["git", "push", "origin", "main"], cwd=REPO, check=False)
    if push.returncode != 0:
        print(f"vendor-backup: committed but PUSH failed: {(push.stdout + push.stderr)[:300]}"); sys.exit(1)

    print(f"🗂 Бэкап навыков: изменения в заводских навыках сохранены в GitHub ({changed} файл(ов)).")


if __name__ == "__main__":
    main()
