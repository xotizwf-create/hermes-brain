import json, urllib.request, subprocess, tempfile, os
from pathlib import Path
APP = Path("/var/www/prostye-postavki/app")
secret = ""
for line in (APP / ".env.local").read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith("MCP_SERVER_SECRET="):
        secret = line.split("=", 1)[1].strip().strip('"')
DOC = "30390ab0-3cc0-400a-b9d7-832c73486692"
bin_path = APP / "backend" / "data" / "pending_contract_files" / f"{DOC}.bin"
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
    f.write(bin_path.read_bytes()); tmp = f.name
out = subprocess.run(["pdfinfo", tmp], capture_output=True, text=True)
for ln in out.stdout.splitlines():
    if ln.startswith(("Pages", "Page size")): print(ln)
os.unlink(tmp)
