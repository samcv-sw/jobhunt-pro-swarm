# Cloudflare Pages Proxy Configuration Analysis

## 1. Observation

During the exploration of the codebase, we examined the following configurations and code segments:

1. **`cloudflare/pages/_worker.js`**:
   The current Cloudflare Pages function code includes:
   ```javascript
   // cloudflare/pages/_worker.js (Lines 4-13)
   const WORKER_URL = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev';
   const PROXY_PATHS = ['/api/', '/_/pa/', '/scrape', '/health'];
   const corsHeaders = {
     'Access-Control-Allow-Origin': '*',
     'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
     'Access-Control-Allow-Headers': 'Content-Type, Authorization',
     'Access-Control-Max-Age': '86400',
   };
   ```
   And the proxy fetch implementation:
   ```javascript
   // cloudflare/pages/_worker.js (Lines 24-36)
   // Proxy API calls to Worker
   if (PROXY_PATHS.some(p => path.startsWith(p))) {
     const targetUrl = `${WORKER_URL}${path}${url.search}`;
     try {
       const resp = await fetch(targetUrl, {
         method: request.method,
         headers: {
           'User-Agent': 'JobHuntPro-PagesFunction/1.0',
           'Accept': 'application/json',
         },
         body: request.body,
         // Cloudflare forwards Content-Type header automatically with body
       });
   ```

2. **`deploy/cloudflare-pages.toml`**:
   Contains build configuration and sets the production API URL environment variable for the build stage:
   ```toml
   # deploy/cloudflare-pages.toml (Lines 35-38)
   [context.production.environment]
     NODE_ENV             = "production"
     # Point to your Koyeb backend URL (set this as a Pages secret too)
     NEXT_PUBLIC_API_URL  = "https://your-app.koyeb.app"
   ```

3. **Backend Routing and Frontend Requests**:
   - The FastAPI backend router in `backend/main.py` defines multiple `/api/v1/` endpoints and a WebSocket path:
     - `GET /api/v1/health` (Line 327)
     - `POST /api/v1/scrape` (Line 559)
     - `@app.websocket("/ws/war-room")` (Line 718)
   - The monolithic web router in `web/routers/api_v2.py` exposes v2 endpoints:
     - `@router.get("/api/v2/stats")` (Line 175)
   - The frontend application in `frontend/src/app/page.tsx` directly communicates with these paths:
     - `const res = await fetch("/api/v2/stats");` (Line 43)
     - `ws = new WebSocket(`${protocol}//${host}/api/v1/ws`);` (Line 75)

4. **Cloudflare Pages Routing Rules**:
   - If a `_worker.js` file is output into the publish directory (`frontend/out/`), it completely overrides and ignores `_redirects` and `_headers` rules in Cloudflare Pages.

---

## 2. Logic Chain

The reasoning links our observations to the recommended solution:

1. **Routing Requirements (Frontend → Backend)**:
   The frontend makes calls to `/api/v2/...` and `/api/v1/...` relative paths. These must be forwarded to the FastAPI backend hosting these paths (e.g. `https://your-app.koyeb.app`).
2. **Workers/Pages Priority Rules**:
   Since the codebase already packages a custom `_worker.js` to serve static pages and run edge routing, any attempts to write custom rules in `_redirects` or `_headers` will be ignored by Cloudflare Pages when built.
3. **HTTP vs. WebSocket Proxying**:
   - *Option A (_redirects)*: A simple proxy rule like `/api/* https://your-app.koyeb.app/api/:splat 200` in `_redirects` works for simple HTTP queries, but completely fails for WebSockets (such as `/ws/war-room` or `/api/v1/ws`), because Cloudflare Pages redirects do not support WebSocket handshake upgrades (`101 Switching Protocols`).
   - *Option B (Custom `_worker.js`)*: Modifying the `_worker.js` to route requests enables complete control. Since it behaves as a full Cloudflare Worker, it natively supports WebSocket upgrades and preserves headers.
4. **Header and Body Forwarding**:
   The current `_worker.js` drops request headers (except User-Agent and Accept) and passes `request.body` on all requests. For proper proxying:
   - Request headers (like `Authorization`, `Content-Type`, and cookies) must be forwarded so authentication (`verify_jwt`) works on the backend.
   - For `GET`/`HEAD` requests, `request.body` must not be attached to the proxy `fetch` payload to avoid execution errors.
5. **Dynamic Target API URL**:
   Instead of hardcoding a target worker url (`https://jobhunt-pro-router.samsalameh-cv.workers.dev`), the target URL should be dynamically configured using the `NEXT_PUBLIC_API_URL` environment variable bound to the Cloudflare Pages Function.

---

## 3. Caveats

- **Environment Variables configuration**: Environment variables under `[context.production.environment]` in `cloudflare-pages.toml` are only injected into the *build* environment of Next.js. To access `NEXT_PUBLIC_API_URL` at runtime inside `_worker.js`, the variable must be set in the **Cloudflare Pages Dashboard** (under Settings → Environment Variables) or under `[vars]` in Wrangler.
- **WebSocket path consistency**: The frontend connects to `/api/v1/ws` whereas the backend listening endpoint in `backend/main.py` is `/ws/war-room`. Ensure that the paths match or that the proxy maps the incoming websocket path correctly.

---

## 4. Conclusion & Recommendation

We recommend using **Option B (Enhanced `_worker.js` Pages Function)** as it provides complete control over header forwarding, request method handling, and WebSocket support.

### Proposed Code for `cloudflare/pages/_worker.js`

Here is the recommended copy-paste-ready implementation for `_worker.js`:

```javascript
// JobHunt Pro — Cloudflare Pages Function (_worker.js)
// Proxies all /api/* and /ws/* requests to the FastAPI backend while serving static files correctly.

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // 1. Determine Backend URL (fallback to hardcoded value if env is not configured)
    const backendUrl = env.NEXT_PUBLIC_API_URL || 'https://your-app.koyeb.app';
    const targetUrl = new URL(path + url.search, backendUrl).toString();

    // 2. CORS Preflight Handler
    const corsHeaders = {
      'Access-Control-Allow-Origin': request.headers.get('Origin') || '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
      'Access-Control-Allow-Headers': request.headers.get('Access-Control-Request-Headers') || 'Content-Type, Authorization, X-Requested-With',
      'Access-Control-Allow-Credentials': 'true',
      'Access-Control-Max-Age': '86400',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // 3. Define Proxy Paths
    const PROXY_PATHS = ['/api/', '/ws/', '/_/pa/', '/scrape', '/health'];

    if (PROXY_PATHS.some(p => path.startsWith(p))) {
      // Create a forwardable header map
      const headers = new Headers(request.headers);
      
      // Prevent host conflicts on destination server
      headers.delete('Host'); 
      headers.set('X-Forwarded-Host', url.host);
      headers.set('X-Forwarded-Proto', url.protocol.replace(':', ''));

      // Check if this is a WebSocket Upgrade request
      const isWebSocket = request.headers.get('Upgrade') === 'websocket';

      try {
        const fetchOptions = {
          method: request.method,
          headers: headers,
          redirect: 'manual',
        };

        // Forward request body only for writing methods (to prevent GET/HEAD fetch errors)
        if (request.method !== 'GET' && request.method !== 'HEAD') {
          fetchOptions.body = request.body;
        }

        const resp = await fetch(targetUrl, fetchOptions);

        // Handle WebSocket handshake responses
        if (isWebSocket && resp.status === 101) {
          return resp;
        }

        // Forward normal HTTP responses with CORS headers appended
        const newHeaders = new Headers(resp.headers);
        for (const [key, value] of Object.entries(corsHeaders)) {
          newHeaders.set(key, value);
        }

        return new Response(resp.body, {
          status: resp.status,
          statusText: resp.statusText,
          headers: newHeaders,
        });

      } catch (e) {
        return new Response(
          JSON.stringify({ error: 'Backend gateway unreachable', detail: e.message }),
          {
            status: 502,
            headers: {
              ...corsHeaders,
              'Content-Type': 'application/json',
            },
          }
        );
      }
    }

    // 4. Serve Static Files fallback (Next.js export output)
    try {
      // Fallback index.html mapping for client-side routing
      if (path === '/' || !path.includes('.')) {
        const indexResp = await env.ASSETS.fetch(request);
        const indexText = await indexResp.text();
        return new Response(indexText, {
          status: 200,
          headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'public, max-age=60',
          },
        });
      }
      return env.ASSETS.fetch(request);
    } catch (e) {
      return new Response('Static Asset Not Found', { status: 404 });
    }
  },
};
```

---

## 5. Verification Method

To verify the configuration locally and post-deployment:

1. **Local Emulator Testing**:
   Ensure you copy the updated `_worker.js` file into your built output directory (`frontend/out/`), then run Wrangler Pages local emulator:
   ```bash
   npx wrangler pages dev frontend/out --binding NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
2. **API Verification Request**:
   Send a GET request to `http://localhost:8788/api/v2/stats` (default Wrangler port) and verify it returns correct database statistics from your running backend at `http://localhost:8000`.
3. **WebSocket Verification**:
   Inspect the browser developer console on load and verify that WebSocket handshake at `/api/v1/ws` upgrades successfully without returns of `502` or CORS origin violations.
