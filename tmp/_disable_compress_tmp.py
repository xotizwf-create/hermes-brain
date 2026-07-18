# -*- coding: utf-8 -*-
import sys, base64, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
env = {}
for l in open(".env", encoding="utf-8"):
    s=l.strip()
    if "=" in s and not s.startswith("#"):
        k,v=s.split("=",1); env[k.strip()]=v.strip()
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(env["IP"],username=env["USER"],password=env["PASSWORD"],timeout=30)
def sh(x):
    _,o,e=c.exec_command(x); return (o.read().decode("utf-8","ignore")+e.read().decode("utf-8","ignore")).rstrip()
v="/opt/hermes/secure/projects/albery/.env"
ip=sh("awk -F= '$1==\"IP\"{print $2}' "+v).strip()
sh("awk -F= '$1==\"PASSWORD\"{print $2}' "+v+" > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
def j(r):
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=45 root@"+ip+" '"+r.replace("'", "'\\''")+"'")
edit = r"""
import time, shutil
p='/root/.hermes/config.yaml'
t=open(p,encoding='utf-8').read()
old='compression:\n  enabled: true'
new='compression:\n  enabled: false'
if old not in t:
    print('ANCHOR_NOT_FOUND'); raise SystemExit(1)
shutil.copy2(p, p+'.bak.nocompress.%d'%int(time.time()))
open(p,'w',encoding='utf-8').write(t.replace(old,new,1))
# verify parse + value
import yaml
d=yaml.safe_load(open(p,encoding='utf-8'))
print('compression.enabled =', d['compression']['enabled'])
"""
j("echo "+base64.b64encode(edit.encode()).decode()+" > /tmp/_e.b64 && base64 -d /tmp/_e.b64 > /tmp/_e.py")
print("edit:", j("/usr/local/lib/hermes-agent/venv/bin/python /tmp/_e.py 2>&1"))
print("restart (also clears queued cron run):", j("systemctl restart hermes-gateway && sleep 7 && systemctl is-active hermes-gateway"))
print("verify in config:", j("grep -A1 '^compression:' /root/.hermes/config.yaml | tr -cd '[:print:]\\n'"))
print("owner-weekly next/last (queued run gone):", j("hermes cron list 2>&1 | grep -A6 owner-weekly | grep -iE 'last run|next run' | tr -cd '[:print:]\\n'"))
j("rm -f /tmp/_e.py /tmp/_e.b64"); sh("rm -f /tmp/.alb_pw"); c.close(); print("DONE")
