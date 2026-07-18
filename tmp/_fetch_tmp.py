# -*- coding: utf-8 -*-
"""TEMP: download the good ref report, the cron prompt, and the current bad report to local."""
import sys, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
env = {}
with open(".env", encoding="utf-8") as f:
    for line in f:
        s = line.strip()
        if "=" in s and not s.startswith("#"):
            k, v = s.split("=", 1); env[k.strip()] = v.strip()
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(env["IP"], username=env["USER"], password=env["PASSWORD"], timeout=30)
def sh(c):
    _, o, e = cli.exec_command(c); return o.read().decode("utf-8","ignore").rstrip(), e.read().decode("utf-8","ignore").rstrip()

def save(local, content):
    open(local, "w", encoding="utf-8", newline="\n").write(content)
    print(f"  saved {local} ({len(content)} chars)")

# 217 files (direct)
print("downloading from 217:")
save("_good_v2.md", sh("cat /tmp/albery_weekly_report_v2.md")[0])
save("_good_v3_is_pdf.txt", "(v3 is the 72KB PDF; v2.md is the readable markdown source)")
save("_prompt_file.txt", sh("cat /root/projects/albery/scripts/hermes_owner_weekly_prompt.txt")[0])

# 186 via jump
VAULT="/opt/hermes/secure/projects/albery/.env"
ip=sh(f"awk -F= '$1==\"IP\"{{print $2}}' {VAULT}")[0].strip()
sh(f"awk -F= '$1==\"PASSWORD\"{{print $2}}' {VAULT} > /tmp/.alb_pw && chmod 600 /tmp/.alb_pw")
def j(r):
    return sh("sshpass -f /tmp/.alb_pw ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 "
              f"root@{ip} '" + r.replace("'", "'\\''") + "'")[0]
print("downloading from 186:")
save("_bad_current.md", j("cat /tmp/weekly_report_2026-06-08_2026-06-12.md"))
# the cron job's ACTUAL prompt (jobs.json owner-weekly)
extract = (r"import json; d=json.load(open('/root/.hermes/cron/jobs.json')); "
           r"jobs=d if isinstance(d,list) else d.get('jobs',d); "
           r"import sys; "
           r"[print(j.get('prompt','(no prompt field)')) for j in (jobs.values() if isinstance(jobs,dict) else jobs) if isinstance(j,dict) and j.get('name')=='owner-weekly']")
import base64
b=base64.b64encode(extract.encode()).decode()
j(f"echo {b} | base64 -d > /tmp/_ex.py")
save("_cron_actual_prompt.txt", j("/usr/local/lib/hermes-agent/venv/bin/python /tmp/_ex.py 2>&1"))
j("rm -f /tmp/_ex.py"); sh("rm -f /tmp/.alb_pw")
cli.close(); print("DONE")
