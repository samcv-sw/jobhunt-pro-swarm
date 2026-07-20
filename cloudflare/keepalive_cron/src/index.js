export default {
  async scheduled(event, env, ctx) {
    const urls = [
      env.APP_URL || 'https://jobhunt-pro.onrender.com/',
      env.ENGINE_URL || 'https://jobhunt-pro-engine.onrender.com/'
    ];

    const pingPromises = urls.map(async (url) => {
      try {
        console.log(`Pinging: ${url}`);
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'User-Agent': 'Cloudflare-Worker-KeepAlive-Cron'
          }
        });
        console.log(`Pinged ${url} - Status: ${response.status}`);
      } catch (err) {
        console.error(`Error pinging ${url}: ${err.message}`);
      }
    });

    ctx.waitUntil(Promise.all(pingPromises));
  },

  async fetch(request, env, ctx) {
    const urls = [
      env.APP_URL || 'https://jobhunt-pro.onrender.com/',
      env.ENGINE_URL || 'https://jobhunt-pro-engine.onrender.com/'
    ];

    const results = [];
    for (const url of urls) {
      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'User-Agent': 'Cloudflare-Worker-KeepAlive-Cron'
          }
        });
        results.push({ url, status: response.status });
      } catch (err) {
        results.push({ url, error: err.message });
      }
    }
    return new Response(JSON.stringify(results, null, 2), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
};
