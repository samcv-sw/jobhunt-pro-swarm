import os, sys, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler

class FastHealthCheck(BaseHTTPRequestHandler):
    """Responds immediately on port 10000 while uvicorn starts in background."""
    def do_GET(self):
        if self.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"immortal"}')
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), FastHealthCheck)
    # Start in a separate thread so uvicorn can take over port later
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    # Give health server time to bind, then start uvicorn
    time.sleep(1)
    # Stop health server and start uvicorn
    server.shutdown()

if __name__ == "__main__":
    start_health_server()
    # After health server shuts down, start uvicorn
    import uvicorn
    uvicorn.run("web.app_v2:app", host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
