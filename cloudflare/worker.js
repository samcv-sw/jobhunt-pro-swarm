// JobHunt Pro — Cloudflare Worker v4.0: Autonomous Cloud Engine
// $0 — 100k req/day free. Native D1, KV cache, R2 files, AI scoring.
// Binds: DB (D1), KV (CACHE), R2 (FILES), AI (Workers AI)
// Cron: every 30 min — campaign processor

const CONFIG = {
  PA_BASE: 'https://jhfguf.pythonanywhere.com',
  TIMEOUT_MS: 15000,
  CRON_SELF_URL: 'https://jobhunt-pro-router.samsalameh-cv.workers.dev',
};

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
  'Access-Control-Max-Age': '86400',
};

// ── HELPERS ──
function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { ...CORS, 'Content-Type': 'application/json' } });
}

function error(msg, status = 400) {
  return json({ error: msg }, status);
}

function getBody(request) {
  return request.method === 'GET' ? null : request.clone().text();
}

// ── KV CACHE WRAPPER ──
async function cacheGet(kv, key, ttl = 300) {
  if (!kv) return null;
  const cached = await kv.get(key, { type: 'json' });
  if (cached) return cached;
  return null;
}

async function cacheSet(kv, key, value, ttl = 300) {
  if (!kv) return;
  await kv.put(key, JSON.stringify(value), { expirationTtl: ttl });
}

// ── AI COVER LETTER GENERATION ──
async function generateCoverLetter(ai, jobTitle, company, userName, userRoles, aiKey) {
  // Three-tier AI: 1) User's own key, 2) Workers AI (free), 3) Template fallback
  const prompt = `Write a professional cover letter email for ${userName} applying for ${jobTitle} at ${company}. 
Skills: ${userRoles || 'IT professional'}. Keep it 3-4 sentences, professional but warm. 
Start with "Dear Hiring Manager," and end with "Best regards, ${userName}"`;

  // Tier 1: User's BYO AI key (OpenAI/Groq/Anthropic)
  if (aiKey) {
    try {
      const resp = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + aiKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'llama-3.1-8b-instant',
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 300, temperature: 0.7,
        }),
      });
      const data = await resp.json();
      if (data?.choices?.[0]?.message?.content) return data.choices[0].message.content.trim();
    } catch (e) { /* fall through */ }
  }

  // Tier 2: Cloudflare Workers AI (free, no key needed if binding exists)
  if (ai) {
    try {
      const resp = await ai.run('@cf/meta/llama-3.1-8b-instruct', {
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 300, temperature: 0.7,
      });
      // Workers AI returns { response: "..." } for text gen, or { choices: [...] } for chat
      if (resp?.response) return resp.response.trim();
      if (resp?.choices?.[0]?.message?.content) return resp.choices[0].message.content.trim();
    } catch (e) { /* fall through */ }
  }

  // Tier 3: Template
  return `Dear Hiring Manager,

I am writing to express my strong interest in the ${jobTitle} position at ${company}. With my background in ${userRoles || 'IT'}, I am confident that my skills and experience align perfectly with your requirements.

I would welcome the opportunity to discuss how I can contribute to your team.

Best regards,
${userName}`;
}

// ── SCRAPE JOBS FROM GOOGLE CACHE ──
async function scrapeJobs(env, url) {
  if (!url) return { error: 'Missing url' };
  
  // Check D1 cache
  if (env.DB) {
    const cached = await env.DB.prepare(
      "SELECT content, expires_at FROM scraper_cache WHERE url = ? AND expires_at > datetime('now')"
    ).bind(url).first();
    if (cached) return { source: 'cache', content: cached.content };
  }
  
  try {
    const resp = await fetch(`https://webcache.googleusercontent.com/search?q=cache:${encodeURIComponent(url)}`, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' },
    });
    const text = await resp.text();
    
    if (env.DB && text.length < 100000) {
      env.DB.prepare(
        "INSERT OR REPLACE INTO scraper_cache (url, platform, content, content_hash, expires_at, status) VALUES (?, ?, ?, ?, datetime('now', '+1 hour'), ?)"
      ).bind(url, 'google_cache', text.substring(0, 50000), String(text.length), resp.status).run().catch(() => {});
    }
    return { source: 'google_cache', status: resp.status, content: text.substring(0, 100000) };
  } catch (e) {
    return { error: e.message };
  }
}

// ── CHECK WORKERS AI AVAILABILITY ──
function hasAI(env) {
  return typeof env.AI !== 'undefined' && env.AI !== null && typeof env.AI.run === 'function';
}

export default {
  // ═══════════ SCHEDULED CRON: Campaign Processor (every 30 min) ═══════════
  async scheduled(event, env, ctx) {
    console.log('Running campaign processor...');
    
    try {
      // Step 1: Find active campaigns
      const campaigns = await env.DB.prepare(
        "SELECT c.id, c.user_id, c.sent_count, u.email, u.name, u.target_roles, u.target_locations, u.byo_smtp_email, u.byo_smtp_token, u.byo_ai_key FROM campaigns c JOIN users u ON c.user_id = u.id WHERE c.status = 'active' AND u.status = 'active'"
      ).all();
      
      console.log(`Found ${campaigns.results.length} active campaigns`);
      
      for (const camp of campaigns.results) {
        ctx.waitUntil(processCampaign(env, camp));
      }
    } catch (e) {
      console.error('Cron error:', e.message);
    }
  },

  // ═══════════ HTTP HANDLER ═══════════
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    const db = env.DB;
    const kv = env.CACHE;
    const r2 = env.BUCKET;
    const ai = env.AI;

    if (method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    try {
      // ═══════════ API: CLOUD-HEALTH ═══════════
      if (path === '/api/cloud-health') {
        await db.prepare('SELECT 1').all();
        const kvOk = !!kv;
        const r2Ok = !!r2;
        const aiOk = hasAI(env);
        return json({
          status: 'ok', db: 'd1_connected', kv: kvOk, r2: r2Ok, ai: aiOk, 
          version: '4.0', time: new Date().toISOString(),
        });
      }

      // ═══════════ API: REGISTER ═══════════
      if (path === '/api/register-fast' && method === 'POST') {
        const body = await request.json();
        const name = (body.name || '').trim();
        const email = (body.email || '').trim().toLowerCase();
        if (!name || !email) return error('Name and email required');

        const existing = await db.prepare('SELECT id, email, name FROM users WHERE email = ?').bind(email).first();
        if (existing) return json({ ok: true, user_id: existing.id, name: existing.name, message: 'Welcome back!', existing: true });

        const roles = Array.isArray(body.roles) ? body.roles.join(', ') : (body.roles || '');
        const locations = Array.isArray(body.locations) ? body.locations.join(', ') : (body.locations || '');
        const salary = parseInt(body.salary) || 1500;
        const hash = 'auto_' + email.split('@')[0] + '_' + Date.now();

        const res = await db.prepare(
          'INSERT INTO users (email, name, password_hash, target_roles, target_locations, target_salary_min, byo_ai_key, byo_ai_provider, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime(\"now\"), \"active\")'
        ).bind(email, name, hash, roles, locations, salary, body.ai_key || '', body.ai_provider || 'groq').run();
        
        await cacheSet(kv, 'user_' + email, { id: res.meta.last_row_id }, 3600);
        
        return json({ ok: true, user_id: res.meta.last_row_id, name, email, message: 'Account created! Connect Gmail to start.' });
      }

      // ═══════════ API: USER LOOKUP ═══════════
      if (path === '/api/user/by-email' && method === 'GET') {
        const email = url.searchParams.get('email');
        if (!email) return error('Email required');
        
        const cached = await cacheGet(kv, 'user_' + email.toLowerCase());
        if (cached) return json(cached);

        const user = await db.prepare(
          "SELECT id, email, name, target_roles, target_locations, target_salary_min, byo_smtp_email, created_at, status FROM users WHERE email = ?"
        ).bind(email.toLowerCase()).first();
        if (!user) return json({ error: 'User not found' }, 404);
        
        const result = { 
          id: user.id, user_id: String(user.id), email: user.email, name: user.name, 
          target_roles: user.target_roles || '', target_locations: user.target_locations || '', 
          min_salary: user.target_salary_min || 0, created_at: user.created_at 
        };
        await cacheSet(kv, 'user_' + email.toLowerCase(), result, 300);
        return json(result);
      }

      // ═══════════ API: USER STATS ═══════════
      if (path === '/api/user/stats' && method === 'GET') {
        const uid = url.searchParams.get('user_id');
        if (!uid) return error('user_id required');
        
        const appCount = await db.prepare('SELECT COUNT(*) as c FROM applications WHERE user_id = ?').bind(uid).first();
        const sentCount = await db.prepare("SELECT COUNT(*) as c FROM applications WHERE user_id = ? AND email_sent = 1").bind(uid).first();
        const interviewCount = await db.prepare("SELECT COUNT(*) as c FROM applications WHERE user_id = ? AND status = 'interview'").bind(uid).first();
        const apps = appCount?.c || 0;
        
        return json({
          apps_sent: sentCount?.c || 0, interviews: interviewCount?.c || 0, replies: 0,
          match_rate: apps > 0 ? Math.round((interviewCount?.c || 0) / apps * 1000) / 10 : 0,
          campaign: null,
        });
      }

      // ═══════════ API: CAMPAIGN CREATE ═══════════
      if (path === '/api/campaign/create' && method === 'POST') {
        const body = await request.json();
        const uid = body.user_id;
        if (!uid) return error('user_id required');

        const existing = await db.prepare("SELECT id, status FROM campaigns WHERE user_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1").bind(uid).first();
        if (existing) return json({ ok: true, campaign_id: existing.id, message: 'Campaign already active', existing: true });

        const res = await db.prepare(
          "INSERT INTO campaigns (user_id, name, status, sent_count, created_at) VALUES (?, 'Auto Campaign', 'active', 0, datetime('now'))"
        ).bind(uid).run();

        // Invalidate campaign cache
        await kv.delete('campaigns_' + uid);

        return json({ ok: true, campaign_id: res.meta.last_row_id, user_id: uid, message: 'Auto-Pilot campaign started! AI agents engaged.' });
      }

      // ═══════════ API: CAMPAIGN LIST ═══════════
      if (path === '/api/campaign/list' && method === 'GET') {
        const uid = url.searchParams.get('user_id');
        if (!uid) return error('user_id required');
        
        const cached = await cacheGet(kv, 'campaigns_' + uid, 60);
        if (cached) return json({ campaigns: cached });

        const rows = await db.prepare(
          'SELECT id, name, status, sent_count, created_at, completed_at FROM campaigns WHERE user_id = ? ORDER BY id DESC LIMIT 10'
        ).bind(uid).all();

        const campaigns = rows.results.map(r => ({
          id: r.id, name: r.name || 'Auto Campaign #' + r.id, status: r.status,
          apps_sent: r.sent_count || 0, jobs_found: 0, created_at: r.created_at,
        }));
        
        await cacheSet(kv, 'campaigns_' + uid, campaigns, 60);
        return json({ campaigns });
      }

      // ═══════════ API: JOBS FOR USER ═══════════
      if (path === '/api/jobs/user' && method === 'GET') {
        const uid = url.searchParams.get('user_id');
        const limit = parseInt(url.searchParams.get('limit') || '20');
        if (!uid) return error('user_id required');

        const rows = await db.prepare(
          'SELECT a.id, j.title, j.company, j.platform, a.status, a.sent_at, a.email_sent FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.user_id = ? ORDER BY a.id DESC LIMIT ?'
        ).bind(uid, limit).all();

        const user = await db.prepare('SELECT target_roles FROM users WHERE id = ?').bind(uid).first();
        let unscored = { results: [] };
        if (user?.target_roles) {
          const like = '%' + user.target_roles.split(',')[0].trim() + '%';
          unscored = await db.prepare(
            "SELECT id, title, company, platform FROM jobs WHERE (title LIKE ? OR company LIKE ?) AND id NOT IN (SELECT job_id FROM applications WHERE user_id = ?) ORDER BY id DESC LIMIT ?"
          ).bind(like, like, uid, Math.max(limit - rows.results.length, 5)).all();
        }

        const jobs = [
          ...rows.results.map(r => ({ id: r.id, title: r.title, company: r.company, source: r.platform || 'application', score: 100, status: r.status, sent_at: r.sent_at })),
          ...unscored.results.slice(0, Math.max(limit - rows.results.length, 5)).map(r => ({ id: r.id, title: r.title, company: r.company, source: r.platform || 'web', score: 85, status: 'matched' })),
        ];

        return json({ jobs: jobs.slice(0, limit), total: jobs.length });
      }

      // ═══════════ API: SMTP SAVE ═══════════
      if (path === '/api/byo-smtp/save' && method === 'POST') {
        const body = await request.json();
        const { user_id, email: smtpEmail, password } = body;
        if (!user_id || !smtpEmail || !password) return error('user_id, email, password required');

        const token = Array.from(new TextEncoder().encode(smtpEmail + ':' + password)).map(b => String.fromCharCode(b + 13)).join('');
        await db.prepare('UPDATE users SET byo_smtp_email = ?, byo_smtp_token = ? WHERE id = ?').bind(smtpEmail, token, user_id).run();
        
        // Invalidate KV cache
        const userRow = await db.prepare('SELECT email FROM users WHERE id = ?').bind(user_id).first();
        if (userRow) await kv.delete('user_' + userRow.email.toLowerCase());

        return json({ ok: true, message: 'SMTP credentials saved.' });
      }

      // ═══════════ API: DAILY STATS ═══════════
      if (path === '/api/stats/daily' && method === 'GET') {
        const days = parseInt(url.searchParams.get('days') || '30');
        const rows = await db.prepare(
          "SELECT date(coalesce(sent_at, 'now')) as date, COUNT(*) as apps FROM applications WHERE sent_at IS NOT NULL AND sent_at >= date('now', '-' || ? || ' days') GROUP BY date(coalesce(sent_at, 'now')) ORDER BY date DESC"
        ).bind(days).all();
        return json({ stats: rows.results, period_days: days });
      }

      // ═══════════ API: OUTBOX CLAIM ═══════════
      if (path === '/api/email/outbox/claim' && method === 'GET') {
        const workerId = parseInt(url.searchParams.get('worker') || '0');
        const limit = parseInt(url.searchParams.get('limit') || '5');
        
        // Use modulo to distribute across workers
        await db.prepare(
          "UPDATE email_outbox SET status = 'claimed', sent_at = datetime('now') WHERE id IN (SELECT id FROM email_outbox WHERE status = 'queued' AND id % 16 = ? ORDER BY id ASC LIMIT ?)"
        ).bind(workerId, limit).run();
        
        const claimed = await db.prepare(
          "SELECT eo.id, eo.to_email, eo.to_name, eo.subject, eo.body, u.byo_smtp_email, u.byo_smtp_token, u.email as user_email FROM email_outbox eo JOIN users u ON eo.user_id = u.id WHERE eo.status = 'claimed' AND eo.id % 16 = ? ORDER BY eo.id ASC"
        ).bind(workerId).all();
        
        // Decode SMTP credentials
        const emails = claimed.results.map(e => {
          let smtpInfo = { email: '', password: '' };
          if (e.byo_smtp_token) {
            const decoded = Array.from(e.byo_smtp_token).map(c => String.fromCharCode(c.charCodeAt(0) - 13)).join('');
            const parts = decoded.split(':');
            smtpInfo = { email: parts[0] || '', password: parts.slice(1).join(':') || '' };
          } else {
            smtpInfo = { email: e.user_email || '', password: '' };
          }
          return {
            id: e.id, to_email: e.to_email, to_name: e.to_name || '',
            subject: e.subject || 'Job Application', body: e.body || '',
            smtp_email: smtpInfo.email, smtp_password: smtpInfo.password,
          };
        });
        
        return json({ emails, worker: workerId });
      }

      // ═══════════ API: OUTBOX UPDATE ═══════════
      if (path === '/api/email/outbox/update' && method === 'POST') {
        const body = await request.json();
        const { id, status: es, error } = body;
        if (!id || !es) return error('id and status required');
        
        await db.prepare(
          "UPDATE email_outbox SET status = ?, error = ?, sent_at = datetime('now') WHERE id = ?"
        ).bind(es === 'sent' ? 'sent' : 'failed', error || '', id).run();
        
        // Update campaign sent count
        await db.prepare(
          "UPDATE campaigns SET sent_count = (SELECT COUNT(*) FROM email_outbox WHERE status = 'sent' AND campaign_id = (SELECT campaign_id FROM email_outbox WHERE id = ?)) WHERE id = (SELECT campaign_id FROM email_outbox WHERE id = ?)"
        ).bind(id, id).run();
        
        return json({ ok: true, message: 'Email ' + id + ' marked as ' + es });
      }

      // ═══════════ API: AI GENERATE COVER LETTER ═══════════
      if (path === '/api/ai/cover-letter' && method === 'POST') {
        const body = await request.json();
        const { user_id, job_title, company } = body;
        if (!user_id || !job_title || !company) return error('user_id, job_title, company required');
        
        const user = await db.prepare('SELECT name, target_roles, byo_ai_key FROM users WHERE id = ?').bind(user_id).first();
        if (!user) return error('User not found', 404);
        
        const letter = await generateCoverLetter(ai, job_title, company, user.name || 'Applicant', user.target_roles || '', user.byo_ai_key || '');
        return json({ ok: true, cover_letter: letter });
      }

      // ═══════════ API: CV UPLOAD (R2) ═══════════
      if (path === '/api/cv/upload' && method === 'POST') {
        if (!r2) return error('File storage not available', 503);
        
        const body = await request.json();
        const { user_id, filename, content } = body;  // content is base64
        if (!user_id || !content) return error('user_id and content required');
        
        const key = 'cv/' + user_id + '/' + (filename || 'resume.pdf');
        const binary = Uint8Array.from(atob(content), c => c.charCodeAt(0));
        await r2.put(key, binary, { httpMetadata: { contentType: 'application/pdf' } });
        
        // Update user record
        await db.prepare('UPDATE users SET cv_url = ? WHERE id = ?').bind(key, user_id).run();
        
        return json({ ok: true, url: key, message: 'CV uploaded!' });
      }

      // ═══════════ API: SCRAPE ═══════════
      if (path === '/scrape') {
        const urlParam = url.searchParams.get('url');
        const result = await scrapeJobs(env, urlParam);
        return json(result);
      }

      // ═══════════ PA PROXY (backward compat) ═══════════
      if (path.startsWith('/_/pa/')) {
        const targetPath = path.replace('/_/pa/', '/');
        const targetUrl = CONFIG.PA_BASE + targetPath + url.search;
        const resp = await fetch(targetUrl, {
          method: method,
          headers: { 'User-Agent': 'JobHuntPro-CFWorker/4.0', 'Accept': 'application/json', 'Content-Type': request.headers.get('Content-Type') || 'application/json' },
          body: await getBody(request),
        });
        return new Response(await resp.text(), { status: resp.status, headers: { ...CORS, ...Object.fromEntries(resp.headers) } });
      }

      // ═══════════ HEALTH ═══════════
      if (path === '/health') {
        return json({
          status: 'ok', worker: 'jobhunt-pro-router', version: '4.0',
          d1: !!db, kv: !!kv, r2: !!r2, ai: hasAI(env),
          cron: 'every 30min',
        });
      }

      return json({ error: 'Not found' }, 404);
    } catch (e) {
      console.error('Error:', e.message, e.stack);
      return json({ error: e.message }, 500);
    }
  },
};

// ── PROCESS SINGLE CAMPAIGN (called from cron) ──
async function processCampaign(env, camp) {
  const db = env.DB;
  const ai = env.AI;
  console.log(`Processing campaign ${camp.id} for user ${camp.user_id}`);
  
  try {
    // Find unscored jobs matching user's target
    if (camp.target_roles) {
      const keywords = camp.target_roles.split(',').map(k => k.trim()).filter(Boolean);
      const jobs = await db.prepare(
        "SELECT id, title, company, location FROM jobs WHERE (title LIKE ? OR company LIKE ?) AND id NOT IN (SELECT job_id FROM applications WHERE user_id = ?) ORDER BY scraped_at ASC LIMIT 20"
      ).bind('%' + keywords[0] + '%', '%' + keywords[0] + '%', camp.user_id).all();
      
      for (const job of jobs.results) {
        // Generate cover letter
        const letter = await generateCoverLetter(ai, job.title, job.company, camp.name, camp.target_roles, camp.byo_ai_key);
        
        // Create application record
        await db.prepare(
          'INSERT INTO applications (user_id, job_id, status, cover_letter, email_sent) VALUES (?, ?, ?, ?, 0)'
        ).bind(camp.user_id, job.id, 'matched', letter.substring(0, 2000)).run();
        
        // Queue email in outbox
        const toEmail = job.email || '';
        if (toEmail) {
          await db.prepare(
            "INSERT INTO email_outbox (campaign_id, user_id, to_email, to_name, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'queued', datetime('now'))"
          ).bind(camp.id, camp.user_id, toEmail, job.company, 'Application for ' + job.title + ' at ' + job.company, letter.substring(0, 1000)).run();
          console.log(`  Queued email for job ${job.id}: ${job.title}`);
        }
        console.log(`  Matched job ${job.id}: ${job.title} at ${job.company}`);
      }
    }
    
    // Update campaign stats
    const sentCount = await db.prepare("SELECT COUNT(*) as c FROM applications WHERE user_id = ? AND email_sent = 1").bind(camp.user_id).first();
    await db.prepare("UPDATE campaigns SET sent_count = ? WHERE id = ?").bind(sentCount?.c || 0, camp.id).run();
    
  } catch (e) {
    console.error(`Campaign ${camp.id} error:`, e.message);
  }
}
