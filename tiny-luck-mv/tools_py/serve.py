#!/usr/bin/env python3
"""Tiny static server with HTTP Range support (for direct MV playback links).
Usage: python tools_py/serve.py [port] [dir]   (defaults 8000, render/)
"""
import os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

ROOT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else "render")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
TYPES = {".mp4": "video/mp4", ".html": "text/html; charset=utf-8", ".jpg": "image/jpeg", ".png": "image/png", ".md": "text/plain; charset=utf-8"}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            f = os.path.join(ROOT, "watch.html")
        else:
            f = os.path.normpath(os.path.join(ROOT, path.lstrip("/")))
            if not f.startswith(ROOT): return self.send_error(403)
        if not os.path.isfile(f): return self.send_error(404)
        ext = os.path.splitext(f)[1].lower()
        ctype = TYPES.get(ext, "application/octet-stream")
        size = os.path.getsize(f)
        rng = self.headers.get("Range")
        if rng and ext == ".mp4":
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            a = int(m.group(1)) if m and m.group(1) else 0
            b = int(m.group(2)) if m and m.group(2) else size - 1
            b = min(b, size - 1)
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(b - a + 1))
            self.end_headers()
            with open(f, "rb") as fh:
                fh.seek(a); left = b - a + 1
                while left > 0:
                    chunk = fh.read(min(1 << 18, left))
                    if not chunk: break
                    self.wfile.write(chunk); left -= len(chunk)
        else:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(size))
            self.end_headers()
            with open(f, "rb") as fh:
                while True:
                    chunk = fh.read(1 << 18)
                    if not chunk: break
                    self.wfile.write(chunk)

if __name__ == "__main__":
    print(f"serving {ROOT} on 0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
