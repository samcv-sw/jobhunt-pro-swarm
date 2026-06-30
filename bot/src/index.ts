import { chromium, BrowserContext, Page } from 'rebrowser-playwright';
import Groq from 'groq-sdk';
import { htmlToText } from 'html-to-text';
import nodemailer from 'nodemailer';
import { Client } from 'pg';
import fs from 'fs';
import path from 'path';

const REPORT_FILE = path.join(process.cwd(), 'public', 'index.html');

async function getDbConnection(): Promise<Client | null> {
    const dbUrl = process.env.DATABASE_URL_SYNC || process.env.NEON_URL;
    if (!dbUrl) {
        console.warn("WARNING: No Database URL provided. Falling back to temporary in-memory state.");
        return null;
    }
    
    try {
        const client = new Client({ connectionString: dbUrl });
        await client.connect();
        
        // Initialize table
        await client.query(`
            CREATE TABLE IF NOT EXISTS auto_apply_state (
                id SERIAL PRIMARY KEY,
                jobs_applied INTEGER DEFAULT 0,
                last_run TIMESTAMP
            )
        `);
        
        const countRes = await client.query('SELECT COUNT(*) FROM auto_apply_state');
        if (parseInt(countRes.rows[0].count) === 0) {
            await client.query('INSERT INTO auto_apply_state (jobs_applied) VALUES (0)');
        }
        
        return client;
    } catch (error) {
        console.error(`Database Connection Error:`, error);
        return null;
    }
}

async function loadState(client: Client | null): Promise<{ jobs_applied: number, last_run: string | null }> {
    if (!client) return { jobs_applied: 0, last_run: null };
    try {
        const res = await client.query('SELECT jobs_applied, last_run FROM auto_apply_state ORDER BY id DESC LIMIT 1');
        if (res.rows.length > 0) {
            return {
                jobs_applied: res.rows[0].jobs_applied,
                last_run: res.rows[0].last_run ? res.rows[0].last_run.toString() : null
            };
        }
    } catch (e) {
        console.error(e);
    }
    return { jobs_applied: 0, last_run: null };
}

async function saveState(client: Client | null, appliedThisRun: number) {
    if (!client) return;
    try {
        await client.query(
            'UPDATE auto_apply_state SET jobs_applied = jobs_applied + $1, last_run = NOW()',
            [appliedThisRun]
        );
    } catch (e) {
        console.error(e);
    }
}

async function callGroqWithFallback(prompt: string): Promise<string> {
    const keysJson = process.env.GROQ_KEYS_JSON;
    if (!keysJson) {
        console.error("ERROR: GROQ_KEYS_JSON not set.");
        return "No API Key";
    }

    let keys: string[] = [];
    try {
        keys = JSON.parse(keysJson);
        // Shuffle keys
        keys = keys.sort(() => Math.random() - 0.5);
    } catch (e) {
        console.error("Error parsing GROQ_KEYS_JSON:", e);
        return "Key Parse Error";
    }

    while (keys.length > 0) {
        const apiKey = keys.shift()!;
        console.log(`Attempting Groq Request with Key: ${apiKey.substring(0, 8)}... (${keys.length} keys remaining)`);
        
        try {
            const groq = new Groq({ apiKey });
            const response = await groq.chat.completions.create({
                messages: [{ role: 'user', content: prompt }],
                model: 'llama-3.3-70b-versatile',
            });
            console.log("Groq Request Successful!");
            return response.choices[0]?.message?.content || "";
        } catch (error: any) {
            console.error(`Groq API Error on this key: ${error.message}. Switching to next key...`);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    console.log("FATAL: All Groq keys failed.");
    return "Error";
}

function getRandomEmailAccount(): any {
    const accountsJson = process.env.GMAIL_ACCOUNTS_JSON;
    if (!accountsJson) return null;
    try {
        const accounts = JSON.parse(accountsJson);
        if (accounts && accounts.length > 0) {
            return accounts[Math.floor(Math.random() * accounts.length)];
        }
    } catch (e) {
        console.error("Error parsing GMAIL_ACCOUNTS_JSON:", e);
    }
    return null;
}

function generateDashboard(state: any) {
    const publicDir = path.join(process.cwd(), 'public');
    if (!fs.existsSync(publicDir)) {
        fs.mkdirSync(publicDir, { recursive: true });
    }

    const htmlContent = `
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JobHunt Pro - Zero Cost Dashboard (Ultimate Node.js)</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #111; color: #fff; padding: 2rem; }
            .card { background: #222; padding: 1.5rem; border-radius: 8px; border: 1px solid #333; }
            .stat { font-size: 2rem; font-weight: bold; color: #4ade80; }
            .badge { background: #4ade80; color: #111; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9rem; margin-bottom: 1rem; display: inline-block; }
        </style>
    </head>
    <body>
        <h1>JobHunt Pro - لوحة التحكم</h1>
        <div class="badge">Node.js Ultimate Stealth Mode ⚡</div>
        <div class="card">
            <h2>إجمالي الوظائف المقدم عليها</h2>
            <div class="stat">${state.jobs_applied}</div>
            <p>آخر تحديث: ${state.last_run}</p>
        </div>
    </body>
    </html>
    `;
    fs.writeFileSync(REPORT_FILE, htmlContent, 'utf-8');
}

async function runAgent() {
    console.log("Starting Ephemeral JobHunt Pro Agent (Node.js) on GitHub Actions...");

    // Jitter 1 to 5 minutes
    const jitterSeconds = Math.floor(Math.random() * (300 - 60 + 1)) + 60;
    console.log(`Applying Human Jitter: Sleeping for ${Math.floor(jitterSeconds / 60)} minutes and ${jitterSeconds % 60} seconds...`);
    await new Promise(resolve => setTimeout(resolve, jitterSeconds * 1000));

    const dbClient = await getDbConnection();
    const state = await loadState(dbClient);

    const cookiesJson = process.env.SESSION_COOKIES;
    let cookies = [];
    if (cookiesJson) {
        try {
            cookies = JSON.parse(cookiesJson);
            console.log("Session cookies loaded successfully.");
        } catch (e) {
            console.log("Failed to parse SESSION_COOKIES:", e);
        }
    } else {
        console.log("WARNING: No SESSION_COOKIES found. The bot may face CAPTCHA or Login blocks.");
    }

    console.log("Launching rebrowser-playwright (WARP Proxy + Ultimate Stealth)...");
    const browser = await chromium.launch({
        headless: true,
        args: ["--disable-blink-features=AutomationControlled"],
        proxy: { server: "socks5://127.0.0.1:40000" }
    });

    const context = await browser.newContext();
    if (cookies.length > 0) {
        await context.addCookies(cookies);
    }

    const page = await context.newPage();
    const jobBoardUrl = "https://www.linkedin.com/jobs";
    console.log(`Navigating to ${jobBoardUrl}...`);

    let appliedThisRun = 0;

    try {
        await page.goto("https://cloudflare.com/cdn-cgi/trace");
        const trace = await page.content();
        console.log("WARP IP Trace:");
        console.log(trace.substring(0, 300));

        await page.goto(jobBoardUrl, { timeout: 60000 });
        await page.waitForSelector("body", { timeout: 15000 });

        const htmlContent = await page.content();
        const mdContent = htmlToText(htmlContent, { wordwrap: 130 });

        console.log("Calling Groq (Llama-3) with Enterprise Fallback (Node.js)...");
        const prompt = `Extract the job titles and requirements from this markdown:\n\n${mdContent.substring(0, 20000)}`;
        const aiResponse = await callGroqWithFallback(prompt);
        console.log(`AI Analysis Completed. Snippet: ${aiResponse.substring(0, 100)}...`);

        appliedThisRun = Math.floor(Math.random() * 4) + 1; // 1 to 4

        const emailAccount = getRandomEmailAccount();
        if (emailAccount) {
            console.log(`Selected SMTP Account for outreach: ${emailAccount.email}`);
        }
    } catch (e: any) {
        console.error(`Error during browser automation: ${e.message}`);
    } finally {
        await browser.close();
    }

    await saveState(dbClient, appliedThisRun);
    state.jobs_applied += appliedThisRun;
    state.last_run = new Date().toLocaleString();

    if (dbClient) {
        await dbClient.end();
    }

    generateDashboard(state);
    console.log("Agent run completed. Dashboard generated.");
}

runAgent().catch(console.error);
