// JobHunt Pro — Cloudflare Pages Function (_worker.js)
// $0 — 100k req/day free. Routes: Pages static → Worker → PA → D1

const WORKER_URL = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev';

const PROXY_PATHS = ['/api/', '/_/pa/', '/scrape', '/health'];

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

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
        const contentType = resp.headers.get('Content-Type') || 'application/json';
        if (resp.headers.get('Content-Length') === '0') {
          return new Response(null, { status: resp.status, headers: corsHeaders });
        }
        const text = await resp.text();
        return new Response(text, {
          status: resp.status,
          headers: { ...corsHeaders, 'Content-Type': contentType },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: 'Worker unreachable', detail: e.message }), {
          status: 502,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // Serve static files
    try {
      if (path === '/' || !path.includes('.')) {
        const indexResp = await env.ASSETS.fetch(request);
        return new Response(await indexResp.text(), {
          status: 200,
          headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=60' },
        });
      }
      return env.ASSETS.fetch(request);
    } catch (e) {
      return new Response('Not Found', { status: 404 });
    }
  },
};
