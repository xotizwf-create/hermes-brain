# -*- coding: utf-8 -*-
"""Local verify: apply OLD->NEW from the patch onto a stub, compile + test classification."""
import importlib.util, py_compile, tempfile, os, re

spec = importlib.util.spec_from_file_location("pep", "scripts/hermes_provider_error_patch.py")
pep = importlib.util.module_from_spec(spec); spec.loader.exec_module(pep)

# Build a stub run.py fragment: regex defs + the function containing OLD, then patch it.
stub = '''import re
_GATEWAY_PROVIDER_POLICY_RE = re.compile(r"(policy\\\\s+violation)", re.IGNORECASE)
_GATEWAY_AUTH_ERROR_RE = re.compile(r"(provider\\\\s+authentication\\\\s+failed|invalid\\\\s+api\\\\s+key|\\\\b401\\\\b)", re.IGNORECASE)
_GATEWAY_RATE_LIMIT_RE = re.compile(r"(rate\\\\s+limit|\\\\b429\\\\b|quota|usage\\\\s+limit)", re.IGNORECASE)


def _gateway_provider_error_reply(text: str) -> str:
    """doc"""
''' + pep.OLD + '''    if _GATEWAY_PROVIDER_POLICY_RE.search(text):
        return "policy"
    if _GATEWAY_RATE_LIMIT_RE.search(text):
        return "old-rate"
    return "fallback"
'''

assert pep.OLD in stub, "OLD anchor not in stub"
patched = stub.replace(pep.OLD, pep.NEW, 1)
assert pep.MARKER in patched, "marker missing after patch"

# compile the patched stub
with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
    f.write(patched); path=f.name
try:
    py_compile.compile(path, doraise=True)
    print("PATCHED_STUB_COMPILES_OK")
except Exception as e:
    print("COMPILE_FAIL:", e); raise SystemExit(1)

# exec + test classification
ns={}; exec(patched, ns)
fn=ns["_gateway_provider_error_reply"]
t429="HTTP 429: {'error': {'type': 'usage_limit_reached', 'message': 'The usage limit has been reached', 'resets_in_seconds': 4936}}"
print("429 usage-limit ->", fn(t429))
print("auth          ->", fn("Codex authentication failed - invalid api key"))
print("rate-limit    ->", fn("rate limit exceeded, slow down"))
print("policy        ->", fn("policy violation detected"))
print("other         ->", fn("some weird error"))
os.unlink(path)
