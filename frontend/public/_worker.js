export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    const BACKEND_URL = (typeof env !== 'undefined' && env.BACKEND_URL) || 'https://jobhunt-pro.onrender.com';
    const PROXY_PATHS = ['/api/', '/ws/', '/_/pa/', '/scrape', '/health'];

    if (PROXY_PATHS.some(p => path.startsWith(p))) {
      // Build backend target URL
      const targetUrl = new URL(path + url.search, BACKEND_URL);

      // Support WebSocket handshakes by matching protocol
      let targetUrlStr = targetUrl.toString();
      const isWebSocket = request.headers.get('Upgrade') === 'websocket';
      if (isWebSocket) {
        targetUrlStr = targetUrlStr.replace(/^http/, 'ws');
      }

      // Copy headers from request
      const headers = new Headers(request.headers);
      
      // Crucial: Set Host header to match backend host.
      // Otherwise, backend hosting providers like PythonAnywhere will reject the request (since they use Host-based routing).
      headers.set('Host', targetUrl.host);

      const hasBody = !['GET', 'HEAD'].includes(request.method);

      try {
        const response = await fetch(targetUrlStr, {
          method: request.method,
          headers: headers,
          body: hasBody ? request.body : null,
          redirect: 'manual'
        });
        return response;
      } catch (e) {
        return new Response(JSON.stringify({ error: 'Backend unreachable via Cloudflare Pages Function Proxy', detail: e.message }), {
          status: 502,
          headers: { 'Content-Type': 'application/json' },
        });
      }
    }

    // Default to serving static assets from the pages site
    try {
      return await env.ASSETS.fetch(request);
    } catch (e) {
      return new Response('Not Found', { status: 404 });
    }
  }
};
