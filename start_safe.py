import traceback
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

def run():
    try:
        import uvicorn
        import web.app_v2
        
        print("Imports successful. Starting uvicorn normally...")
        os.execvp("uvicorn", ["uvicorn", "web.app_v2:app", "--host", "0.0.0.0", "--port", "10000"])
    except Exception as e:
        err = traceback.format_exc()
        print("FATAL ERROR:\n" + err)
        
        class handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type','text/plain')
                self.end_headers()
                self.wfile.write(bytes(err, "utf8"))
                
        server_address = ('', 10000)
        httpd = HTTPServer(server_address, handler)
        print("Starting dummy HTTP server to serve error on port 10000...")
        httpd.serve_forever()

if __name__ == "__main__":
    run()
