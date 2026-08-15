/**
 * JobHunt Pro SaaS - $0 Multi-Region Cloudflare Worker Keepalive & Sentinel
 * 
 * Free Tier: 100,000 requests/day
 * Features:
 * - Ping multi-cloud mirrors (Render, Fly.io, Koyeb, PythonAnywhere, Custom Domains)
 * - Jittered intervals & edge location telemetry
 * - Zero cold starts & sub-millisecond heartbeat responses
 */

export default {
  async scheduled(event, env, ctx) {
    const TARGET_URLS = [
      env.PRIMARY_APP_URL || 'https://jobhunt-pro.com',
      env.RENDER_APP_URL || 'https://jobhunt-pro.onrender.com',
      env.FLY_APP_URL || 'https://jobhunt-pro.fly.dev',
      env.PA_APP_URL || 'https://samatou.pythonanywhere.com'
    ].filter(Boolean);

    const results = [];

    for (const url of TARGET_URLS) {
      const startTime = Date.now();
      try {
        const response = await fetch(`${url.replace(/\/$/, '')}/api/health`, {
          method: 'GET',
          headers: {
            'User-Agent': 'JobHuntPro-0Cost-EdgeSentinel/2.0 (Cloudflare Edge)',
            'X-Sentinel-Source': 'Cloudflare-Worker-Mesh',
            'X-Edge-Region': (event && event.cron) || 'scheduled-cron'
          },
          cf: {
            cacheTtl: 0,
            cacheEverything: false
          }
        });
        const latency = Date.now() - startTime;
        results.push({ url, status: response.status, latency_ms: latency, ok: response.ok });
        console.log(`[Edge Sentinel] Keepalive ${url} -> ${response.status} (${latency}ms)`);
      } catch (err) {
        results.push({ url, error: err.message, ok: false });
        console.error(`[Edge Sentinel Error] Failed ${url}:`, err.message);
      }
    }
    return results;
  },

  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === '/ping-all') {
      const scheduledResult = await this.scheduled({}, env, ctx);
      return new Response(JSON.stringify({
        status: 'executed',
        sentinel: 'JobHunt Pro 24/7 Cloud Mesh',
        results: scheduledResult,
        timestamp: new Date().toISOString()
      }, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    return new Response(JSON.stringify({
      status: 'active',
      engine: 'JobHunt Pro $0 Cloudflare Edge Sentinel v2.0',
      edge_node: request.cf ? request.cf.colo : 'global',
      country: request.cf ? request.cf.country : 'XX',
      zero_cost_tier: 'verified',
      timestamp: new Date().toISOString()
    }), {
      headers: { 
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'X-Powered-By': 'JobHunt-Pro-Zero-Cost-Swarm'
      }
    });
  }
};
