/**
 * JOB PROXY — Cloudflare Worker
 * 
 * Bypasses Indeed/Bayt/Gulftalent blocks by proxying through Cloudflare's IP range.
 * Cloudflare IPs are never blocked by job sites.
 * 
 * Deploy: Copy this entire file into https://workers.cloudflare.com
 * Free tier: 100,000 requests/day, $0
 */

// ── All job sources ──
const SOURCES = {
  indeed: {
    url: (q, l) => `https://www.indeed.com/rss?q=${encodeURIComponent(q)}&l=${encodeURIComponent(l)}&sort=date`,
    parse: (xml) => {
      const items = [];
      const regex = /<item>[\s\S]*?<\/item>/g;
      let match;
      while ((match = regex.exec(xml)) !== null) {
        const item = match[0];
        const title = (item.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>/) || item.match(/<title>(.*?)<\/title>/))?.[1] || '';
        const link = (item.match(/<link>(.*?)<\/link>/))?.[1] || '';
        const desc = (item.match(/<description><!\[CDATA\[(.*?)\]\]><\/description>/) || item.match(/<description>(.*?)<\/description>/))?.[1] || '';
        items.push({ title, url: link, description: desc, source: 'indeed' });
      }
      return items;
    }
  },
  
  indeed_search: {
    url: (q, l) => `https://www.indeed.com/rss?q=${encodeURIComponent(q)}&sort=date`,
    parse: (xml) => SOURCES.indeed.parse(xml)
  }
};

// ── Extract company + title from Indeed items ──
function extractMeta(item) {
  let company = '';
  let title = item.title || '';
  const dashPos = title.lastIndexOf(' - ');
  if (dashPos > 0) {
    company = title.substring(dashPos + 3).trim();
    title = title.substring(0, dashPos).trim();
  }
  return { title, company, url: item.url, source: item.source };
}

// ── HEADERS to look like a real browser ──
const BROWSER_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en-US,en;q=0.9',
  'Cache-Control': 'no-cache',
  'Pragma': 'no-cache'
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
    
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }
    
    // Route: /indeed/rss?q=...&l=...
    if (path.startsWith('/indeed')) {
      const q = url.searchParams.get('q') || 'network engineer';
      const l = url.searchParams.get('l') || '';
      const source = l ? SOURCES.indeed : SOURCES.indeed_search;
      const targetUrl = source.url(q, l);
      
      try {
        const resp = await fetch(targetUrl, { headers: BROWSER_HEADERS });
        if (!resp.ok) {
          // Fallback: try without location
          const fallbackUrl = SOURCES.indeed_search.url(q, l);
          const resp2 = await fetch(fallbackUrl, { headers: BROWSER_HEADERS });
          if (!resp2.ok) {
            return new Response(JSON.stringify({ error: `Source returned ${resp.status}`, jobs: [] }), {
              headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
          }
          const text = await resp2.text();
          const items = SOURCES.indeed_search.parse(text);
          const jobs = items.map(extractMeta);
          return new Response(JSON.stringify({ jobs, source: 'indeed_fallback', count: jobs.length }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }
        
        const text = await resp.text();
        const items = source.parse(text);
        const jobs = items.map(extractMeta);
        
        return new Response(JSON.stringify({ jobs, source: 'indeed', count: jobs.length }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: e.message, jobs: [] }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // Route: /status
    if (path === '/status') {
      return new Response(JSON.stringify({ 
        status: 'ok', 
        version: '1.0',
        routes: ['/indeed?q=keyword&l=location', '/status']
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }
    
    // Root: HTML instructions
    return new Response(`<!DOCTYPE html>
<html><head><title>Job Proxy</title><meta charset="utf-8"></head><body>
<h1>Job Proxy Worker</h1>
<p>Routes:</p>
<ul>
  <li><code>/indeed?q=network+engineer&l=Dubai</code> — Get Indeed jobs as JSON</li>
  <li><code>/status</code> — Health check</li>
</ul>
</body></html>`, {
      headers: { ...corsHeaders, 'Content-Type': 'text/html' }
    });
  }
};
