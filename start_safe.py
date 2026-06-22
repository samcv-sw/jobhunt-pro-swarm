import traceback
import os
import sys

def run():
    try:
        import uvicorn
        # Try importing the app to catch missing modules
        import web.app_v2
        
        print("Imports successful. Starting uvicorn normally...")
        # Replace the current process with uvicorn
        os.execvp("uvicorn", ["uvicorn", "web.app_v2:app", "--host", "0.0.0.0", "--port", "10000"])
    except Exception as e:
        err = traceback.format_exc()
        print("FATAL ERROR:\n" + err)
        with open("error.log", "w") as f:
            f.write(err)
        
        print("Starting dummy HTTP server to serve error.log on port 10000...")
        os.execvp("python", ["python", "-m", "http.server", "10000"])

if __name__ == "__main__":
    run()
