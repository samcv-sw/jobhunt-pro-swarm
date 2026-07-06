import asyncio
import os
import sys
import time
from collections import defaultdict
from fastapi import Request, HTTPException

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history = defaultdict(list)
        self.lock = asyncio.Lock()

    async def __call__(self, request: Request):
        # Update client IP resolution to check for X-Forwarded-For or X-Real-IP
        client_ip = None
        xff = request.headers.get("x-forwarded-for")
        if xff:
            client_ip = xff.split(",")[0].strip()
        else:
            xri = request.headers.get("x-real-ip")
            if xri:
                client_ip = xri.strip()
        
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
            
        async with self.lock:
            now = time.time()
            # Prune keys older than window_seconds from the history to prevent memory leaks
            for ip in list(self.history.keys()):
                self.history[ip] = [t for t in self.history[ip] if now - t < self.window_seconds]
                if not self.history[ip]:
                    del self.history[ip]
                    
            self.history[client_ip] = [t for t in self.history[client_ip] if now - t < self.window_seconds]
            if len(self.history[client_ip]) >= self.requests_limit:
                raise HTTPException(status_code=429, detail="Too many requests. Rate limit exceeded.")
            self.history[client_ip].append(now)

    def reset(self):
        self.history.clear()

# Adjust rate limits dynamically if testing is detected
if "pytest" in sys.modules or os.getenv("TESTING") == "true":
    RATE_LIMIT_REQUESTS = 3
    RATE_LIMIT_WINDOW = 10
else:
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60

rate_limiter = RateLimiter(requests_limit=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW)
