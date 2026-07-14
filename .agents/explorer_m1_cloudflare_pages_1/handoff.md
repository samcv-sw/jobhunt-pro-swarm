# Next.js Static HTML Export Analysis and Migration Plan

## 1. Observation

Direct observations from codebase inspection:

1. **Next.js Config (`frontend/next.config.ts`)**:
   Lines 10-18:
   ```typescript
   // Comment out output: "export" to deploy to Vercel and use full Next.js SSR & Image Optimization
   // output: "export",
   trailingSlash: true,
   images: {
     // Enable WebP & AVIF for smaller image sizes on supported browsers
     formats: ['image/avif', 'image/webp'],
     unoptimized: false,
   },
   ```

2. **Next.js Package Scripts (`frontend/package.json`)**:
   Lines 5-10:
   ```json
   "scripts": {
     "dev": "next dev",
     "build": "node node_modules/next/dist/bin/next build --webpack",
     "start": "next start",
     "lint": "node node_modules/eslint/bin/eslint.js ."
   },
   ```

3. **Relative Fetch API Requests (`frontend/src/app/page.tsx`)**:
   Line 43:
   ```typescript
   const res = await fetch("/api/v2/stats");
   ```

4. **WebSocket Connection Endpoint (`frontend/src/app/page.tsx`)**:
   Lines 70-75:
   ```typescript
   const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
   const host = process.env.NEXT_PUBLIC_API_URL 
     ? new URL(process.env.NEXT_PUBLIC_API_URL).host 
     : window.location.host;
   
   ws = new WebSocket(`${protocol}//${host}/api/v1/ws`);
   ```

5. **FastAPI CORS Configurations (`backend/main.py`)**:
   Lines 237-255:
   ```python
   allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
   if allowed_origins_env:
       origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
   else:
       # Safe defaults for local development
       origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
   ...
   if os.getenv("ENV") == "production" or allowed_origins_env or _has_wildcard_pattern:
       app.add_middleware(
           SecureCORSMiddleware,
           allowed_patterns=origins,
           allow_credentials=True,
       )
   ```

---

## 2. Logic Chain

1. **Uncommenting `output: "export"`**:
   Uncommenting `output: "export"` directs Next.js to produce static assets (`.html`, `.css`, `.js`, media) in the `out/` directory.

2. **Image Optimization Error**:
   Next.js Image Optimization service is a server-side feature running on Node.js. If `output: "export"` is enabled and `images.unoptimized` is `false`, Next.js build fails with:
   `Error: Image Optimization using the default loader is not compatible with { output: 'export' }.`
   To prevent build failure, `images.unoptimized` must be changed to `true`.

3. **Broken Relative `/api/*` Routes in Static Export**:
   Since static export has no running Node.js middleware or server-side redirects, relative requests to `/api/v2/stats` will resolve against the static host domain (e.g. Cloudflare Pages) and return a 404.
   
4. **Proxy Routing Options**:
   * **Option A (Direct Client-Side CORS - Recommended)**:
     By appending the environment variable `process.env.NEXT_PUBLIC_API_URL` to fetches (similar to how the WebSocket is already configured), client-side queries target the backend domain directly (e.g. Render or PythonAnywhere).
     Because `SecureCORSMiddleware` handles origin checking, we only need to add the static app's origin domain to the backend's `ALLOWED_ORIGINS` (e.g., `https://*.pages.dev` or custom domain) to handle CORS properly.
   * **Option B (Edge Redirects via `_redirects`)**:
     A `_redirects` file can be placed in `public/_redirects`. During export, Next.js copies the public folder contents directly to `out/_redirects`.
     An entry `/api/* https://jobhunt-pro-swarm.onrender.com/api/:splat 200` enables Cloudflare Pages to proxy regular HTTP requests directly to the FastAPI server at the Edge.
     *Caveat*: WebSockets cannot be routed via Pages `200` proxy rules, meaning they must still query `process.env.NEXT_PUBLIC_API_URL` directly.

---

## 3. Caveats

1. **WebSockets and Cloudflare Page Proxy Limits**:
   Cloudflare Pages `200` rewrite proxying in the `_redirects` configuration does NOT support WebSockets. The client code must connect to the WebSocket endpoint using its absolute domain. Fortunately, `frontend/src/app/page.tsx` is already structured to extract hostnames from `NEXT_PUBLIC_API_URL`.
2. **Next-PWA Static Compatibility**:
   PWA generation relies on service worker assets. The build command copies `public/sw.js` and `public/workbox-*.js` into `out/`. Any changes in build scripts must verify these service worker assets compile correctly in static modes.
3. **Subfolder Deployments**:
   If the static build is hosted on a subdirectory path (e.g., `domain.com/subpath/`), `assetPrefix` and routing parameters in `next.config.ts` must be adjusted. This report assumes root-level deployment (e.g., standard `*.pages.dev` root deployment).

---

## 4. Conclusion

To successfully enable Next.js static HTML export without breaking features, implement the following four-step plan:

### Step 1: Update Next.js Configuration
Uncomment `output: "export"` and set `images.unoptimized` to `true` in `frontend/next.config.ts` to satisfy build-time constraints:
```typescript
// Proposed changes in frontend/next.config.ts
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    formats: ['image/avif', 'image/webp'],
    unoptimized: true, // Must be true for output: "export"
  },
};
```

### Step 2: Ensure API Calls Prepend the Base API URL
Modify client-side fetch calls in the frontend (such as `frontend/src/app/page.tsx`) to prepend `process.env.NEXT_PUBLIC_API_URL`:
```typescript
// Before
const res = await fetch("/api/v2/stats");

// After
const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
const res = await fetch(`${apiBase}/api/v2/stats`);
```

### Step 3: Configure FastAPI Backend CORS Origins
In the FastAPI production environment variables, ensure `ALLOWED_ORIGINS` authorizes the Cloudflare Pages subdomain patterns:
```env
ALLOWED_ORIGINS=https://*.pages.dev,https://your-custom-domain.com,http://localhost:3000
```
This enables the dynamic `SecureCORSMiddleware` in `backend/main.py` to allow cross-origin requests.

### Step 4: (Optional) Establish Edge Routing / Fallback Proxy
Create a redirect configuration in `frontend/public/_redirects` to proxy `/api/*` requests on the Edge:
```text
/api/* https://jobhunt-pro-swarm.onrender.com/api/:splat 200
```
*Note: This is optional if client-side fetches have been refactored to absolute URLs (Step 2).*

---

## 5. Verification Method

To verify the setup:

1. **Locally run the static export build**:
   ```bash
   cd frontend
   npm run build
   ```
   Check that it builds successfully without throwing the image optimization loader error, and outputs files into the `out/` directory.

2. **Verify files in `out/`**:
   Check if the `out/index.html`, `out/dashboard/index.html` (or `out/dashboard.html`), `out/_redirects` (if created), `out/sw.js` and CSS/JS assets exist.

3. **Local HTTP Server test**:
   Serve the `out/` directory locally (e.g. `npx serve out`) and verify that the page renders and loads properly.
   Run tests using the project test suite if present (e.g., `npm run test` or client-side checks) to ensure standard routes render.
