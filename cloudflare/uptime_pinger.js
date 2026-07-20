export default {
  async scheduled(event, env, ctx) {
    const urls = [
      "https://jhfguf.pythonanywhere.com/health",
      "https://jhfguf.pythonanywhere.com/api/v1/health"
    ];
    for (const url of urls) {
      try {
        const response = await fetch(url, {
          headers: {
            "User-Agent": "JobHuntPro-Uptime-Pinger/1.0"
          }
        });
        console.log(`Pinged ${url}: Status ${response.status}`);
      } catch (error) {
        console.error(`Failed to ping ${url}:`, error);
      }
    }
  }
};
