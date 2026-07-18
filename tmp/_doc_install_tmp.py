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
def jrun(cmd, t=300):
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=45 root@"+ip+" "+cmd)
print("=== preflight ===")
print(jrun("'free -m | grep -E \"Mem|Swap\"; uptime'"))
print("\n=== pip install (pure-python wheels) ===")
print(jrun("'cd /var/www/albery && .venv/bin/pip install --no-input pypdf python-docx openpyxl 2>&1 | tail -8'"))
print("\n=== free after ===")
print(jrun("'free -m | grep Mem'"))
sh("rm -f /tmp/.alb_pw"); c.close(); print("\nDONE")
