import sys, base64, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CONF={}
for l in open(".env",encoding="utf-8"):
    s=l.strip()
    if "=" in s and not s.startswith("#"):
        k,v=s.split("=",1); CONF[k.strip()]=v.strip()
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(CONF["IP"],username=CONF["USER"],password=CONF["PASSWORD"],timeout=30)
def sh(x):
    _,o,e=c.exec_command(x); return (o.read().decode("utf-8","ignore")+e.read().decode("utf-8","ignore")).rstrip()
ip=sh("awk -F= '$1==\"IP\"{print $2}' /opt/hermes/secure/projects/albery/.env").strip()
sh("awk -F= '$1==\"PASSWORD\"{print $2}' /opt/hermes/secure/projects/albery/.env > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
def j(r):
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=60 root@"+ip+" '"+r.replace("'", "'\''")+"'")
EDIT=("import time,shutil\n"
 "p='/var/www/albery/.env'\n"
 "shutil.copy(p,p+'.bak.'+str(int(time.time())))\n"
 "drop=('GOOGLE_API_KEY=','GOOGLE_API_BASE_URL=')\n"
 "ls=open(p,encoding='utf-8').read().splitlines()\n"
 "out=[ln for ln in ls if not ln.startswith(drop)]\n"
 "open(p,'w',encoding='utf-8').write(chr(10).join(out)+chr(10))\n"
 "print('removed lines:', len(ls)-len(out))\n")
print("remove GOOGLE_API_* from .env:", j("echo "+base64.b64encode(EDIT.encode()).decode()+" | base64 -d > /tmp/_e.py && python3 /tmp/_e.py && rm -f /tmp/_e.py"))
print("verify gone:", j("grep -cE '^GOOGLE_API_KEY=|^GOOGLE_API_BASE_URL=' /var/www/albery/.env || echo 0"))
print("restart albery+gateway:", j("systemctl restart albery hermes-gateway && sleep 4 && systemctl is-active albery hermes-gateway"))
print("app health (MCP responds):", j("curl -s -o /dev/null -w '%{http_code}' https://mcp.m4s.ru/ 2>&1; echo"))
sh("rm -f /tmp/.alb_pw"); c.close()
