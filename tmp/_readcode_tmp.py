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
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=40 root@"+ip+" '"+r.replace("'", "'\\''")+"'")

def dump(a,b):
    rd=("t=open('/usr/local/lib/hermes-agent/gateway/run.py',encoding='utf-8').read().splitlines();"
        "print(chr(10).join('%5d| %s'%(i+1,t[i]) for i in range(%d-1,%d)))" % (a,b))
    j("echo "+base64.b64encode(rd.encode()).decode()+" | base64 -d > /tmp/_rd.py")
    return j("/usr/local/lib/hermes-agent/venv/bin/python /tmp/_rd.py 2>&1")

print("===== run.py 222-256 (the message def) =====")
print(dump(222,256))
print("\n===== run.py 9244-9300 (usage_limit classifier) =====")
print(dump(9244,9300))
print("\n===== run.py 16650-16700 (generic auth-fail final_response) =====")
print(dump(16650,16700))
j("rm -f /tmp/_rd.py"); sh("rm -f /tmp/.alb_pw"); c.close(); print("DONE")
