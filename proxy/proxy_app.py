import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import uvicorn

app = FastAPI()

HF_TOKEN = os.getenv("HF_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "https://sam907-jobhunt-backend.hf.space")

client = httpx.AsyncClient(timeout=60.0)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(request: Request, path: str):
    url = f"{BACKEND_URL}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
        
    body = await request.body()
    
    req = client.build_request(
        method=request.method,
        url=url,
        headers=headers,
        content=body
    )
    
    res = await client.send(req, stream=True)
    
    response_headers = dict(res.headers)
    for h in ["content-encoding", "content-length", "transfer-encoding"]:
        response_headers.pop(h, None)
        
    return StreamingResponse(
        res.aiter_raw(),
        status_code=res.status_code,
        headers=response_headers,
        background=res.aclose
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
