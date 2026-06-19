const BROWSER_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
};

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const corsHeaders = { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' };
    if (request.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

    // e.g. /indeed?q=network+engineer&l=Dubai
    if (url.pathname.startsWith('/indeed')) {
      const q = url.searchParams.get('q') || 'network+engineer';
      const l = url.searchParams.get('l') || '';
      const targetUrl = l
        ? `https://www.indeed.com/rss?q=${encodeURIComponent(q)}&l=${encodeURIComponent(l)}&sort=date`
        : `https://www.indeed.com/rss?q=${encodeURIComponent(q)}&sort=date`;

      const resp = await fetch(targetUrl, { headers: BROWSER_HEADERS });
      if (!resp.ok) return new Response(JSON.stringify({error:`Upstream ${resp.status}`}), {status:500, headers:corsHeaders});

      const xml = await resp.text();
      const items = [];
      const regex = /<item>[\s\S]*?<\/item>/g;
      let match;
      while ((match = regex.exec(xml)) !== null) {
        const item = match[0];
        const t = (item.match(/<title>(.*?)<\/title>/))?.[1] || '';
        const link = (item.match(/<link>(.*?)<\/link>/))?.[1] || '';
        let company = 'Unknown';
        const dashPos = t.lastIndexOf(' - ');
        if (dashPos > 0) company = t.substring(dashPos + 3).trim();
        items.push({ title: t.split(' - ')[0], company, url: link, source: 'indeed' });
      }
      return new Response(JSON.stringify({source:'indeed', jobs:items, count:items.length}), {headers:corsHeaders});
    }

    // e.g. /bayt?t=network-engineer&c=uae
    if (url.pathname.startsWith('/bayt')) {
      const t = url.searchParams.get('t') || 'network-engineer';
      const c = url.searchParams.get('c') || 'uae';
      const targetUrl = `https://www.bayt.com/en/${c}/jobs/${t}-jobs/`;
      const resp = await fetch(targetUrl, { headers: BROWSER_HEADERS });
      if (!resp.ok) return new Response(JSON.stringify({error:`Upstream ${resp.status}`}), {status:500, headers:corsHeaders});
      const html = await resp.text();
      // Extract JSON-LD items
      const items = [];
      const ldRegex = /{"@type":"JobPosting".*?}/g;
      let m;
      while ((m = ldRegex.exec(html)) !== null) {
        try { items.push(JSON.parse(m[0])); } catch(e) {}
      }
      return new Response(JSON.stringify({source:'bayt', jobs:items, count:items.length}), {headers:corsHeaders});
    }

    return new Response(JSON.stringify({error:'/indeed?q=&l=  or  /bayt?t=&c='}), {headers:corsHeaders});
  }
}
