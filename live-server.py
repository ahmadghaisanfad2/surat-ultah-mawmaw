#!/usr/bin/env python3
"""
Live Reload Server untuk Surat Cinta
- Serve file di folder ini
- Watch perubahan file .html/.css/.js
- Browser auto-refresh saat file disimpan
- Buka http://localhost:8089 di browser
"""

import http.server
import socketserver
import os
import time
import hashlib
import threading
import json
from pathlib import Path

PORT = 8089
DIR = Path(__file__).parent

# Track file hashes for change detection
file_hashes = {}

def get_hash(filepath):
    """Get MD5 hash of file content"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def scan_files():
    """Scan all HTML/CSS/JS files and store hashes"""
    hashes = {}
    for ext in ['*.html', '*.css', '*.js']:
        for f in DIR.glob(ext):
            hashes[str(f)] = get_hash(f)
    return hashes

def detect_changes():
    """Check if any file changed"""
    global file_hashes
    new_hashes = scan_files()
    changed = []
    for path, h in new_hashes.items():
        if path in file_hashes and file_hashes[path] != h:
            changed.append(os.path.basename(path))
        elif path not in file_hashes:
            changed.append(os.path.basename(path))
    # Check deleted files
    for path in file_hashes:
        if path not in new_hashes:
            changed.append(os.path.basename(path))
    file_hashes = new_hashes
    return changed


class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that injects live-reload script into HTML"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def do_GET(self):
        # SSE endpoint for live reload
        if self.path == '/__livereload':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            last_check = time.time()
            try:
                while True:
                    changed = detect_changes()
                    if changed:
                        data = json.dumps({"changed": changed})
                        self.wfile.write(f"data: {data}\n\n".encode())
                        self.wfile.flush()
                        print(f"🔄 Changed: {', '.join(changed)}")
                    time.sleep(0.5)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        # Serve HTML files with injected script
        if self.path == '/' or self.path.endswith('.html'):
            filepath = DIR / (self.path.lstrip('/') or 'index.html')
            if filepath.exists() and filepath.suffix == '.html':
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Inject live-reload script before </body>
                reload_script = """
<script>
// ──── LIVE RELOAD (auto-injected by server) ────
(function() {
  const sse = new EventSource('/__livereload');
  sse.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log('🔄 File changed, reloading...', data.changed);
    location.reload();
  };
  sse.onerror = function() {
    console.log('⚠️ Live reload disconnected, retrying...');
  };
})();
</script>
"""
                if '</body>' in content:
                    content = content.replace('</body>', reload_script + '</body>')
                else:
                    content += reload_script

                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', len(content.encode()))
                self.end_headers()
                self.wfile.write(content.encode())
                return

        # Serve other files normally (CSS, JS, images, fonts)
        return super().do_GET()

    def log_message(self, format, *args):
        # Quieter logging
        if '/__livereload' not in str(args):
            super().log_message(format, *args)


def main():
    global file_hashes
    file_hashes = scan_files()

    with socketserver.TCPServer(("", PORT), LiveReloadHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"""
╔══════════════════════════════════════════════╗
║   💕 Surat Cinta - Live Reload Server       ║
╠══════════════════════════════════════════════╣
║                                              ║
║   Buka di browser:                           ║
║   👉 http://localhost:{PORT}                  ║
║                                              ║
║   Edit index.html → save → auto-refresh!     ║
║   Ctrl+C untuk stop server                   ║
║                                              ║
╚══════════════════════════════════════════════╝
""")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped.")

if __name__ == '__main__':
    main()
