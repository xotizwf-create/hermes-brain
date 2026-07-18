# -*- coding: utf-8 -*-
"""TEMP background: wait for the fresh owner-weekly report (generated_at > baseline), fetch + verify."""
import sys, time, json, base64, paramiko
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
print("monitor2 started", time.strftime("%H:%M:%S"), flush=True)
for i in range(26):  # ~39 min
    time.sleep(90)
    try:
        c, sh, j = conn_jump()
        j("echo "+base64.b64encode(FETCH.encode()).decode()+" > /tmp/_q.b64 && base64 -d /tmp/_q.b64 > /tmp/_q.py")
        out=j("cd /var/www/albery && .venv/bin/python /tmp/_q.py 2>&1")
        j("rm -f /tmp/_q.py /tmp/_q.b64"); sh("rm -f /tmp/.alb_pw"); c.close()
    except Exception as ex:
        print(f"[{time.strftime('%H:%M:%S')}] cycle err {str(ex)[:60]}", flush=True); continue
    gen=""; rt64=""; meta={}
    for ln in out.splitlines():
        if ln.startswith("LATEST "):
            try: meta=json.loads(ln[7:]); gen=meta.get("gen","")
            except Exception: pass
        if ln.startswith("RT64 "): rt64=ln[5:]
    print(f"[{time.strftime('%H:%M:%S')}] latest gen={gen} len={meta.get('len')}", flush=True)
    if gen and gen > BASELINE:
        rt=base64.b64decode(rt64).decode("utf-8","ignore")
        open("_fresh_report.md","w",encoding="utf-8",newline="\n").write(rt)
        print("=== NEW REPORT gen="+gen+" period="+meta.get("ps","")+".."+meta.get("pe","")+" ===", flush=True)
        print("len:", len(rt), flush=True)
        print("section-6 'Оценка руководителей' present:", "Оценка руководителей" in rt, flush=True)
        print("leader-table '| Вердикт' cells:", rt.count("| Вердикт"), flush=True)
        print("Friday-as-выходной:", ("выходн" in rt.lower()), flush=True)
        print("Bitrix-Marketplace flag:", ("Marketplace" in rt or "Маркетплейс" in rt), flush=True)
        heads=[l for l in rt.splitlines() if l.strip().startswith("#") or (l.strip()[:2].rstrip().isdigit() and "." in l[:4])]
        print("headings:", heads[:14], flush=True)
        print("saved _fresh_report.md", flush=True)
        break
else:
    print("=== timed out: no new report within ~39 min ===", flush=True)
print("MONITOR2_DONE", flush=True)
