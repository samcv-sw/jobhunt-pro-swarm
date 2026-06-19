// JobHunt Pro — Cloudflare Worker: D1 API Router + PA Proxy
// $0 — 100k req/day free. All frontend API routes native in D1.

const CONFIG = {
  PA_BASE: 'https://jhfguf.pythonanywhere.com',
  TIMEOUT_MS: 15000,
};

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
  'Access-Control-Max-Age': '86400',
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;

    if (method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    const db = env.DB;
    const json = (data, status = 200) =>
      new Response(JSON.stringify(data), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });

    try {
      // ═══════════ D1-BACKED API ROUTES ═══════════

      // POST /api/register-fast — register user
      if (path === '/api/register-fast' && method === 'POST') {
        const body = await request.json();
        const name = (body.name || '').trim();
        const email = (body.email || '').trim().toLowerCase();
        if (!name || !email) return json({ error: 'Name and email required' }, 400);

        const existing = await db.prepare('SELECT id, email, name FROM users WHERE email = ?').bind(email).first();
        if (existing) return json({ ok: true, user_id: existing.id, name: existing.name, message: 'Welcome back!', existing: true });

        const roles = Array.isArray(body.roles) ? body.roles.join(', ') : (body.roles || '');
        const locations = Array.isArray(body.locations) ? body.locations.join(', ') : (body.locations || '');
        const salary = parseInt(body.salary) || 1500;

        const hash = 'auto_' + email.split('@')[0];
        const res = await db.prepare(
          'INSERT INTO users (email, name, password_hash, target_roles, target_locations, target_salary_min, created_at, status) VALUES (?, ?, ?, ?, ?, ?, datetime("now"), "active")'
        ).bind(email, name, hash, roles, locations, salary).run();
        
        const uid = res.meta.last_row_id;
        return json({ ok: true, user_id: uid, name: name, email: email, message: 'Account created!' });
      }

      // GET /api/user/by-email — lookup user
      if (path === '/api/user/by-email' && method === 'GET') {
        const email = url.searchParams.get('email');
        if (!email) return json({ error: 'Email required' }, 400);
        const user = await db.prepare(
          'SELECT id as user_id, email, name, target_roles, target_locations, target_salary_min, created_at, status, byo_smtp_email FROM users WHERE email = ?'
        ).bind(email.toLowerCase()).first();
        if (!user) return json({ error: 'User not found' }, 404);
        return json({ id: user.user_id, user_id: String(user.user_id), email: user.email, name: user.name, target_roles: user.target_roles || '', target_locations: user.target_locations || '', min_salary: user.target_salary_min || 0, created_at: user.created_at });
      }

      // GET /api/user/stats — user stats
      if (path === '/api/user/stats' && method === 'GET') {
        const uid = url.searchParams.get('user_id');
        if (!uid) return json({ error: 'user_id required' }, 400);
        
        const appCount = await db.prepare('SELECT COUNT(*) as c FROM applications WHERE user_id = ?').bind(uid).first();
        const sentCount = await db.prepare("SELECT COUNT(*) as c FROM applications WHERE user_id = ? AND email_sent = 1").bind(uid).first();
        const interviewCount = await db.prepare("SELECT COUNT(*) as c FROM applications WHERE user_id = ? AND status = 'interview'").bind(uid).first();
        const apps = appCount?.c || 0;
        
        return json({
          apps_sent: sentCount?.c || 0,
          interviews: interviewCount?.c || 0,
          replies: 0,
          match_rate: apps > 0 ? Math.round((interviewCount?.c || 0) / apps * 100 * 10) / 10 : 0,
          campaign: null,
        });
      }

      // POST /api/campaign/create — create campaign
      if (path === '/api/campaign/create' && method === 'POST') {
        const body = await request.json();
        const uid = body.user_id;
        if (!uid) return json({ error: 'user_id required' }, 400);

        const existing = await db.prepare("SELECT id, status FROM campaigns WHERE user_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1").bind(uid).first();
        if (existing) return json({ ok: true, campaign_id: existing.id, message: 'Campaign already active', existing: true });

        const res = await db.prepare(
          "INSERT INTO campaigns (user_id, name, status, sent_count, created_at) VALUES (?, 'Auto Campaign', 'active', 0, datetime('now'))"
        ).bind(uid).run();

        return json({ ok: true, campaign_id: res.meta.last_row_id, user_id: uid, message: 'Auto-Pilot campaign started! 200 AI agents engaged.' });
      }

      // GET /api/campaign/list — list campaigns
      if (path === '/api/campaign/list' && method === 'GET') {
        const uid = url.searchParams.get('user_id');
        if (!uid) return json({ error: 'user_id required' }, 400);
        
        const rows = await db.prepare(
          'SELECT id, name, status, sent_count, created_at, completed_at FROM campaigns WHERE user_id = ? ORDER BY id DESC LIMIT 10'
        ).bind(uid).all();

        return json({
          campaigns: rows.results.map(r => ({
            id: r.id,
            name: r.name || 'Auto Campaign #' + r.id,
            status: r.status,
            apps_sent: r.sent_count || 0,
            jobs_found: 0,
            created_at: r.created_at,
          })),
        });
      }

      // GET /api/jobs/user — jobs for user
      if (path === '/api/jobs/user' && method === 'GET') {
        const uid = url.searchParams.get('user_id');
        const limit = parseInt(url.searchParams.get('limit') || '20');
        if (!uid) return json({ error: 'user_id required' }, 400);

        const rows = await db.prepare(
          'SELECT a.id, j.title, j.company, a.status, a.sent_at, a.email_sent FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.user_id = ? ORDER BY a.id DESC LIMIT ?'
        ).bind(uid, limit).all();

        // Also get unscored jobs from jobs table
        const user = await db.prepare('SELECT target_roles, target_locations FROM users WHERE id = ?').bind(uid).first();
        let unscored = { results: [] };
        if (user?.target_roles) {
          const like = '%' + user.target_roles.split(',')[0].trim() + '%';
          unscored = await db.prepare(
            "SELECT id, title, company, source FROM jobs WHERE (title LIKE ? OR company LIKE ?) AND id NOT IN (SELECT job_id FROM applications WHERE user_id = ?) ORDER BY created_at DESC LIMIT ?"
          ).bind(like, like, uid, Math.max(limit - rows.results.length, 5)).all();
        }

        const jobs = [
          ...rows.results.map(r => ({ id: r.id, title: r.title, company: r.company, source: 'application', score: 100, status: r.status, sent_at: r.sent_at })),
          ...unscored.results.slice(0, Math.max(limit - rows.results.length, 5)).map(r => ({ id: r.id, title: r.title, company: r.company, source: r.source || 'web', score: 85, status: 'matched' })),
        ];

        return json({ jobs: jobs.slice(0, limit), total: jobs.length });
      }

      // POST /api/byo-smtp/save — save SMTP credentials
      if (path === '/api/byo-smtp/save' && method === 'POST') {
        const body = await request.json();
        const { user_id, email: smtpEmail, password } = body;
        if (!user_id || !smtpEmail || !password) return json({ error: 'user_id, email, password required' }, 400);

        // Store (basic encoding, upgrade later)
        const token = Array.from(new TextEncoder().encode(smtpEmail + ':' + password)).map(b => String.fromCharCode(b + 13)).join('');
        await db.prepare('UPDATE users SET byo_smtp_email = ?, byo_smtp_token = ? WHERE id = ?').bind(smtpEmail, token, user_id).run();

        return json({ ok: true, message: 'SMTP credentials saved.' });
      }

      // GET /api/stats/daily — global stats
      if (path === '/api/stats/daily' && method === 'GET') {
        const days = parseInt(url.searchParams.get('days') || '30');
        const rows = await db.prepare(
          "SELECT date(coalesce(sent_at, 'now')) as date, COUNT(*) as apps FROM applications WHERE sent_at IS NOT NULL AND sent_at >= date('now', '-' || ? || ' days') GROUP BY date(coalesce(sent_at, 'now')) ORDER BY date DESC"
        ).bind(days).all();
        return json({ stats: rows.results, period_days: days });
      }

      // GET /api/cloud-health — health
      if (path === '/api/cloud-health' && method === 'GET') {
        await db.prepare('SELECT 1').all();
        return json({ status: 'ok', db: 'd1_connected', api: 'v2-d1-native', time: new Date().toISOString() });
      }

      // ═══════════ PA PROXY ═══════════
      if (path.startsWith('/_/pa/')) {
        const targetPath = path.replace('/_/pa/', '/');
        const targetUrl = CONFIG.PA_BASE + targetPath + url.search;
        const resp = await fetch(targetUrl, {
          method: method,
          headers: { 'User-Agent': 'JobHuntPro-CFWorker/2.0', 'Accept': 'application/json', 'Content-Type': request.headers.get('Content-Type') || 'application/json' },
          body: method === 'GET' ? null : await request.text(),
        });
        return new Response(await resp.text(), { status: resp.status, headers: { ...CORS, ...Object.fromEntries(resp.headers) } });
      }

      // ═══════════ HEALTH ═══════════
      if (path === '/health') {
        return json({ status: 'ok', worker: 'jobhunt-pro-router', version: '3.0', d1: true, routes: ['/api/*', '/_/pa/*'] });
      }

      return json({ error: 'Not found' }, 404);
    } catch (e) {
      return json({ error: e.message, detail: e.stack }, 500);
    }
  },
};
