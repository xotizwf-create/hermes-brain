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

print("=== doc/pdf libs in albery venv ===")
print(jb(r'''cd /var/www/albery && .venv/bin/pip list 2>/dev/null | grep -iE "markitdown|python-docx|docx|openpyxl|pdfminer|pymupdf|fitz|weasyprint|reportlab|fpdf|markdown|xhtml2pdf|pandas|Pillow|xlrd" '''))
print("\n=== system converters (libreoffice/pandoc/antiword/wkhtmltopdf) ===")
print(jb(r'''for b in libreoffice soffice pandoc antiword wkhtmltopdf wkhtmltoimage; do which $b 2>/dev/null && echo "  ^$b"; done; echo "done"'''))
print("\n=== how owner weekly PDF is generated (pdf_bytes source) ===")
print(jb(r'''cd /var/www/albery && grep -nE "def .*pdf|pdf_bytes|weasyprint|HTML\(|render.*pdf|markdown.*pdf|def upload_pdf_to_bitrix_disk|send_owner_weekly_report_pdf|fpdf|reportlab|def _b24_send_file|im.disk.file.commit|disk.storage.uploadfile" app.py | head -40'''))
sh("rm -f /tmp/.alb_pw"); c.close(); print("\nDONE")
