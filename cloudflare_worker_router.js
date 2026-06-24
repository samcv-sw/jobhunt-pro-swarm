/**
 * OMEGA ROUTER — Cloudflare Worker (Hydra Architecture)
 * 
 * Balances traffic and handles automatic fallbacks for free-tier cloud deployments.
 * Primary: Hugging Face Spaces (16GB RAM)
 * Fallback: Koyeb / Render
 *
 * Deploy: Copy this into https://workers.cloudflare.com
 */

export default {
  async fetch(request, env, ctx) {
    const paBase = (env && env.PA_BASE) || "https://jhfguf.pythonanywhere.com";
    const flyBase = (env && env.FLY_BASE) || "https://jobhunt-pro.fly.dev";
    const zeaburBase = (env && env.ZEABUR_BASE) || "https://jobhunt-pro.zeabur.app";
    const renderBase = (env && env.RENDER_BASE) || "https://jobhunt-pro.onrender.com";

    const BACKENDS = [
      paBase,
      flyBase,
      zeaburBase,
      renderBase
    ];
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

    // 2. Try backends in order of priority (Fallback mechanism)
    let lastErr = null;
    for (const backend of BACKENDS) {
      const targetUrl = new URL(url.pathname + url.search, backend);
      try {
        let response = await fetch(targetUrl, {
          method: request.method,
          headers: request.headers,
          body: request.body
        });
        
        // If the backend returns a 502/503 (sleeping or offline), try the next one
        if (response.status === 502 || response.status === 503) {
          lastErr = `Backend ${backend} returned ${response.status}`;
          continue; 
        }

        response = new Response(response.body, response);
        for (const [key, value] of Object.entries(corsHeaders)) {
          response.headers.set(key, value);
        }
        return response;
      } catch (err) {
        lastErr = err.message;
        // Continue to next backend on network error
      }
    }

    // 3. If all backends fail
    return new Response(JSON.stringify({ 
      error: "All Hydra backends offline or sleeping", 
      detail: lastErr
    }), {
      status: 502,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
};
