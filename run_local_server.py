import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FORCE_SQLITE"] = "1"
os.environ["SKIP_INSTALL"] = "1"
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    print("====================================================================", flush=True)
    print(" 🔥 JobHunt Pro Local Engine v1 — Starting Server...", flush=True)
    print(" 🚀 Server Live URL: http://127.0.0.1:8000", flush=True)
    print(" 📊 Dashboard URL:   http://127.0.0.1:8000/user-dashboard", flush=True)
    print(" 🩺 Health Check:   http://127.0.0.1:8000/api/v2/health", flush=True)
    print("====================================================================", flush=True)

    import threading
    import webbrowser
    import socket

    _browser_opened = False

    def _open_browser_auto():
        global _browser_opened
        if _browser_opened:
            return
        import time
        for _ in range(40):
            time.sleep(0.3)
            try:
                with socket.create_connection(("127.0.0.1", 8000), timeout=0.5):
                    break
            except Exception:
                continue
        time.sleep(0.5)
        if not _browser_opened:
            _browser_opened = True
            try:
                webbrowser.open_new_tab('http://127.0.0.1:8000/user-dashboard')
            except Exception:
                pass

    threading.Thread(target=_open_browser_auto, daemon=True).start()

    import uvicorn
    uvicorn.run("web.app_v2:app", host="127.0.0.1", port=8000, log_level="warning", access_log=False, timeout_keep_alive=30, reload=False)

