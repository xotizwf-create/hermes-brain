# -*- coding: utf-8 -*-
"""TEMP background: wait for codex usage-limit reset (~17:48 MSK), trigger owner-weekly ONCE,
then monitor until the run completes; report whether the report was produced + delivered."""
import sys, time, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CONF = {}
for l in open(".env", encoding="utf-8"):
    s=l.strip()
    if "=" in s and not s.startswith("#"):
        k,v=s.split("=",1); CONF[k.strip()]=v.strip()
PREV_LASTRUN = "16:25:55"  # the failed (429) run; a NEW run => different timestamp

def connect():
    c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(CONF["IP"],username=CONF["USER"],password=CONF["PASSWORD"],timeout=30)
    def sh(x):
        _,o,e=c.exec_command(x); return (o.read().decode("utf-8","ignore")+e.read().decode("utf-8","ignore")).rstrip()
    v="/opt/hermes/secure/projects/albery/.env"
    ip=sh("awk -F= '$1==\"IP\"{print $2}' "+v).strip()
    sh("awk -F= '$1==\"PASSWORD\"{print $2}' "+v+" > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
    def j(r):
        return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 root@"+ip+" '"+r.replace("'", "'\\''")+"'")
    return c, sh, j

# 1) wait for codex limit reset (~4920s to ~17:53 MSK)
print("autofinish: waiting ~82 min for codex usage-limit reset...", time.strftime("%H:%M:%S"), flush=True)
time.sleep(4920)

# 2) trigger ONCE
try:
    c, sh, j = connect()
    print("trigger @", time.strftime("%H:%M:%S"), ":", j("hermes cron run 4baf5fcd80d1 2>&1 | tr -cd '[:print:]\\n'"), flush=True)
    sh("rm -f /tmp/.alb_pw"); c.close()
except Exception as ex:
    print("trigger err:", str(ex)[:100], flush=True)

# 3) monitor up to ~40 min for completion
for i in range(27):
    time.sleep(90)
    try:
        c, sh, j = connect()
        lastrun=j("hermes cron list 2>&1 | grep -A6 owner-weekly | grep -i 'last run' | tr -cd '[:print:]'")
        pdfs=j("ls --time-style=+%H:%M /root/.hermes/media_cache/*.pdf 2>&1 | tr '\\n' ' '")
        err429=j("journalctl -u hermes-gateway --no-pager --since '3 min ago' 2>/dev/null | grep -ac 'usage limit'")
        deliv=j("journalctl -u hermes-gateway --no-pager --since '3 min ago' 2>/dev/null | grep -aciE 'MEDIA|save_owner_weekly|sendDocument'")
        sh("rm -f /tmp/.alb_pw"); c.close()
    except Exception as ex:
        print(f"[{time.strftime('%H:%M:%S')}] cycle err {str(ex)[:60]}", flush=True); continue
    lr = lastrun.split("Last run:")[-1].strip()[:25]
    print(f"[{time.strftime('%H:%M:%S')}] lastrun={lr} pdfs={pdfs.strip()} 429={err429} deliver_activity={deliv}", flush=True)
    if PREV_LASTRUN not in lastrun:
        ok = (err429 == "0")
        print("=== NEW RUN COMPLETED ===", flush=True)
        print("lastrun:", lastrun, flush=True)
        print("pdfs:", pdfs, flush=True)
        print("RESULT:", "LIKELY OK (no 429)" if ok else "RAN BUT 429 STILL PRESENT", flush=True)
        break
else:
    print("=== timed out waiting for new run ===", flush=True)
print("AUTOFINISH_DONE", flush=True)
