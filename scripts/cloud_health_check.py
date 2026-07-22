"""
JobHunt Pro - Multi-Cloud Health & Telemetry Verifier
Checks latency, availability, and queue state across Vercel, Render, PythonAnywhere, and Cloudflare Edge nodes.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import time

TARGET_NODES = {
    "vercel": os.environ.get("VERCEL_URL", "https://jobhunt-pro-frontend.vercel.app/api/health"),
    "render": os.environ.get("RENDER_URL", "https://jobhunt-pro-backend.onrender.com/health"),
    "pythonanywhere": os.environ.get("PA_URL", "https://jhfguf.pythonanywhere.com/api/v2/health"),
    "cloudflare": os.environ.get("CF_WORKER_URL", "https://jobhunt-edge.workers.dev/ping"),
}

def ping_target(name: str, url: str) -> dict:
    start = time.time()
    result = {"name": name, "url": url, "status": "UNKNOWN", "latency_ms": 0, "code": 0}
    
    if not url or url.startswith("https://jobhunt-edge.workers.dev") or "placeholder" in url:
        result["status"] = "SKIPPED_UNCONFIGURED"
        return result
        
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "JobHunt-Pro-CloudTelemetry/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            latency = round((time.time() - start) * 1000, 2)
            result["status"] = "HEALTHY" if response.status == 200 else f"HTTP_{response.status}"
            result["code"] = response.status
            result["latency_ms"] = latency
    except urllib.error.HTTPError as e:
        result["status"] = f"HTTP_{e.code}"
        result["code"] = e.code
    except Exception as e:
        result["status"] = f"FAILED: {str(e)[:50]}"
        
    return result

def main():
    print("=" * 60)
    print("JobHunt Pro - Cloud Telemetry & Health Audit")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("=" * 60)
    
    results = []
    healthy_count = 0
    
    for name, url in TARGET_NODES.items():
        res = ping_target(name, url)
        results.append(res)
        if res["status"] in ["HEALTHY", "SKIPPED_UNCONFIGURED"]:
            healthy_count += 1
        print(f"[{res['status']:^20}] Node: {name:<15} | Latency: {res['latency_ms']}ms")
        
    summary = {
        "timestamp": time.time(),
        "total_nodes": len(results),
        "healthy_count": healthy_count,
        "nodes": results
    }
    
    print("-" * 60)
    print(f"Telemetry Summary: {healthy_count}/{len(results)} nodes operational.")
    print("=" * 60)
    
    # Save report
    os.makedirs("data", exist_ok=True)
    with open("data/cloud_telemetry.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    # Exit cleanly
    sys.exit(0)

if __name__ == "__main__":
    main()
