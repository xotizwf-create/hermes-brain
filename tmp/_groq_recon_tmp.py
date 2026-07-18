# -*- coding: utf-8 -*-
"""TEMP read-only: locate Groq keys on 217 and 186 (MASKED — never print full value)."""
import sys, paramiko
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

# mask helper runs server-side: prints file:var starts<6>...len
MASK = (r'''for f in /root/.hermes/secure/*.env /root/.hermes/.env /root/.hermes/secure/secrets.yaml; do '''
        r'''[ -f "$f" ] && grep -aiE "GROQ" "$f" | while IFS= read -r line; do '''
        r'''k="${line%%=*}"; val="${line#*=}"; '''
        r'''echo "$f :: ${k} :: starts=$(printf %s "$val" | cut -c1-6) len=$(printf %s "$val" | wc -c)"; done; done''')

print("======== 217 (current project) Groq keys ========")
print(sh(MASK) or "(none found in those files)")
print("\n217 aux health (recent journal): ", sh("journalctl -u hermes-gateway --no-pager --since '10 min ago' 2>/dev/null | grep -aic 'payment / credit'") , "payment/credit warnings")

# jump to 186
v="/opt/hermes/secure/projects/albery/.env"
ip=sh("awk -F= '$1==\"IP\"{print $2}' "+v).strip()
sh("awk -F= '$1==\"PASSWORD\"{print $2}' "+v+" > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
def j(r):
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 root@"+ip+" '"+r.replace("'", "'\\''")+"'")
print("\n======== 186 (Albery) Groq keys ========")
print(j(MASK) or "(none found)")
print("\n186 aux config (where key is referenced):")
print(j("grep -rniE 'groq|api_key|GROQ_API_KEY' /root/.hermes/config.yaml 2>/dev/null | head -8 | tr -cd '[:print:]\\n'"))
print("186 systemd env files for gateway:")
print(j("systemctl cat hermes-gateway 2>/dev/null | grep -iE 'EnvironmentFile|Environment=' | tr -cd '[:print:]\\n'"))
sh("rm -f /tmp/.alb_pw"); c.close(); print("\nDONE")
