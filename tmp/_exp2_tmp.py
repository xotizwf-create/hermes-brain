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
print("=== download_export (24645-24675) ===")
print(jb(r'''cd /var/www/albery && sed -n '24645,24675p' app.py'''))
print("\n=== zoom export public url builder + token download route (21031-21100) ===")
print(jb(r'''cd /var/www/albery && grep -nE "_zoom_export_public_url|def _zoom_export|AUTH_EXEMPT|PUBLIC_BASE|EXTERNAL_URL|mcp.m4s.ru|public_base|def absolute_bitrix_url|ZOOM_EXPORT_TOKEN|export.*secret|hmac" app.py | head -30'''))
print("\n=== _zoom_export_public_url body ===")
print(jb(r'''cd /var/www/albery && awk '/def _zoom_export_public_url/{f=1} f{print; n++} f&&n>20{exit}' app.py'''))
sh("rm -f /tmp/.alb_pw"); c.close(); print("\nDONE")
