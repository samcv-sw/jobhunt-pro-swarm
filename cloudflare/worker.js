// JobHunt Pro — Cloudflare Worker: Scraper Proxy + API Router + D1 DB
// $0 — 100k requests/day free, global CDN with D1 global reads
// Routes: /_/pa/* → PA proxy, /scrape → Google Cache, /api/* → D1
// Binds: env.DB = Cloudflare D1 database

// ── CONFIG ──
const CONFIG = {
  PA_BASE: 'https://jhfguf.pythonanywhere.com',
  GOOGLE_CACHE_ENABLED: true,
  TIMEOUT_MS: 15000,
  DB_CACHE_TTL_S: 300, // 5 min D1 cache
};

// ── MAIN ──
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const isApi = path.startsWith('/api/');

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // ─── Route: API — D1 Database Queries ───
    if (isApi) {
      if (!env.DB) {
        return new Response(JSON.stringify({ error: 'D1 not bound' }), {
          status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      const db = env.DB;

      // GET /api/jobs?platform=linkedin&limit=20
      if (path === '/api/jobs' && request.method === 'GET') {
        const platform = url.searchParams.get('platform') || '';
        const limit = parseInt(url.searchParams.get('limit') || '20');
        const offset = parseInt(url.searchParams.get('offset') || '0');
        const keyword = url.searchParams.get('q') || '';

        let query = 'SELECT * FROM jobs WHERE status = "active"';
        const params = [];

        if (platform) {
          query += ' AND platform = ?';
          params.push(platform);
        }
        if (keyword) {
          query += ' AND (title LIKE ? OR company LIKE ? OR description LIKE ?)';
          params.push(`%${keyword}%`, `%${keyword}%`, `%${keyword}%`);
        }

        query += ' ORDER BY posted_at DESC LIMIT ? OFFSET ?';
        params.push(limit, offset);

        const { results } = await db.prepare(query).bind(...params).all();
        return new Response(JSON.stringify({ jobs: results, total: results.length }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      // GET /api/users/:id/stats
      const userStatsMatch = path.match(/^\/api\/users\/(\d+)\/stats$/);
      if (userStatsMatch && request.method === 'GET') {
        const userId = parseInt(userStatsMatch[1]);
        const { results } = await db.prepare(`
          SELECT 
            COUNT(*) as total_apps,
            SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN status = 'interview' THEN 1 ELSE 0 END) as interviews
          FROM applications WHERE user_id = ?
        `).bind(userId).all();

        const { results: user } = await db.prepare(
          'SELECT email, name, target_roles, status FROM users WHERE id = ?'
        ).bind(userId).all();

        return new Response(JSON.stringify({ stats: results[0] || {}, user: user[0] || {} }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      // POST /api/sync — PA → D1 sync
      if (path === '/api/sync' && request.method === 'POST') {
        const body = await request.json();
        const { table, action, data } = body;

        if (!table || !action || !data) {
          return new Response(JSON.stringify({ error: 'Need table, action, data' }), {
            status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          });
        }

        if (action === 'insert' && table === 'jobs') {
          await db.prepare(`
            INSERT OR REPLACE INTO jobs (external_id, title, company, location, platform, url, description, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            data.external_id, data.title, data.company,
            data.location || '', data.platform, data.url || '',
            data.description || '', data.posted_at || new Date().toISOString()
          ).run();
        }

        if (action === 'insert' && table === 'applications') {
          await db.prepare(`
            INSERT INTO applications (user_id, job_id, status, email_sent, cover_letter)
            VALUES (?, ?, ?, ?, ?)
          `).bind(data.user_id, data.job_id, 'pending', 0, data.cover_letter || '').run();
        }

        // Log sync
        await db.prepare(
          'INSERT INTO sync_log (source, action, table_name, record_id, status) VALUES ("worker", ?, ?, ?, "success")'
        ).bind(action, table, data.id || 0).run();

        return new Response(JSON.stringify({ status: 'synced' }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      // GET /api/stats/daily
      if (path === '/api/stats/daily' && request.method === 'GET') {
        const days = parseInt(url.searchParams.get('days') || '7');
        const { results } = await db.prepare(`
          SELECT stat_date, SUM(apps_sent) as apps, SUM(interviews) as interviews
          FROM stats WHERE stat_date >= date('now', ? || ' days')
          GROUP BY stat_date ORDER BY stat_date DESC
        `).bind(`-${days}`).all();

        return new Response(JSON.stringify({ stats: results }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      // Health check with D1 ping
      if (path === '/api/health') {
        try {
          await db.prepare('SELECT 1 as ping').all();
          return new Response(JSON.stringify({ status: 'ok', db: 'connected' }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        } catch (e) {
          return new Response(JSON.stringify({ status: 'error', db: e.message }), {
            status: 503, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          });
        }
      }

      // 404 on unknown API path
      return new Response(JSON.stringify({ error: 'API not found' }), {
        status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // ─── Route: Proxy to PA ───
    if (path.startsWith('/_/pa/')) {
      const targetPath = path.replace('/_/pa/', '/');
      const targetUrl = `${CONFIG.PA_BASE}${targetPath}${url.search}`;
      try {
        const resp = await fetch(targetUrl, {
          method: request.method,
          headers: {
            'User-Agent': 'JobHuntPro-CFWorker/1.0',
            'Accept': 'application/json',
            ...(request.headers.get('Authorization') ? { 'Authorization': request.headers.get('Authorization') } : {}),
          },
          body: request.method === 'GET' ? null : await request.text(),
        });
        return new Response(await resp.text(), {
          status: resp.status,
          headers: { ...corsHeaders, ...Object.fromEntries(resp.headers) },
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: 'PA unreachable', detail: e.message }), {
          status: 502,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // ─── Route: Scrape via Google Cache ───
    if (path === '/scrape' && CONFIG.GOOGLE_CACHE_ENABLED) {
      const targetUrl = url.searchParams.get('url');
      if (!targetUrl) {
        return new Response(JSON.stringify({ error: 'Missing ?url=' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      // Check D1 cache first
      if (env.DB) {
        const { results } = await env.DB.prepare(
          'SELECT content FROM scraper_cache WHERE url = ? AND expires_at > datetime("now")'
        ).bind(targetUrl).all();
        if (results.length > 0) {
          return new Response(JSON.stringify({
            source: 'cache_d1', cached: true, content: results[0].content
          }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
        }
      }

      try {
        const cacheUrl = `https://webcache.googleusercontent.com/search?q=cache:${encodeURIComponent(targetUrl)}`;
        const resp = await fetch(cacheUrl, {
          headers: { 'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' },
        });
        const text = await resp.text();

        // Cache in D1
        if (env.DB && text.length < 50000) {
          ctx.waitUntil(env.DB.prepare(
            'INSERT OR REPLACE INTO scraper_cache (url, platform, content, content_hash, expires_at, status) VALUES (?, "google_cache", ?, ?, datetime("now", "+1 hour"), ?)'
          ).bind(targetUrl, text.substring(0, 50000), text.length.toString(), resp.status).run());
        }

        return new Response(JSON.stringify({
          source: 'google_cache', status: resp.status, size: text.length,
          content: text.substring(0, 100000),
        }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
      } catch (e) {
        return new Response(JSON.stringify({ error: 'Scrape failed', detail: e.message }), {
          status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
    }

    // ─── Route: Health ───
    if (path === '/health' || path === '/') {
      return new Response(JSON.stringify({
        status: 'ok', worker: 'jobhunt-pro-router', version: '2.0',
        routes: ['/_/pa/*', '/scrape?url=', '/api/jobs', '/api/sync', '/api/health'],
        d1: !!env.DB,
      }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } });
    }

    return new Response(JSON.stringify({ error: 'Not found' }), {
      status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  },
};
