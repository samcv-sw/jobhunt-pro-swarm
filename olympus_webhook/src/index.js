// Built-in Web Crypto API is used for HMAC verification

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // --- CORS Headers ---
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    // --- CHECKOUT ENDPOINT (NOWPayments) ---
    if (url.pathname === '/api/v1/checkout' && request.method === 'POST') {
        try {
            const body = await request.json();
            const telegramId = body.userId;
            
            // Create Invoice via NOWPayments
            const npPayload = {
                price_amount: 20,
                price_currency: "usd",
                order_id: telegramId + "_" + Date.now(),
                order_description: "JobHunt Pro AI - Lifetime Access",
                ipn_callback_url: "https://olympus-webhook.samsalameh-cv.workers.dev/api/v1/webhook/nowpayments",
                success_url: "https://t.me/JobHuntPro_Ai_Bot",
                cancel_url: "https://t.me/JobHuntPro_Ai_Bot"
            };

            const npRes = await fetch("https://api.nowpayments.io/v1/invoice", {
                method: 'POST',
                headers: {
                    'x-api-key': env.NOWPAYMENTS_API_KEY,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(npPayload)
            });

            const npData = await npRes.json();
            if (npData.invoice_url) {
                return new Response(JSON.stringify({ invoice_url: npData.invoice_url }), { 
                    status: 200, 
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
                });
            } else {
                return new Response(JSON.stringify({ error: "Failed to generate invoice", details: npData }), { 
                    status: 500,
                    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
                });
            }
        } catch (e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
        }
    }
    
    // --- TELEGRAM WEBHOOK ---
    if (url.pathname === '/api/v1/webhook/telegram') {
        try {
            const body = await request.json();
            
            // Handle /start command and referrals
            if (body && body.message && body.message.text && body.message.text.startsWith('/start')) {
                const chatId = body.message.chat.id.toString();
                const firstName = body.message.chat.first_name || "User";
                const textParts = body.message.text.split(' ');
                
                let referredBy = null;
                if (textParts.length > 1) {
                    referredBy = textParts[1];
                }
                
                try {
                    // Track user in D1 Database
                    await env.leviathan_db.prepare(
                        `INSERT INTO users (telegram_id, first_name, referral_code, referred_by) 
                         VALUES (?, ?, ?, ?) 
                         ON CONFLICT(telegram_id) DO NOTHING`
                    ).bind(chatId, firstName, chatId, referredBy).run();
                    
                    // If they were referred, give the referrer a point
                    if (referredBy && referredBy !== chatId) {
                        await env.leviathan_db.prepare(
                            `UPDATE users SET credits = credits + 1 WHERE referral_code = ?`
                        ).bind(referredBy).run();
                    }
                } catch (dbErr) {
                    console.error("Database Error: ", dbErr);
                }

                // Send Welcome Message with Mini App Link
                const miniAppUrl = "https://leviathan-miniapp.pages.dev";
                const telegramApi = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
                
                const reply = {
                    chat_id: chatId,
                    text: `🚀 Welcome to JobHunt Pro AI, ${firstName}!\n\nClick the button below to launch the app and automatically apply to 500 remote jobs worldwide.`,
                    reply_markup: {
                        inline_keyboard: [[{ text: "Open AI App 🚀", web_app: { url: miniAppUrl } }]]
                    }
                };
                
                await fetch(telegramApi, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(reply)
                });
            }
            
            // Handle CV Uploads (PDF)
            if (body && body.message && body.message.document) {
                const chatId = body.message.chat.id.toString();
                const document = body.message.document;
                
                if (document.mime_type === "application/pdf") {
                    const fileId = document.file_id;
                    
                    try {
                        await env.leviathan_db.prepare(
                            `UPDATE users SET cv_file_id = ?, job_status = 'queued' WHERE telegram_id = ?`
                        ).bind(fileId, chatId).run();
                        
                        const telegramApi = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
                        await fetch(telegramApi, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                chat_id: chatId,
                                text: "📄 CV Received & Queued!\n\n🤖 Our local AI Swarm has received your CV. It is now in the processing queue. You will receive live updates here once the application blitz begins!"
                            })
                        });
                    } catch (dbErr) {
                        console.error("Database Error on CV upload: ", dbErr);
                    }
                }
            }
            
            return new Response('OK', { status: 200 });
        } catch (e) {
            console.error("Telegram error:", e);
            return new Response('OK', { status: 200 }); // Always return 200 to Telegram so it stops retrying
        }
    }
    
    // --- LOCAL QUEUE API ---
    if (url.pathname === '/api/v1/queue' && request.method === 'GET') {
        try {
            // Get 10 pending jobs
            const { results } = await env.leviathan_db.prepare(
                `SELECT telegram_id, cv_file_id FROM users WHERE job_status = 'queued' LIMIT 10`
            ).all();
            
            return new Response(JSON.stringify(results || []), { 
                status: 200, 
                headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
            });
        } catch (e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
        }
    }
    
    // --- USER PROFILE API ---
    if (url.pathname.startsWith('/api/v1/user/') && request.method === 'GET') {
        try {
            const telegramId = url.pathname.split('/').pop();
            const { results } = await env.leviathan_db.prepare(
                `SELECT credits, job_status FROM users WHERE telegram_id = ?`
            ).bind(telegramId).all();
            
            if (results && results.length > 0) {
                return new Response(JSON.stringify(results[0]), { 
                    status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
                });
            } else {
                return new Response(JSON.stringify({ credits: 0, job_status: null }), { 
                    status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
                });
            }
        } catch (e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
        }
    }
    
    // --- B2B RECRUITER API (DATA BROKER) ---
    if (url.pathname === '/api/v1/b2b/candidates' && request.method === 'GET') {
        try {
            const apiKey = request.headers.get('x-b2b-key');
            // Hardcoded B2B key for MVP. In production, check against a recruiters table.
            if (apiKey !== env.B2B_API_KEY) {
                return new Response(JSON.stringify({ error: "Unauthorized B2B Access" }), { status: 403, headers: corsHeaders });
            }
            
            // Return anonymous stats: total candidates, grouped by status
            const totalQuery = await env.leviathan_db.prepare(`SELECT COUNT(*) as total FROM users`).all();
            const statusQuery = await env.leviathan_db.prepare(`SELECT job_status, COUNT(*) as count FROM users GROUP BY job_status`).all();
            
            const report = {
                total_candidates_pool: totalQuery.results[0].total,
                candidates_by_status: statusQuery.results,
                pricing: "Contact sales@jobhuntpro.ai to unlock full candidate contact details. $500/mo."
            };
            
            return new Response(JSON.stringify(report), { 
                status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
            });
        } catch (e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
        }
    }
    
    // --- MARK JOB AS IN_PROGRESS / DONE ---
    if (url.pathname === '/api/v1/queue/status' && request.method === 'POST') {
        try {
            const body = await request.json();
            const { telegram_id, status } = body;
            await env.leviathan_db.prepare(
                `UPDATE users SET job_status = ? WHERE telegram_id = ?`
            ).bind(status, String(telegram_id)).run();
            
            return new Response(JSON.stringify({ success: true }), { 
                status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
            });
        } catch (e) {
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
        }
    }
    
    // --- NOWPAYMENTS WEBHOOK ---
    if (url.pathname === '/api/v1/webhook/nowpayments') {
        try {
          const signature = request.headers.get('x-nowpayments-sig');
          if (!signature) {
            return new Response('Missing Signature', { status: 400 });
          }

          const bodyText = await request.text();
          const bodyDict = JSON.parse(bodyText);
          
          const sortedKeys = Object.keys(bodyDict).sort();
          const sortedObj = {};
          for (const key of sortedKeys) {
            sortedObj[key] = bodyDict[key];
          }
          const message = JSON.stringify(sortedObj);
          
          const encoder = new TextEncoder();
          const keyData = encoder.encode(env.IPN_SECRET);
          
          const cryptoKey = await crypto.subtle.importKey(
            'raw', keyData, { name: 'HMAC', hash: 'SHA-512' }, false, ['sign', 'verify']
          );
          
          const signatureBytes = await crypto.subtle.sign(
            'HMAC', cryptoKey, encoder.encode(message)
          );
          
          const hashArray = Array.from(new Uint8Array(signatureBytes));
          const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
          
          if (hashHex !== signature) {
            console.error("Invalid Signature!");
            return new Response('Invalid Signature', { status: 403 });
          }

          const paymentStatus = bodyDict.payment_status;
          const orderId = bodyDict.order_id;
          
          console.log(`Valid IPN received! Order: ${orderId} | Status: ${paymentStatus}`);
          
          if (paymentStatus === 'finished') {
            console.log(`Payment FINISHED for ${orderId}. Triggering automated delivery...`);
            const telegramId = orderId.split("_")[0];
            
            await env.leviathan_db.prepare(
                `UPDATE users SET job_status = 'queued' WHERE telegram_id = ?`
            ).bind(telegramId).run();

            try {
                // Round-Robin Multi-Cloud Trigger Strategy
                const { results } = await env.leviathan_db.prepare(
                    `SELECT value FROM global_registry WHERE key = 'current_cloud_provider'`
                ).all();
                
                let provider = results.length > 0 ? results[0].value : 'github';
                
                console.log(`Triggering Swarm on Cloud Provider: ${provider}`);
                
                if (provider === 'github') {
                    const ghRes = await fetch("https://api.github.com/repos/samcv-sw/jobhunt-pro-swarm/actions/workflows/ghost_swarm.yml/dispatches", {
                        method: "POST",
                        headers: {
                            "Accept": "application/vnd.github.v3+json",
                            "Authorization": `token ${env.GITHUB_TOKEN}`,
                            "User-Agent": "Cloudflare-Worker"
                        },
                        body: JSON.stringify({ ref: "main" })
                    });
                    
                    if (ghRes.status === 403 || ghRes.status === 429) {
                        console.log("GitHub limits reached. Failing over to GitLab...");
                        await env.leviathan_db.prepare(`INSERT OR REPLACE INTO global_registry (key, value) VALUES ('current_cloud_provider', 'gitlab')`).run();
                    }
                } else if (provider === 'gitlab') {
                    // GitLab CI/CD execution payload
                    const glRes = await fetch("https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/trigger/pipeline", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ token: env.GITLAB_TOKEN, ref: "main" })
                    });
                    
                    if (glRes.status === 403 || glRes.status === 429) {
                        console.log("GitLab limits reached. Failing over to Bitbucket...");
                        await env.leviathan_db.prepare(`INSERT OR REPLACE INTO global_registry (key, value) VALUES ('current_cloud_provider', 'bitbucket')`).run();
                    }
                } else {
                    // Bitbucket execution payload
                    const bbRes = await fetch("https://api.bitbucket.org/2.0/repositories/YOUR_WORKSPACE/YOUR_REPO/pipelines/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${env.BITBUCKET_TOKEN}`
                        },
                        body: JSON.stringify({ target: { ref_type: "branch", type: "pipeline_ref_target", ref_name: "main" } })
                    });
                    
                    if (bbRes.status === 403 || bbRes.status === 429) {
                        console.log("Bitbucket limits reached. Resetting to GitHub...");
                        await env.leviathan_db.prepare(`INSERT OR REPLACE INTO global_registry (key, value) VALUES ('current_cloud_provider', 'github')`).run();
                    }
                }
            } catch (err) {
                console.error("Failed to trigger Multi-Cloud Action:", err);
            }
          }
          
          return new Response(JSON.stringify({ status: 'ok' }), { status: 200, headers: {'Content-Type': 'application/json'} });
        } catch (e) {
          return new Response('Error Processing Webhook: ' + e.message, { status: 500 });
        }
    }
    
    return new Response('Not Found', { status: 404 });
  }
};
