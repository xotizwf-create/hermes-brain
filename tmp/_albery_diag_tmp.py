# -*- coding: utf-8 -*-
"""TEMP: read-only diagnosis of the Albery Hermes (186) media-drop issue.
Connects to 217, reads 186 creds from the Vault, sshpass-jumps to 186. No secrets printed."""
import sys, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

env = {}
with open(".env", encoding="utf-8") as f:
    for line in f:
        s = line.strip()
        if "=" in s and not s.startswith("#"):
            k, v = s.split("=", 1); env[k.strip()] = v.strip()
host, user, pwd = env["IP"], env["USER"], env["PASSWORD"]  # 217

cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(host, username=user, password=pwd, timeout=30)
print(f"connected to 217 ({user}@{host})")
def sh(c):
    _, o, e = cli.exec_command(c); return o.read().decode("utf-8","ignore").rstrip(), e.read().decode("utf-8","ignore").rstrip()

VAULT = "/opt/hermes/secure/projects/albery/.env"
print("\n-- 217: prerequisites --")
print("sshpass:", sh("command -v sshpass || echo MISSING")[0])
print("vault file:", sh(f"test -f {VAULT} && echo present || echo MISSING")[0])
ip186 = sh(f"awk -F= '$1==\"IP\"{{print $2}}' {VAULT}")[0].strip()
usr186 = sh(f"awk -F= '$1==\"USER\"{{print $2}}' {VAULT}")[0].strip() or "root"
print("186 IP from vault:", ip186, "| user:", usr186)
# stage 186 password into a 600 temp file on 217 (never printed)
sh(f"awk -F= '$1==\"PASSWORD\"{{print $2}}' {VAULT} > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
print("pw staged:", sh("test -s /tmp/.alb_pw && echo yes || echo NO")[0])

def j(remote):  # run a command ON 186 via the jump
    cmd = ("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 "
           f"{usr186}@{ip186} " + "'" + remote.replace("'", "'\\''") + "'")
    return sh(cmd)

print("\n========== 186 (Albery) PREFLIGHT (rule #7) ==========")
print(j("free -m; echo '---'; swapon --show; echo '---'; uptime; echo '---'; df -h / | tail -1")[0])
print("\nservices:", j("systemctl is-active albery hermes-gateway 2>&1 | tr '\\n' ' '")[0])
print("hermes ver:", j("hermes --version 2>&1 | head -1")[0])

print("\n========== DIAGNOSIS ==========")
print("\n-- config: media_delivery_allow_dirs (likely the bug) --")
print(j("grep -n -A8 'media_delivery_allow_dirs\\|media_delivery' /root/.hermes/config.yaml 2>&1 | head -20")[0] or "  (key ABSENT in config.yaml)")
print("\n-- gateway section of config (context) --")
print(j("awk '/^gateway:/{f=1} f{print} /^[a-z]/{if(f && !/^gateway:/)exit}' /root/.hermes/config.yaml 2>&1 | head -25")[0])
print("\n-- journal: silent MEDIA drops? --")
print("count:", j("journalctl -u hermes-gateway --no-pager 2>/dev/null | grep -c 'Skipping unsafe MEDIA'")[0])
print(j("journalctl -u hermes-gateway --no-pager 2>/dev/null | grep 'Skipping unsafe MEDIA' | tail -3")[0] or "  (no such log lines)")
print("\n-- rescue patch present? --")
print("patches dir:", j("ls -la /root/.hermes/patches/ 2>&1 | tr '\\n' '|'")[0])
print("rescue marker in base.py:", j("grep -c _rescue_media_path_to_outbox /usr/local/lib/hermes-agent/gateway/platforms/base.py 2>&1")[0])
print("\n-- where do PDFs land? recent .pdf files --")
print(j("find /root /tmp /var/www/albery -maxdepth 3 -name '*.pdf' -mmin -4320 2>/dev/null | head -10")[0] or "  (no recent pdfs)")
print("\n-- owner weekly pdf code path (albery app) --")
print(j("grep -rn 'send_owner_weekly_report_pdf\\|weekly_report.*pdf\\|outbox' /var/www/albery/*.py 2>/dev/null | head -8")[0] or "  (no hits)")

sh("rm -f /tmp/.alb_pw")
print("\n(pw file removed)")
cli.close()
print("DONE")
