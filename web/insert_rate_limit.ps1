$file = "C:\Users\samde\Desktop\cv sam new ma3 kimi\web\app_v2.py"
$content = Get-Content $file -Raw
$lines = $content -split '\r?\n'

$rateLimitCode = @'
# --- Rate Limiting Middleware ---
# Global in-memory rate limiter for all HTTP routes.
# Health endpoints and static files are excluded.
from time import time as _rl_time
_global_rate_limits = {}

@app.middleware("http")
async def global_rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for health checks and static files
    path = request.url.path
    if path.startswith("/static") or path.startswith("/health") or path.startswith("/api/v1/health"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = _rl_time()
    if client_ip not in _global_rate_limits:
        _global_rate_limits[client_ip] = []
    _global_rate_limits[client_ip] = [t for t in _global_rate_limits[client_ip] if now - t < 60]

    # 120 req/min for regular pages, 180 req/min for API routes
    limit = 180 if path.startswith("/api") else 120
    if len(_global_rate_limits[client_ip]) >= limit:
        return JSONResponse(
            {"error": "rate_limited", "message": "Too many requests. Please slow down."},
            status_code=429
        )
    _global_rate_limits[client_ip].append(now)

    # Periodically purge old entries to prevent memory leak
    if len(_global_rate_limits) > 5000:
        stale = [ip for ip, ts_list in _global_rate_limits.items() if not [t for t in ts_list if now - t < 60]]
        for ip in stale:
            del _global_rate_limits[ip]

    return await call_next(request)

'@

# Find line index of "import re as _csrf_re" (0-based)
$insertIdx = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq "import re as _csrf_re") {
        $insertIdx = $i
        break
    }
}

if ($insertIdx -ge 0) {
    $newLines = $lines[0..($insertIdx-1)] + $rateLimitCode + "" + $lines[$insertIdx..($lines.Count-1)]
    $newContent = $newLines -join "`r`n"
    Set-Content -Path $file -Value $newContent -Encoding UTF8 -NoNewline
    Write-Output "Inserted rate limit middleware before line $($insertIdx+1)"
} else {
    Write-Output "ERROR: Could not find import re as _csrf_re"
}
