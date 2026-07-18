"""Probe #2: try gpt-5.6-terra WITH the codex provider explicitly; also ask codex what models it has."""
import subprocess

ENV = {"HOME": "/root", "PATH": "/usr/local/bin:/usr/bin:/bin"}


def run(cmd, timeout=200):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd="/root", env=ENV)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


# 1) hermes model list (what does hermes think is available on this provider?)
rc, out, err = run(["hermes", "model", "list"], timeout=90)
print("hermes model list rc:", rc)
print((out or err)[:1200])

# 2) live turns with explicit provider
for model in ("gpt-5.6-terra", "gpt-5.6", "gpt-5.5"):
    rc, out, err = run(["hermes", "-z", "Ответь одним словом: работаю",
                        "--provider", "openai-codex", "-m", model])
    print(f"\n[{model}] rc={rc} out={out[:100]!r}")
    if err:
        print("  stderr:", err[:300])
