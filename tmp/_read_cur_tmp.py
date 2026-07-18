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
print("=== _b24_compose_user_text (current) ===")
print(jb(r'''cd /var/www/albery && awk '/^def _b24_compose_user_text/{f=1} f{print} f&&/return /{if(--c<0)exit}' app.py | head -25'''))
print("\n=== MSGADD extras call + empty check + spawn (current) ===")
print(jb(r'''cd /var/www/albery && grep -n "image_texts, reply_text = _b24_message_extras\|not image_texts and not reply_text\|_b24_compose_user_text(message_text" app.py'''))
print(jb(r'''cd /var/www/albery && sed -n '/image_texts, reply_text = _b24_message_extras(payload)/,/return jsonify({"ok": True, "event": event_name, "accepted": True})/p' app.py'''))
print("\n=== _b24_extract_escalation + its use in _b24_app_process ===")
print(jb(r'''cd /var/www/albery && sed -n '/def _b24_extract_escalation/,/^def /p' app.py | head -40'''))
print("\n=== hermes_brain_answer fmt string end (to append deliver instruction) ===")
print(jb(r'''cd /var/www/albery && grep -n "аккуратным оформлением, акцентами жирным и живыми эмодзи" app.py'''))
sh("rm -f /tmp/.alb_pw"); c.close(); print("\nDONE")
