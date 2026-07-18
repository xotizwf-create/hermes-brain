import sys, base64, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
env={}
for l in open(".env",encoding="utf-8"):
    s=l.strip()
    if "=" in s and not s.startswith("#"):
        k,v=s.split("=",1); env[k.strip()]=v.strip()
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(env["IP"],username=env["USER"],password=env["PASSWORD"],timeout=60)
def sh(x):
    _,o,e=c.exec_command(x); return (o.read().decode("utf-8","ignore")+e.read().decode("utf-8","ignore")).rstrip()
vf="/opt/hermes/secure/projects/albery/.env"
ip=sh("awk -F= '$1==\"IP\"{print $2}' "+vf).strip()
sh("awk -F= '$1==\"PASSWORD\"{print $2}' "+vf+" > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
def jb(script):
    b=base64.b64encode(script.encode()).decode()
    sh("echo "+b+" | base64 -d > /tmp/_r.sh && sshpass -f /tmp/.alb_pw scp -o StrictHostKeyChecking=no /tmp/_r.sh root@"+ip+":/tmp/_r.sh >/dev/null 2>&1")
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no root@"+ip+" bash /tmp/_r.sh; sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no root@"+ip+" rm -f /tmp/_r.sh")
def jpy(script, name="_p.py"):
    b=base64.b64encode(script.encode()).decode()
    sh("echo "+b+" | base64 -d > /tmp/"+name+" && sshpass -f /tmp/.alb_pw scp -o StrictHostKeyChecking=no /tmp/"+name+" root@"+ip+":/tmp/"+name+" >/dev/null 2>&1")
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no root@"+ip+" 'cd /var/www/albery && .venv/bin/python /tmp/"+name+" 2>&1'; sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no root@"+ip+" rm -f /tmp/"+name)
print("=== onboarding steps block (21650-21725) ===")
print(jb(r'''cd /var/www/albery && sed -n '21650,21725p' app.py'''))
print("\n=== full capability content (verbatim) ===")
print(jpy(r'''
import sys; sys.path.insert(0,"/var/www/albery")
import app
with app.pg_connect() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT content FROM ai_agent_capabilities WHERE tier='full'")
        print(cur.fetchone()["content"])
'''))
sh("rm -f /tmp/.alb_pw"); c.close(); print("\nDONE")
