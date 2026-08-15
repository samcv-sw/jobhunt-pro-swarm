export default {
  async scheduled(event, env, ctx) {
    const urls = [
      env.PRIMARY_URL || 'https://jobhunt-pro.onrender.com/ping',
      env.BACKEND_URL || 'https://jhfguf.pythonanywhere.com/ping',
      env.KOYEB_URL || 'https://jobhunt-pro-koyeb.koyeb.app/ping',
      env.APP_URL || 'https://jobhunt-pro.onrender.com/healthz',
      env.ENGINE_URL || 'https://jobhunt-pro-engine.onrender.com/ping'
    ];

    // Remove duplicates
    const uniqueUrls = [...new Set(urls)];

    const pingPromises = uniqueUrls.map(async (url) => {
      try {
        console.log(`[KeepAlive] Pinging: ${url}`);
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'User-Agent': 'Cloudflare-Worker-KeepAlive-Cron/2.0',
            'X-Probe-Source': 'cloudflare-sentinel'
          },
          signal: AbortSignal.timeout(10000)
        });
        console.log(`[KeepAlive] Pinged ${url} - Status: ${response.status}`);
      } catch (err) {
        console.error(`[KeepAlive] Error pinging ${url}: ${err.message}`);
      }
    });

    ctx.waitUntil(Promise.all(pingPromises));
  },

  async fetch(request, env, ctx) {
    const urls = [
      env.PRIMARY_URL || 'https://jobhunt-pro.onrender.com/ping',
      env.BACKEND_URL || 'https://jhfguf.pythonanywhere.com/ping',
      env.KOYEB_URL || 'https://jobhunt-pro-koyeb.koyeb.app/ping',
      env.APP_URL || 'https://jobhunt-pro.onrender.com/healthz',
      env.ENGINE_URL || 'https://jobhunt-pro-engine.onrender.com/ping'
    ];

    const uniqueUrls = [...new Set(urls)];
    const results = [];

    for (const url of uniqueUrls) {
      const startTime = Date.now();
      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'User-Agent': 'Cloudflare-Worker-KeepAlive-Cron/2.0',
            'X-Probe-Source': 'cloudflare-manual-trigger'
          },
          signal: AbortSignal.timeout(10000)
        });
        const latencyMs = Date.now() - startTime;
        results.push({
          url,
          status: response.status,
          ok: response.ok,
          latency_ms: latencyMs
        });
      } catch (err) {
        results.push({
          url,
          error: err.message,
          ok: false,
          latency_ms: Date.now() - startTime
        });
      }
    }

    return new Response(
      JSON.stringify(
        {
          timestamp: new Date().toISOString(),
          sentinel: "Cloudflare-Worker-KeepAlive-Cron/2.0",
          results
        },
        null,
        2
      ),
      {
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};
