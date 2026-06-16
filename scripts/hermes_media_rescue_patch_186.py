#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent media-rescue patch for the Albery Hermes on 186 (base.py variant).

Problem (2026-06-16): the Albery gateway runs as root, so the agent writes
deliverables to /root/<file>.pdf. /root is a delivery denylist prefix, and 186's
native recency fallback explicitly refuses denied-prefix paths
(``if window > 0 and not _path_under_denied_prefix(resolved): ...``), so
validate_media_delivery_path() returns None and the attachment is dropped with a
log-only warning — the agent keeps telling the owner the file was sent.

217's hermes_media_rescue_patch.py does NOT fit here: 186 is a different Hermes
version (no _media_delivery_strict_mode / _path_under_denied_prefix-based strict
branch the 217 anchors expect). This patch targets 186's structure and uses only
helpers that exist there (_HERMES_HOME, _MEDIA_DELIVERY_DENIED_HOME_SUBPATHS,
_path_is_within, _file_is_recently_produced).

Fix: when the path is rejected only because of its LOCATION (e.g. under /root),
but the file (a) is not under a credential/system location, (b) was produced
recently, and (c) is not huge — copy it into the allowlisted outbox
(~/.hermes/outbox) and deliver from there. Credential/system paths stay blocked.

Runs as ExecStartPre of hermes-gateway.service: every write is py_compile-checked
on a temp copy and swapped atomically; always exits 0 so startup is never blocked;
if the anchors ever change (new Hermes version) it prints SKIP and leaves base.py
untouched.

Source of truth in git: hermes-brain scripts/hermes_media_rescue_patch_186.py
Deployed on 186 as /root/.hermes/patches/media_rescue_patch.py
"""
import pathlib
import py_compile

BASE = pathlib.Path("/usr/local/lib/hermes-agent/gateway/platforms/base.py")

MARKER = "_rescue_media_path_to_outbox"

# Module-level validate fn on 186 (its docstring is unique vs the staticmethod variant).
HELPERS_ANCHOR = '''def validate_media_delivery_path(path: str) -> Optional[str]:
    """Return a safe absolute file path for native media delivery, else None.
'''

HELPERS = '''_MEDIA_RESCUE_MAX_BYTES = 50 * 1024 * 1024
_MEDIA_RESCUE_WINDOW_SECONDS = 1800.0


def _media_rescue_sensitive(resolved: Path) -> bool:
    """True if ``resolved`` may hold credentials/system data: never rescue."""
    home = Path(os.path.expanduser("~"))
    for sub in _MEDIA_DELIVERY_DENIED_HOME_SUBPATHS:
        try:
            denied = (home / sub).resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            continue
        if _path_is_within(resolved, denied):
            return True
    try:
        if _path_is_within(resolved, Path(_HERMES_HOME).resolve(strict=False)):
            return True
    except (OSError, RuntimeError, ValueError):
        pass
    for prefix in ("/etc", "/proc", "/sys", "/dev", "/boot", "/var",
                   "/usr", "/bin", "/sbin", "/lib", "/lib64", "/run"):
        if _path_is_within(resolved, Path(prefix)):
            return True
    return False


def _rescue_media_path_to_outbox(resolved: Path) -> Optional[str]:
    """Copy a freshly produced non-credential file into the outbox allowlist.

    Local patch (2026-06-16, Albery/186). Files the agent created under /root
    (the gateway runs as root) used to be dropped silently. Recency is the
    session-trust signal; credential and system locations stay rejected.
    """
    import shutil

    try:
        if _media_rescue_sensitive(resolved):
            return None
        if not _file_is_recently_produced(resolved, _MEDIA_RESCUE_WINDOW_SECONDS):
            return None
        if resolved.stat().st_size > _MEDIA_RESCUE_MAX_BYTES:
            return None
        outbox = Path(_HERMES_HOME) / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        target = outbox / resolved.name
        if target.exists() and not target.samefile(resolved):
            target = outbox / ("%d_%s" % (int(time.time()), resolved.name))
        shutil.copy2(str(resolved), str(target))
        logger.warning("Rescued MEDIA path outside allowlist: %s -> %s", resolved, target)
        return str(target)
    except Exception as exc:
        logger.warning("MEDIA rescue failed for %s: %s", resolved, exc)
        return None


'''

# 186's validate fn ends with this recency block; rescue replaces the final return.
STRICT_OLD = '''    window = _media_delivery_recency_seconds()
    if window > 0 and not _path_under_denied_prefix(resolved):
        if _file_is_recently_produced(resolved, window):
            return str(resolved)

    return None
'''

STRICT_NEW = '''    window = _media_delivery_recency_seconds()
    if window > 0 and not _path_under_denied_prefix(resolved):
        if _file_is_recently_produced(resolved, window):
            return str(resolved)

    return _rescue_media_path_to_outbox(resolved)
'''


def _safe_write(path: pathlib.Path, text: str) -> bool:
    tmp = pathlib.Path(str(path) + ".tmp.media_rescue186")
    tmp.write_text(text, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except Exception as exc:
        print("media_rescue_patch_186: py_compile failed, leaving original:", exc)
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(path)
    return True


def main() -> None:
    try:
        text = BASE.read_text(encoding="utf-8")
    except Exception as exc:
        print("media_rescue_patch_186: cannot read base.py:", exc)
        return
    if MARKER in text:
        print("media_rescue_patch_186: already applied")
        return
    missing = [name for name, frag in
               (("helpers-anchor", HELPERS_ANCHOR), ("strict-tail", STRICT_OLD))
               if frag not in text]
    if missing:
        print("media_rescue_patch_186: SKIP (anchors changed):", missing)
        return
    patched = text.replace(HELPERS_ANCHOR, HELPERS + HELPERS_ANCHOR, 1)
    patched = patched.replace(STRICT_OLD, STRICT_NEW, 1)
    if _safe_write(BASE, patched):
        print("media_rescue_patch_186: applied")


if __name__ == "__main__":
    main()
