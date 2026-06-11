#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent patch: rescue agent-produced MEDIA files instead of dropping them.

Problem (2026-06-11): the model wrote a deliverable to /root/<file>.pdf and
emitted a MEDIA directive. /root is on the hardcoded system denylist in
gateway/platforms/base.py, so validate_media_delivery_path() returned None and
filter_media_delivery_paths() dropped the attachment with a log-only warning.
The agent got no error signal and repeatedly told the owner the file was sent.

Fix: when validation rejects a path purely because of its LOCATION, but the
file (a) exists, (b) is not under a credential/system-sensitive location,
(c) was produced within the last 30 minutes (the same session-trust signal the
upstream code uses for strict mode), and (d) is not huge — copy it into the
allowlisted outbox (~/.hermes/outbox) and deliver from there. Credential paths
(~/.ssh, ~/.hermes/* except caches, /etc, …) and stale files remain rejected.

Runs as ExecStartPre of hermes-gateway.service (same contract as
apply_patches.py): every write is py_compile-validated on a temp copy and
swapped in atomically; always exits 0 so gateway startup is never blocked.

Source of truth in git: hermes-brain scripts/hermes_media_rescue_patch.py
"""
import pathlib
import py_compile

BASE = pathlib.Path("/usr/local/lib/hermes-agent/gateway/platforms/base.py")

MARKER = "_rescue_media_path_to_outbox"

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
    for hermes_root in (_HERMES_HOME, _HERMES_ROOT):
        try:
            denied = Path(hermes_root).resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            continue
        if _path_is_within(resolved, denied):
            return True
    for prefix in ("/etc", "/proc", "/sys", "/dev", "/boot", "/var",
                   "/usr", "/bin", "/sbin", "/lib", "/lib64", "/run"):
        if _path_is_within(resolved, Path(prefix)):
            return True
    return False


def _rescue_media_path_to_outbox(resolved: Path) -> Optional[str]:
    """Copy a freshly produced non-credential file into the outbox allowlist.

    Local patch (2026-06-11). Files the agent had just created outside the
    allowlisted dirs used to be dropped silently, so the agent kept claiming
    a delivery that never happened (/root/integral_solution_2026.pdf).
    Recency is the session-trust signal; credential and system locations
    stay rejected.
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
        logger.warning(
            "Rescued MEDIA path outside allowlist: %s -> %s",
            _log_safe_path(str(resolved)), target,
        )
        return str(target)
    except Exception as exc:
        logger.warning(
            "MEDIA rescue failed for %s: %s", _log_safe_path(str(resolved)), exc
        )
        return None


'''

NONSTRICT_OLD = '''    if not _media_delivery_strict_mode():
        if _path_under_denied_prefix(resolved):
            return None
        return str(resolved)
'''

NONSTRICT_NEW = '''    if not _media_delivery_strict_mode():
        if _path_under_denied_prefix(resolved):
            return _rescue_media_path_to_outbox(resolved)
        return str(resolved)
'''

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
    tmp = pathlib.Path(str(path) + ".tmp.media_rescue")
    tmp.write_text(text, encoding="utf-8")
    try:
        py_compile.compile(str(tmp), doraise=True)
    except Exception as exc:
        print("media_rescue_patch: py_compile failed, leaving original:", exc)
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(path)
    return True


def main() -> None:
    try:
        text = BASE.read_text(encoding="utf-8")
    except Exception as exc:
        print("media_rescue_patch: cannot read base.py:", exc)
        return
    if MARKER in text:
        print("media_rescue_patch: already applied")
        return
    missing = [name for name, frag in
               (("helpers-anchor", HELPERS_ANCHOR),
                ("nonstrict", NONSTRICT_OLD),
                ("strict-tail", STRICT_OLD))
               if frag not in text]
    if missing:
        print("media_rescue_patch: anchors not found, skipping:", missing)
        return
    patched = text.replace(HELPERS_ANCHOR, HELPERS + HELPERS_ANCHOR, 1)
    patched = patched.replace(NONSTRICT_OLD, NONSTRICT_NEW, 1)
    patched = patched.replace(STRICT_OLD, STRICT_NEW, 1)
    if _safe_write(BASE, patched):
        print("media_rescue_patch: applied")


if __name__ == "__main__":
    main()
