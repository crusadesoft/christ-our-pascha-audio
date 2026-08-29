# -*- coding: utf-8 -*-
"""Static server with HTTP Range support, so the browser can seek in the M4B.

Python's stock http.server ignores Range requests; the browser then reports
the media as unseekable (seekable.end(0) == 0) and click-to-seek silently
does nothing. This handler implements 206 Partial Content.
"""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)", rng)
        if not m:
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416); return None
        f = open(path, "rb"); f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, src, dst):
        if not hasattr(self, "_remaining"):
            return super().copyfile(src, dst)
        left = self._remaining
        while left > 0:
            chunk = src.read(min(64 * 1024, left))
            if not chunk:
                break
            try:
                dst.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                break
            left -= len(chunk)
        del self._remaining

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        SimpleHTTPRequestHandler.end_headers(self)

    def log_message(self, *a):
        pass

def lan_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))          # no packets sent; just picks a route
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    root = sys.argv[2] if len(sys.argv) > 2 else "out"
    # bind all interfaces so a phone on the same wi-fi can reach it
    host = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"
    os.chdir(root)
    print(f"serving {os.getcwd()}  (Range enabled)")
    print(f"  this machine : http://localhost:{port}/review.html")
    ip = lan_ip()
    if ip and host == "0.0.0.0":
        print(f"  phone/tablet : http://{ip}:{port}/review.html")
    ThreadingHTTPServer((host, port), RangeHandler).serve_forever()
