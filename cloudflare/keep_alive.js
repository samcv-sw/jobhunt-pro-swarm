/**
 * Cloudflare Worker: 24/7 Keep-Alive Auto-Ping for JobHunt Pro SaaS
 * 
 * Schedule: */5 * * * * (runs every 5 minutes)
 * Purpose: Ping Render web backend, Vercel frontend, and trigger light DB queries to Neon.
 */

// Define target endpoints. Ensure no trailing slashes.
const TARGETS = [
  "https://jhfguf.pythonanywhere.com/api/v1/health", // PythonAnywhere main API health
  "https://jhfguf.pythonanywhere.com/api/v1/public/jobs", // Public job board route (triggers Neon/SQLite read)
  // Add Render service URL if dual-hosted:
  // "https://jobhunt-backend.onrender.com/api/v1/health"
];

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(handleScheduled(event));
  },
  
  async fetch(request, env, ctx) {
    // Allows manual trigger via HTTP request for verification
    const url = new URL(request.url);
    if (url.pathname === "/trigger") {
      const results = await handleScheduled(null);
      return new Response(JSON.stringify(results), {
        headers: { "Content-Type": "application/json" }
      });
    }
    return new Response("JobHunt Pro Keep-Alive Worker Active.", { status: 200 });
  }
};

async function handleScheduled(event) {
  const timestamp = new Date().toISOString();
  console.log(`[Keep-Alive] Triggered cron run at ${timestamp}`);
  
  const results = [];
  
  for (const url of TARGETS) {
    try {
      const start = Date.now();
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "User-Agent": "JobHuntPro-KeepAlive-Bot/1.0 (+https://cloudflare.com)",
          "Cache-Control": "no-cache"
        },
        // Timeout after 15 seconds
        signal: AbortSignal.timeout(15000)
      });
      
      const duration = Date.now() - start;
      const status = response.status;
      
      console.log(`[Keep-Alive] Pinged ${url} - Status: ${status} - Duration: ${duration}ms`);
      results.push({ url, success: true, status, duration });
    } catch (error) {
      console.error(`[Keep-Alive] Failed to ping ${url}: ${error.message || error}`);
      results.push({ url, success: false, error: error.message || String(error) });
    }
  }
  
  return results;
}
