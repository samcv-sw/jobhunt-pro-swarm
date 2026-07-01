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

// ── FNV-1a HASH RESOLVER FOR 500 SHARDS ──
function fnv1a(str) {
  let hash = 2166136261;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return Math.abs(hash);
}

// ── TURSO SHARD DATABASE ROUTER ──
async function executeTurso(env, userId, sql, params = []) {
  const shardIndex = fnv1a(userId || 'default') % 500;
  const dbName = `jh-shard-${shardIndex}`;
  const userName = env.TURSO_USER_NAME || "samsalameh";
  const url = `https://${dbName}-${userName}.turso.io/v2/pipeline`;
  const token = env.TURSO_AUTH_TOKEN;

  if (!token) {
    console.warn("TURSO_AUTH_TOKEN is missing, falling back to local D1 DB");
    if (env.DB) {
      const stmt = env.DB.prepare(sql).bind(...params);
      return await stmt.run();
    }
    throw new Error("No database available (Turso token & D1 missing)");
  }

  // Format arguments for Turso HTTP API
  const args = params.map(p => {
    if (typeof p === 'number') return { type: 'integer', value: String(p) };
    return { type: 'text', value: String(p) };
  });

  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      requests: [
        {
          type: 'execute',
          stmt: { sql, args }
        },
        { type: 'close' }
      ]
    })
  });

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Turso Error: ${resp.status} - ${errText}`);
  }

  const data = await resp.json();
  const execResult = data.results?.[0]?.response?.result;
  return {
    success: true,
    meta: {
      changes: execResult?.rows_affected || 0,
      last_row_id: execResult?.last_insert_rowid || null
    },
    results: execResult?.rows || []
  };
}

// ── UPSTASH REDIS QUEUE STORAGE ──
async function redisCommand(env, command, ...args) {
  const url = env.UPSTASH_REDIS_REST_URL;
  const token = env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;
  try {
    const resp = await fetch(`${url}/${command}/${args.join('/')}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (resp.ok) return await resp.json();
  } catch (err) {
    console.error("Redis command error:", err.message);
  }
  return null;
}

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
async function generateCoverLetter(ai, jobTitle, company, userName, userRoles, aiKey, aiProvider) {
  // Three-tier AI: 1) User's own key (Groq/OpenAI/Gemini/Anthropic), 2) Workers AI (free), 3) Template fallback
  const prompt = `Write a professional cover letter email for ${userName} applying for ${jobTitle} at ${company}. 
Skills: ${userRoles || 'IT professional'}. Keep it 3-4 sentences, professional but warm. 
Start with "Dear Hiring Manager," and end with "Best regards, ${userName}"`;

  const provider = (aiProvider || 'groq').toLowerCase().trim();

  // Tier 1: User's BYO AI key
  if (aiKey) {
    try {
      if (provider === 'groq') {
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
      }
      else if (provider === 'openai') {
        const resp = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + aiKey, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: 'gpt-4o-mini',
            messages: [{ role: 'user', content: prompt }],
            max_tokens: 300, temperature: 0.7,
          }),
        });
        const data = await resp.json();
        if (data?.choices?.[0]?.message?.content) return data.choices[0].message.content.trim();
      }
      else if (provider === 'gemini') {
        const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${aiKey}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }]
          }),
        });
        const data = await resp.json();
        if (data?.candidates?.[0]?.content?.parts?.[0]?.text) return data.candidates[0].content.parts[0].text.trim();
      }
      else if (provider === 'anthropic') {
        const resp = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: { 
            'x-api-key': aiKey, 
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json' 
          },
          body: JSON.stringify({
            model: 'claude-3-5-sonnet-20240620',
            max_tokens: 300,
            messages: [{ role: 'user', content: prompt }]
          }),
        });
        const data = await resp.json();
        if (data?.content?.[0]?.text) return data.content[0].text.trim();
      }
    } catch (e) {
      console.error(`BYO AI (${provider}) failed, falling back to Workers AI:`, e.message);
    }
  }

  // Tier 2: Cloudflare Workers AI (free fallback)
  if (ai) {
    try {
      const resp = await ai.run('@cf/meta/llama-3.1-8b-instruct', {
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 300, temperature: 0.7,
      });
      if (resp?.response) return resp.response.trim();
      if (resp?.choices?.[0]?.message?.content) return resp.choices[0].message.content.trim();
    } catch (e) {
      console.error("Workers AI failed, falling back to template:", e.message);
    }
  }

  // Tier 3: Template
  return `Dear Hiring Manager,

I am writing to express my strong interest in the ${jobTitle} position at ${company}. With my background in ${userRoles || 'IT'}, I am confident that my skills and experience align perfectly with your requirements.

I would welcome the opportunity to discuss how I can contribute to your team.

Best regards,
${userName}`;
}

// ── SCRAPE JOBS WITH DIRECT FETCH AND GOOGLEBOT FALLBACK ──
async function scrapeJobs(env, url) {
  if (!url) return { error: 'Missing url' };
  
  // Check D1 cache
  if (env.DB) {
    const cached = await env.DB.prepare(
      "SELECT content, expires_at FROM scraper_cache WHERE url = ? AND expires_at > datetime('now')"
    ).bind(url).first();
    if (cached) return { source: 'cache', content: cached.content };
  }
  
  // 1. Try Direct Fetch first (Modern browser UA)
  try {
    const resp = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
      },
      signal: AbortSignal.timeout(10000)
    });
    
    if (resp.status === 200) {
      const text = await resp.text();
      if (env.DB && text.length < 100000) {
        env.DB.prepare(
          "INSERT OR REPLACE INTO scraper_cache (url, platform, content, content_hash, expires_at, status) VALUES (?, ?, ?, ?, datetime('now', '+1 hour'), ?)"
        ).bind(url, 'direct_fetch', text.substring(0, 50000), String(text.length), resp.status).run().catch(() => {});
      }
      return { source: 'direct_fetch', status: 200, content: text.substring(0, 100000) };
    }
  } catch (directErr) {
    console.error("Direct fetch failed:", directErr.message);
  }
  
  // 2. Fallback: Googlebot fetch (bypasses some basic crawler blocks)
  try {
    const resp = await fetch(url, {
      headers: { 
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
      },
      signal: AbortSignal.timeout(10000)
    });
    
    if (resp.status === 200) {
      const text = await resp.text();
      if (env.DB && text.length < 100000) {
        env.DB.prepare(
          "INSERT OR REPLACE INTO scraper_cache (url, platform, content, content_hash, expires_at, status) VALUES (?, ?, ?, ?, datetime('now', '+1 hour'), ?)"
        ).bind(url, 'googlebot_fetch', text.substring(0, 50000), String(text.length), resp.status).run().catch(() => {});
      }
      return { source: 'googlebot_fetch', status: 200, content: text.substring(0, 100000) };
    } else {
      return { error: `Googlebot fetch returned status: ${resp.status}`, status: resp.status };
    }
  } catch (e) {
    return { error: `Fallback fetch failed: ${e.message}`, status: 502 };
  }
}

// ── CHECK WORKERS AI AVAILABILITY ──
function hasAI(env) {
  return typeof env.AI !== 'undefined' && env.AI !== null && typeof env.AI.run === 'function';
}

export default {
  // ═══════════ SCHEDULED CRON: Campaign Processor & Hydra Tick (every 4 min) ═══════════
  async scheduled(event, env, ctx) {
    console.log('Running campaign processor and Hydra tick...');
    
    const BACKENDS = [
      env.PA_BASE || "https://jhfguf.pythonanywhere.com",
      "https://jobhunt-pro.fly.dev",
      "https://jobhunt-pro.zeabur.app",
      "https://jobhunt-pro.onrender.com"
    ];

    // 1. Tick and Keep Alive all backends in parallel (non-blocking)
    ctx.waitUntil((async () => {
      let paFailed = false;
      let tickOk = false;
      let activeBackend = "none";

      for (const backend of BACKENDS) {
        try {
          console.log(`Pinging/Ticking backend: ${backend}`);
          // Send tick request
          const resp = await fetch(`${backend}/api/v2/cloud-tick`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action: 'cloud_tick',
              source: 'cf-cron',
              company_limit: 3,
              mode: 'normal'
            }),
            signal: AbortSignal.timeout(60000) // 60s timeout
          });

          if (resp.status === 200) {
            const data = await resp.json().catch(() => ({}));
            if (data.status === "ok") {
              tickOk = true;
              activeBackend = backend;
              console.log(`✓ Tick successful on ${backend}`);
            } else {
              console.log(`✗ Tick returned non-ok status on ${backend}: ${JSON.stringify(data)}`);
              if (backend.includes("pythonanywhere")) paFailed = true;
            }
          } else {
            console.log(`✗ Tick failed on ${backend} with status ${resp.status}`);
            if (backend.includes("pythonanywhere")) paFailed = true;
          }
        } catch (e) {
          console.error(`Error ticking ${backend}:`, e.message);
          if (backend.includes("pythonanywhere")) paFailed = true;
        }

        // Keepalive ping for healthz / api/ping as well
        try {
          fetch(`${backend}/healthz`, { signal: AbortSignal.timeout(10000) }).catch(() => {});
          fetch(`${backend}/api/ping`, { signal: AbortSignal.timeout(10000) }).catch(() => {});
          // Auto-reset stuck campaigns on all backends
          fetch(`${backend}/api/v2/cloud-tick/reset-stuck`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: AbortSignal.timeout(15000)
          }).catch(() => {});
        } catch (e) {}
      }

      // If Primary PythonAnywhere failed, attempt to reload it using PA API if token is configured
      if (paFailed && env.PA_API_TOKEN) {
        console.log("=== PA RELOAD TRIGGERED VIA CF WORKER ===");
        try {
          const paUser = env.PA_USER || "jhfguf";
          const paDomain = env.PA_DOMAIN || "jhfguf.pythonanywhere.com";
          const reloadUrl = `https://www.pythonanywhere.com/api/v0/user/${paUser}/webapps/${paDomain}/reload/`;
          const reloadResp = await fetch(reloadUrl, {
            method: 'POST',
            headers: { 'Authorization': `Token ${env.PA_API_TOKEN}` },
            signal: AbortSignal.timeout(30000)
          });
          console.log(`Reload API Response: ${reloadResp.status}`);
        } catch (reloadErr) {
          console.error("Failed to trigger PA reload:", reloadErr.message);
        }
      }

      // Send Telegram alert if the entire tick failed on all backends and we have a bot token
      if (!tickOk && env.TELEGRAM_BOT_TOKEN && env.TELEGRAM_CHAT_ID) {
        const msg = `🚨 CLOUDFLARE CRON CRITICAL ALERT: All Hydra backends failed to tick! Active: ${activeBackend}`;
        try {
          await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              chat_id: env.TELEGRAM_CHAT_ID,
              text: msg
            })
          });
        } catch (tgErr) {
          console.error("Failed to send Telegram alert:", tgErr.message);
        }
      }
    })());

    // 2. In addition, run the D1 campaign processor
    try {
      const campaigns = await env.DB.prepare(
        "SELECT c.id, c.user_id, c.sent_count, c.target_count, u.email, u.name, u.target_roles, u.target_locations, u.byo_smtp_email, u.byo_smtp_token, u.byo_ai_key, u.byo_ai_provider, u.daily_limit FROM campaigns c JOIN users u ON c.user_id = u.id WHERE c.status = 'active' AND u.status = 'active'"
      ).all();
      
      console.log(`Found ${campaigns.results.length} active campaigns in D1`);
      
      for (const camp of campaigns.results) {
        ctx.waitUntil(processCampaign(env, camp));
      }
    } catch (e) {
      console.error('D1 campaign cron error:', e.message);
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
      // ═══════════ API: SYNC (WASM LOCAL DB TO TURSO SHARDS) ═══════════
      if (path === '/api/sync' && method === 'POST') {
        const body = await request.json().catch(() => ({}));
        const { user_id, mutations } = body;
        if (!user_id || !Array.isArray(mutations)) {
          return error('user_id and mutations array required');
        }

        const synced = [];
        for (const m of mutations) {
          try {
            const { action_type, table_name, payload } = m;
            let sql = '';
            let params = [];

            if (action_type === 'insert') {
              const keys = Object.keys(payload);
              const placeholders = keys.map(() => '?').join(', ');
              sql = `INSERT OR REPLACE INTO ${table_name} (${keys.join(', ')}) VALUES (${placeholders})`;
              params = Object.values(payload);
            } else if (action_type === 'update') {
              const keys = Object.keys(payload).filter(k => k !== 'id');
              const sets = keys.map(k => `${k} = ?`).join(', ');
              sql = `UPDATE ${table_name} SET ${sets} WHERE id = ?`;
              params = [...keys.map(k => payload[k]), payload.id];
            } else if (action_type === 'delete') {
              sql = `DELETE FROM ${table_name} WHERE id = ?`;
              params = [payload.id];
            }

            if (sql) {
              await executeTurso(env, user_id, sql, params);
              synced.push(m.id);
            }
          } catch (err) {
            console.error(`Failed to sync mutation:`, err.message);
          }
        }

        return json({ ok: true, synced, message: `Synced ${synced.length} mutations successfully` });
      }

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
          'INSERT INTO users (email, name, password_hash, target_roles, target_locations, target_salary_min, byo_ai_key, byo_ai_provider, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime("now"), "active")'
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

      // ═══════════ API: JOBS FEED (BULK UPLOAD) ═══════════
      if (path === '/api/jobs/feed' && method === 'POST') {
        const body = await request.json();
        const jobs = body.jobs || [];
        if (!Array.isArray(jobs)) return error('jobs must be an array');
        
        let inserted = 0;
        const stmt = db.prepare(
          'INSERT OR IGNORE INTO jobs (external_id, title, company, location, platform, url, email, scraped_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, datetime("now"), "active")'
        );
        
        const batch = [];
        for (const job of jobs) {
          const title = (job.title || '').trim();
          const company = (job.company || 'Unknown').trim();
          const url = (job.url || '').trim();
          const location = (job.location || '').trim();
          const platform = (job.source || job.platform || 'web').trim();
          const email = (job.email || '').trim();
          
          if (!title || !url) continue;
          
          // Generate a simple unique hash for external_id based on URL
          const externalId = 'hash_' + Array.from(new TextEncoder().encode(url))
            .reduce((hash, val) => (hash * 31 + val) & 0xFFFFFFFF, 0).toString(16);
          
          batch.push(stmt.bind(externalId, title, company, location, platform, url, email));
        }
        
        if (batch.length > 0) {
          const res = await db.batch(batch);
          inserted = res.reduce((sum, r) => sum + (r.meta?.changes || 0), 0);
        }
        
        return json({ ok: true, received: jobs.length, inserted, message: `Successfully processed ${jobs.length} jobs` });
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
        // Optional Bearer token validation for security
        if (env.OUTBOX_SECRET) {
          const authHeader = request.headers.get('Authorization') || '';
          if (authHeader !== 'Bearer ' + env.OUTBOX_SECRET) {
            return error('Unauthorized', 401);
          }
        }

        const workerId = parseInt(url.searchParams.get('worker') || '0');
        const limit = parseInt(url.searchParams.get('limit') || '5');
        
        let emails = [];
        let redisPopped = false;
        
        // 1. Try pulling from Redis first
        try {
          const redisRes = await redisCommand(env, "RPOP", "hydra_email_queue");
          if (redisRes && redisRes.result) {
            const task = JSON.parse(redisRes.result);
            // Fetch User SMTP details
            const user = await db.prepare("SELECT byo_smtp_email, byo_smtp_token, email FROM users WHERE id = ?").bind(task.user_id).first();
            let smtpInfo = { email: '', password: '' };
            if (user) {
              if (user.byo_smtp_token) {
                const decoded = Array.from(user.byo_smtp_token).map(c => String.fromCharCode(c.charCodeAt(0) - 13)).join('');
                const parts = decoded.split(':');
                smtpInfo = { email: parts[0] || '', password: parts.slice(1).join(':') || '' };
              } else {
                smtpInfo = { email: user.email || '', password: '' };
              }
            }
            emails.push({
              id: task.id,
              to_email: task.to_email,
              to_name: task.to_name || '',
              subject: task.subject,
              body: task.body,
              smtp_email: smtpInfo.email,
              smtp_password: smtpInfo.password
            });
            redisPopped = true;
          }
        } catch (redisErr) {
          console.error("Failed to pop from Redis outbox:", redisErr.message);
        }

        // 2. Fallback: D1 SQL database
        if (!redisPopped) {
          // Use modulo to distribute across workers
          await db.prepare(
            "UPDATE email_outbox SET status = 'claimed', sent_at = datetime('now') WHERE id IN (SELECT id FROM email_outbox WHERE status = 'queued' AND id % 16 = ? ORDER BY id ASC LIMIT ?)"
          ).bind(workerId, limit).run();
          
          const claimed = await db.prepare(
            "SELECT eo.id, eo.to_email, eo.to_name, eo.subject, eo.body, u.byo_smtp_email, u.byo_smtp_token, u.email as user_email FROM email_outbox eo JOIN users u ON eo.user_id = u.id WHERE eo.status = 'claimed' AND eo.id % 16 = ? ORDER BY eo.id ASC"
          ).bind(workerId).all();
          
          emails = claimed.results.map(e => {
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
        }
        
        return json({ emails, worker: workerId });
      }

      // ═══════════ API: OUTBOX UPDATE ═══════════
      if (path === '/api/email/outbox/update' && method === 'POST') {
        if (env.OUTBOX_SECRET) {
          const authHeader = request.headers.get('Authorization') || '';
          if (authHeader !== 'Bearer ' + env.OUTBOX_SECRET) {
            return error('Unauthorized', 401);
          }
        }
        const body = await request.json();
        const { id, status: es, error } = body;
        if (!id || !es) return error('id and status required');
        
        await db.prepare(
          "UPDATE email_outbox SET status = ?, error = ?, sent_at = datetime('now') WHERE id = ?"
        ).bind(es === 'sent' ? 'sent' : 'failed', error || '', id).run();
        
        // Sync application state
        try {
          const outboxInfo = await db.prepare("SELECT user_id, job_id FROM email_outbox WHERE id = ?").bind(id).first();
          if (outboxInfo && outboxInfo.job_id) {
            if (es === 'sent') {
              await db.prepare(
                "UPDATE applications SET email_sent = 1, status = 'sent', sent_at = datetime('now') WHERE user_id = ? AND job_id = ?"
              ).bind(outboxInfo.user_id, outboxInfo.job_id).run();
            } else {
              await db.prepare(
                "UPDATE applications SET status = 'failed' WHERE user_id = ? AND job_id = ?"
              ).bind(outboxInfo.user_id, outboxInfo.job_id).run();
            }
          }
        } catch (syncErr) {
          console.error("Failed to sync application state:", syncErr.message);
        }

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
        
        const user = await db.prepare('SELECT name, target_roles, byo_ai_key, byo_ai_provider FROM users WHERE id = ?').bind(user_id).first();
        if (!user) return error('User not found', 404);
        
        const letter = await generateCoverLetter(ai, job_title, company, user.name || 'Applicant', user.target_roles || '', user.byo_ai_key || '', user.byo_ai_provider || 'groq');
        return json({ ok: true, cover_letter: letter });
      }

      // ═══════════ API: CV UPLOAD (R2 or KV fallback) ═══════════
      if (path === '/api/cv/upload' && method === 'POST') {
        const body = await request.json();
        const { user_id, filename, content } = body;
        if (!user_id || !content) return error('user_id and content required');
        
        const key = 'cv/' + user_id + '/' + (filename || 'resume.pdf');
        const binary = Uint8Array.from(atob(content), c => c.charCodeAt(0));
        
        if (r2) {
          // Use R2 (preferred)
          await r2.put(key, binary, { httpMetadata: { contentType: 'application/pdf' } });
        } else if (kv) {
          // Fallback to KV storage (25MB limit)
          await kv.put(key, binary, { expirationTtl: 86400 * 30, metadata: { contentType: 'application/pdf', user_id } });
        } else {
          return error('No storage available', 503);
        }
        
        await db.prepare('UPDATE users SET cv_url = ? WHERE id = ?').bind(key, user_id).run();
        return json({ ok: true, url: key, message: 'CV uploaded!', storage: r2 ? 'r2' : 'kv' });
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
        const paBase = env.PA_BASE || CONFIG.PA_BASE;
        const targetUrl = paBase.replace(/\/$/, '') + targetPath + url.search;
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
    // 1. Check if campaign has reached target count limit
    const targetLimit = camp.target_count || 50;
    const currentSent = camp.sent_count || 0;
    if (currentSent >= targetLimit) {
      console.log(`Campaign ${camp.id} reached its limit of ${targetLimit}. Marking completed.`);
      await db.prepare("UPDATE campaigns SET status = 'completed', completed_at = datetime('now') WHERE id = ?").bind(camp.id).run();
      return;
    }

    // 1b. Quota Shield Check: Check how many emails the user has already sent today
    const sentToday = await db.prepare(
      "SELECT COUNT(*) as c FROM email_outbox WHERE user_id = ? AND status = 'sent' AND date(sent_at) = date('now')"
    ).bind(camp.user_id).first();
    const dailyLimit = camp.daily_limit || 50;
    if (sentToday && sentToday.c >= dailyLimit) {
      console.log(`User ${camp.user_id} has reached their daily SMTP sending limit (${sentToday.c}/${dailyLimit}). Skipping for today.`);
      return;
    }

    const maxBinds = Math.min(targetLimit - currentSent, dailyLimit - (sentToday?.c || 0));
    if (maxBinds <= 0) return;

    // Find unscored jobs matching user's target roles and locations
    if (camp.target_roles) {
      const keywords = camp.target_roles.split(',').map(k => k.trim()).filter(Boolean);
      const locations = camp.target_locations ? camp.target_locations.split(',').map(l => l.trim()).filter(Boolean) : [];
      
      if (keywords.length > 0) {
        const likes = [];
        const binds = [];
        
        for (const kw of keywords) {
          likes.push("(title LIKE ? OR company LIKE ?)");
          binds.push(`%${kw}%`, `%${kw}%`);
        }
        
        let locQuery = "";
        if (locations.length > 0) {
          const locLikes = [];
          for (const loc of locations) {
            locLikes.push("location LIKE ?");
            binds.push(`%${loc}%`);
          }
          locQuery = ` AND (${locLikes.join(" OR ")})`;
        }
        
        const queryStr = `SELECT id, title, company, location, email FROM jobs WHERE (${likes.join(" OR ")})${locQuery} AND id NOT IN (SELECT job_id FROM applications WHERE user_id = ?) ORDER BY scraped_at ASC LIMIT ?`;
        binds.push(camp.user_id, Math.min(20, maxBinds));
        
        const jobs = await db.prepare(queryStr).bind(...binds).all();
        
        for (const job of jobs.results) {
          // Generate cover letter
          const letter = await generateCoverLetter(ai, job.title, job.company, camp.name, camp.target_roles, camp.byo_ai_key, camp.byo_ai_provider);
          
          // Create application record with campaign_id association
          await db.prepare(
            'INSERT INTO applications (user_id, job_id, campaign_id, status, cover_letter, email_sent) VALUES (?, ?, ?, ?, ?, 0)'
          ).bind(camp.user_id, job.id, camp.id, 'matched', letter.substring(0, 2000)).run();
          
          // Queue email in outbox
          const toEmail = job.email || '';
          if (toEmail) {
            const outRes = await db.prepare(
              "INSERT INTO email_outbox (campaign_id, user_id, job_id, to_email, to_name, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', datetime('now'))"
            ).bind(camp.id, camp.user_id, job.id, toEmail, job.company, 'Application for ' + job.title + ' at ' + job.company, letter.substring(0, 1000)).run();
            
            const outId = outRes?.meta?.last_row_id || Math.floor(Math.random() * 100000);
            
            // Push to Redis for distributed state backup
            try {
              await redisCommand(env, "LPUSH", "hydra_email_queue", JSON.stringify({
                id: outId, campaign_id: camp.id, user_id: camp.user_id, job_id: job.id,
                to_email: toEmail, to_name: job.company, subject: 'Application for ' + job.title + ' at ' + job.company,
                body: letter.substring(0, 1000)
              }));
            } catch (redisErr) {
              console.error("Failed to push email task to Redis queue:", redisErr.message);
            }
            
            console.log(`  Queued email for job ${job.id}: ${job.title} to ${toEmail}`);
          }
          console.log(`  Matched job ${job.id}: ${job.title} at ${job.company}`);
        }
      }
    }
    
    // Update campaign stats isolated by campaign ID
    const sentCount = await db.prepare("SELECT COUNT(*) as c FROM applications WHERE campaign_id = ? AND email_sent = 1").bind(camp.id).first();
    await db.prepare("UPDATE campaigns SET sent_count = ? WHERE id = ?").bind(sentCount?.c || 0, camp.id).run();
    
  } catch (e) {
    console.error(`Campaign ${camp.id} error:`, e.message);
  }
}
