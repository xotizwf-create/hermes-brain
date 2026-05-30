#!/usr/bin/env python3
"""Validate the brain: frontmatter on docs, project manifests, and no leaked secrets.

Usage:
    python scripts/validate.py        # report problems, exit 1 if any
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
DOC_TYPES = {"profile", "engineering", "project", "connector", "personal", "skill", "log", "schema"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# Heuristic secret patterns that must never be committed.
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"postgres(?:ql)?://[^\s:@]+:[^\s:@]+@"),  # db url with creds
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),            # github tokens
]
# Files that legitimately show placeholder secret shapes.
SECRET_ALLOWLIST = {"secrets-templates", "schema", "scripts", "vault"}
# Obvious placeholders — a match containing any of these is documentation, not a real secret.
PLACEHOLDERS = (
    "user:password", "user:pass", "username:password", "example", "changeme",
    "your-", "your_", "<", "xxx", "placeholder", "dbname", "host:5432", "@host",
    "getpass", "env[", "environ", "process.env", "${", "...", "= getpass",
)

errors: list[str] = []


def check_frontmatter(md: Path) -> None:
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{md.relative_to(ROOT)}: missing frontmatter")
        return
    block = text.split("---", 2)[1]
    data = yaml.safe_load(block) or {}
    for field in ("id", "type", "updated"):
        if field not in data:
            errors.append(f"{md.relative_to(ROOT)}: frontmatter missing '{field}'")
    if "id" in data and not ID_RE.match(str(data["id"])):
        errors.append(f"{md.relative_to(ROOT)}: bad id '{data['id']}'")
    if "type" in data and data["type"] not in DOC_TYPES:
        errors.append(f"{md.relative_to(ROOT)}: bad type '{data['type']}'")


def check_skill(md: Path) -> None:
    """Skills use the name/description frontmatter format (required by skill tooling)."""
    text = md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{md.relative_to(ROOT)}: skill missing frontmatter")
        return
    data = yaml.safe_load(text.split("---", 2)[1]) or {}
    for field in ("name", "description"):
        if field not in data:
            errors.append(f"{md.relative_to(ROOT)}: skill frontmatter missing '{field}'")


def check_secrets(f: Path) -> None:
    if any(part in SECRET_ALLOWLIST for part in f.relative_to(ROOT).parts):
        return
    text = f.read_text(encoding="utf-8", errors="ignore")
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        if m and not any(p in m.group(0).lower() for p in PLACEHOLDERS):
            errors.append(f"{f.relative_to(ROOT)}: possible secret leak ({pat.pattern[:30]}...)")
            break


def main() -> int:
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts or "archive" in md.parts:
            continue
        if md.name in {"README.md", "CLAUDE.md"}:
            continue  # landing / agent-instruction files, not knowledge docs
        if "skills" in md.parts:
            # Skills (and their bundled reference docs) use the skill format; only SKILL.md is checked.
            if md.name == "SKILL.md":
                check_skill(md)
            continue
        check_frontmatter(md)
    for f in ROOT.rglob("*"):
        if f.is_file() and ".git" not in f.parts and f.suffix in {".md", ".yaml", ".yml", ".py", ".sh"}:
            check_secrets(f)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print("  -", e)
        return 1
    print("brain valid: frontmatter ok, no secret leaks detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
