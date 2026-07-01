/**
 * Cloudflare Worker for keeping Hugging Face Spaces awake 24/7.
 * Hugging Face Spaces go to sleep after a period of inactivity on the free tier.
 * By using Cloudflare Workers (which provides 100k free requests per day),
 * we can ping the spaces every 5-10 minutes to prevent them from sleeping.
 */

const TARGET_URLS = [
  "https://your-username-hydra-worker-1.hf.space",
  "https://your-username-hydra-worker-2.hf.space"
];

export default {
  // The scheduled event is triggered by Cloudflare's Cron Triggers
  async scheduled(event, env, ctx) {
    ctx.waitUntil(pingSpaces());
  },
  
  // Also allow manual triggering via HTTP request
  async fetch(request, env, ctx) {
    await pingSpaces();
    return new Response("Pinged all worker nodes successfully.");
  }
};

async function pingSpaces() {
  const promises = TARGET_URLS.map(async (url) => {
    try {
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "User-Agent": "Hydra-KeepAlive/1.0"
        }
      });
      console.log(`Pinged ${url} - Status: ${response.status}`);
    } catch (error) {
      console.error(`Failed to ping ${url}: ${error.message}`);
    }
  });

  await Promise.allSettled(promises);
}
