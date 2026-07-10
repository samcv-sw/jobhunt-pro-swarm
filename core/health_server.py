import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs


def start_health_server():
    port = int(os.environ.get("HEALTH_PORT", 9999))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.debug(f"Health check server running on port {port}")
    server.serve_forever()


def run_in_background():
    t = threading.Thread(target=start_health_server, daemon=True)
    t.start()
