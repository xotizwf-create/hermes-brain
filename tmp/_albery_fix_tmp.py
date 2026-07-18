# -*- coding: utf-8 -*-
"""TEMP: fix Albery Hermes (186) media drop — allowlist media_cache/outbox/tmp.
Backup -> surgical edit -> yaml-verify before write -> restart gateway -> verify. No secrets printed."""
import sys, base64, time, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

env = {}
with open(".env", encoding="utf-8") as f:
    for line in f:
        s = line.strip()
        if "=" in s and not s.startswith("#"):
            k, v = s.split("=", 1); env[k.strip()] = v.strip()
host, user, pwd = env["IP"], env["USER"], env["PASSWORD"]

cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(host, username=user, password=pwd, timeout=30)
def sh(c):
    _, o, e = cli.exec_command(c); return o.read().decode("utf-8","ignore").rstrip(), e.read().decode("utf-8","ignore").rstrip()

VAULT = "/opt/hermes/secure/projects/albery/.env"
ip186 = sh(f"awk -F= '$1==\"IP\"{{print $2}}' {VAULT}")[0].strip()
sh(f"awk -F= '$1==\"PASSWORD\"{{print $2}}' {VAULT} > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
VENV = "/usr/local/lib/hermes-agent/venv/bin/python"

def j(remote):
    cmd = ("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 "
           f"root@{ip186} " + "'" + remote.replace("'", "'\\''") + "'")
    return sh(cmd)

# --- edit script that runs on 186 (venv python: has yaml) ---
edit = r'''
import shutil, time, sys, yaml
p = '/root/.hermes/config.yaml'
ts = int(time.time()); bak = '%s.bak.mediafix.%d' % (p, ts)
shutil.copy2(p, bak)
t = open(p, encoding='utf-8').read()
old = '  media_delivery_allow_dirs: []\n'
new = ('  media_delivery_allow_dirs:\n'
       '    - /root/.hermes/media_cache\n'
       '    - /root/.hermes/outbox\n'
       '    - /tmp\n')
if old not in t:
    print('ANCHOR_NOT_FOUND'); sys.exit(2)
t2 = t.replace(old, new, 1)
d = yaml.safe_load(t2)
want = ['/root/.hermes/media_cache', '/root/.hermes/outbox', '/tmp']
got = d['gateway']['media_delivery_allow_dirs']
if got != want:
    print('VERIFY_FAILED', got); sys.exit(3)
open(p, 'w', encoding='utf-8').write(t2)
print('CONFIG_PATCHED_OK', bak)
'''
b64 = base64.b64encode(edit.encode("utf-8")).decode("ascii")
print("-- writing + running edit script on 186 --")
print(j(f"echo {b64} | base64 -d > /tmp/_fix_media.py")[0] or "(staged)")
out, err = j(f"{VENV} /tmp/_fix_media.py")
print("edit:", out or err)

if "CONFIG_PATCHED_OK" not in out:
    print("!! edit did not succeed — NOT restarting. Aborting.")
    sh("rm -f /tmp/.alb_pw"); cli.close(); sys.exit(1)

print("\n-- restarting hermes-gateway ONLY (not albery) --")
print(j("systemctl restart hermes-gateway && sleep 6 && systemctl is-active hermes-gateway")[0])

print("\n-- verify config value live --")
print(j("grep -n -A4 'media_delivery_allow_dirs' /root/.hermes/config.yaml | head -6")[0])

print("\n-- journal since restart (errors?) --")
print(j("journalctl -u hermes-gateway --no-pager --since '20 seconds ago' 2>/dev/null | tail -8")[0] or "(quiet)")

print("\n-- functional check: does validate_media_delivery_path now ACCEPT the PDF? --")
test = (r"import sys; sys.path.insert(0,'/usr/local/lib/hermes-agent'); "
        r"from gateway.platforms import base; "
        r"print('VALIDATE_RESULT:', base.validate_media_delivery_path('/root/.hermes/media_cache/weekly_report_2026-06-08_2026-06-12.pdf'))")
tb64 = base64.b64encode(test.encode("utf-8")).decode("ascii")
j(f"echo {tb64} | base64 -d > /tmp/_test_media.py")
print(j(f"cd /root/.hermes && {VENV} /tmp/_test_media.py 2>&1 | tail -4")[0])

j("rm -f /tmp/_fix_media.py /tmp/_test_media.py")
sh("rm -f /tmp/.alb_pw")
print("\n(temp files removed)\nDONE")
