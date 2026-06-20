/**
 * OMEGA ROUTER — Cloudflare Worker
 * 
 * Balances traffic randomly across multiple free-tier cloud deployments.
 * This ensures no single provider hits their monthly limits, achieving "Infinite" scale for $0.
 *
 * Deploy: Copy this into https://workers.cloudflare.com
 */

// Your free tier backend URLs
const BACKENDS = [
  "https://jobhunt-pro.onrender.com",
  "https://jobhunt-railway.up.railway.app", // example
  "https://jobhunt-fly.fly.dev",            // example
];

export default {
  async fetch(request, env, ctx) {
    // 1. Handle CORS for Frontend API access
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };
    
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // 2. Select a random backend to spread load
    const randomBackend = BACKENDS[Math.floor(Math.random() * BACKENDS.length)];
    const targetUrl = new URL(url.pathname + url.search, randomBackend);

    try {
      // 3. Forward request
      let response = await fetch(targetUrl, {
        method: request.method,
        headers: request.headers,
        body: request.body
      });

      // 4. Copy response and inject CORS
      response = new Response(response.body, response);
      for (const [key, value] of Object.entries(corsHeaders)) {
        response.headers.set(key, value);
      }

      return response;

    } catch (err) {
      return new Response(JSON.stringify({ 
        error: "All backends offline or unreachable", 
        detail: err.message,
        tried: randomBackend
      }), {
        status: 502,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
  }
};
