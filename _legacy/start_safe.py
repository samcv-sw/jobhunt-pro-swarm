import traceback
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

def run():
    try:
        # 1. Redirect to start_cloud.py if available (recommended cloud entry point)
        if os.path.exists("start_cloud.py"):
            print("Redirecting to start_cloud.py...")
            os.execvp(sys.executable, [sys.executable, "start_cloud.py"])
            
        import uvicorn
        import web.app_v2
        
        port = int(os.getenv("PORT", "10000"))
        print(f"Imports successful. Starting uvicorn normally with app_v2 on port {port}...")
        os.execvp("uvicorn", ["uvicorn", "web.app_v2:app", "--host", "0.0.0.0", "--port", str(port)])
    except Exception as e:
        err = traceback.format_exc()
        print("FATAL ERROR:\n" + err)
        
        port = int(os.getenv("PORT", "10000"))
        class handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type','text/plain')
                self.end_headers()
                self.wfile.write(bytes(err, "utf8"))
                
        server_address = ('', port)
        httpd = HTTPServer(server_address, handler)
        print(f"Starting dummy HTTP server to serve error on port {port}...")
        httpd.serve_forever()

if __name__ == "__main__":
    run()
