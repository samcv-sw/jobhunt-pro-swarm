// JobHunt Pro — Cloudflare Pages Function (_worker.js)
// Serves static frontend + proxies API calls to the Worker
// $0 — 100k req/day

// ── Worker Backend ──
const WORKER_URL = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev';

// ── Routes that should go to the Worker ──
const PROXY_PATHS = ['/api/', '/_/pa/', '/scrape', '/health'];

// ── CORS ──
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // ── Route: API calls → Worker ──
    if (PROXY_PATHS.some(p => path.startsWith(p))) {
      const targetUrl = `${WORKER_URL}${path}${url.search}`;
      try {
        const resp = await fetch(targetUrl, {
          method: request.method,
          headers: {
            'User-Agent': 'JobHuntPro-PagesFunction/1.0',
            'Accept': 'application/json',
            'Content-Type': request.headers.get('Content-Type') || 'application/json',
            ...(request.headers.get('Authorization') ? { 'Authorization': request.headers.get('Authorization') } : {}),
          },
          body: ['GET', 'HEAD'].includes(request.method) ? null : await request.text(),
        });
        const text = await resp.text();
        return new Response(text, {
          status: resp.status,
          headers: { ...corsHeaders, ...Object.fromEntries(resp.headers) },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: 'Worker unreachable', detail: e.message }), {
          status: 502,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // ── Route: Static files → Serve index.html for SPA ──
    try {
      // For root or any non-file path, serve index.html
      if (path === '/' || !path.includes('.')) {
        const indexResp = await env.ASSETS.fetch(new URL('/index.html', url));
        return new Response(await indexResp.text(), {
          status: 200,
          headers: { 'Content-Type': 'text/html; charset=utf-8' },
        });
      }
      // For actual files (images, JS, CSS), serve directly
      return env.ASSETS.fetch(request);
    } catch (e) {
      return new Response('Not Found', { status: 404 });
    }
  },
};
