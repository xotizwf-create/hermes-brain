# -*- coding: utf-8 -*-
"""TEMP background: trigger a fresh owner-weekly run, wait for a NEW report (generated_at >
baseline), fetch report_text, summarize structure (leader tables / Friday / Bitrix anomaly)."""
import sys, time, base64, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CONF = {}
for l in open(".env", encoding="utf-8"):
    s=l.strip()
    if "=" in s and not s.startswith("#"):
        k,v=s.split("=",1); CONF[k.strip()]=v.strip()
BASELINE = "2026-06-13 15:29:11"

def conn_jump():
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

# trigger
c, sh, j = conn_jump()
print("trigger @", time.strftime("%H:%M:%S"), ":", j("hermes cron run 4baf5fcd80d1 2>&1 | tr -cd '[:print:]\\n'"), flush=True)
sh("rm -f /tmp/.alb_pw"); c.close()

FETCH = r"""
import base64,json
db=None
for line in open('/var/www/albery/.env',encoding='utf-8'):
    if line.startswith('DATABASE_URL='): db=line.split('=',1)[1].strip().strip('"').strip("'"); break
try:
    import psycopg; conn=psycopg.connect(db)
except Exception:
    import psycopg2; conn=psycopg2.connect(db)
cur=conn.cursor()
cur.execute("SELECT period_start, period_end, generated_at, length(report_text), report_text FROM owner_weekly_reports ORDER BY generated_at DESC LIMIT 1")
r=cur.fetchone()
print("LATEST "+json.dumps({"ps":str(r[0]),"pe":str(r[1]),"gen":str(r[2]),"len":r[3]}))
print("RT64 "+base64.b64encode((r[4] or "").encode()).decode())
"""
for i in range(24):  # ~36 min
    time.sleep(90)
    try:
        c, sh, j = conn_jump()
        j("echo "+base64.b64encode(FETCH.encode()).decode()+" > /tmp/_q.b64 && base64 -d /tmp/_q.b64 > /tmp/_q.py")
        out=j("cd /var/www/albery && .venv/bin/python /tmp/_q.py 2>&1")
        j("rm -f /tmp/_q.py /tmp/_q.b64"); sh("rm -f /tmp/.alb_pw"); c.close()
    except Exception as ex:
        print(f"[{time.strftime('%H:%M:%S')}] cycle err {str(ex)[:60]}", flush=True); continue
    gen=""; rt64=""
    for ln in out.splitlines():
        if ln.startswith("LATEST "):
            gen=json._default_decoder.decode(ln[7:]).get("gen","") if hasattr(json,'_default_decoder') else __import__("json").loads(ln[7:]).get("gen","")
            print(f"[{time.strftime('%H:%M:%S')}] "+ln, flush=True)
        if ln.startswith("RT64 "): rt64=ln[5:]
    if gen and gen > BASELINE:
        rt=base64.b64decode(rt64).decode("utf-8","ignore")
        open("_fresh_report.md","w",encoding="utf-8",newline="\n").write(rt)
        verdict_tables = rt.count("| Вердикт")
        print("=== NEW REPORT generated_at="+gen+" ===", flush=True)
        print("len:", len(rt), flush=True)
        print("leader-table '| Вердикт' columns:", verdict_tables, flush=True)
        print("section-6 'Оценка руководителей':", "Оценка руководителей" in rt, flush=True)
        print("Friday-as-выходной:", ("выходн" in rt.lower()), flush=True)
        print("Bitrix-Marketplace flag:", ("Marketplace" in rt or "Маркетплейс" in rt), flush=True)
        print("first 3 headings:", [l for l in rt.splitlines() if l.strip().startswith("#")][:4], flush=True)
        print("saved _fresh_report.md", flush=True)
        break
else:
    print("=== timed out: no new report within ~36 min ===", flush=True)
print("VERIFY_DONE", flush=True)
