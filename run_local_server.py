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

    import uvicorn
    uvicorn.run("web.app_v2:app", host="127.0.0.1", port=8000, log_level="info", reload=False)

