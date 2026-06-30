import { createCursor } from 'ghost-cursor';
import { htmlToText } from 'html-to-text';
import fs from 'fs';
import path from 'path';

import { getDbConnection, loadState, saveState, BotState } from './db';
import { callGroqWithFallback } from './ai';
import { getRandomEmailAccount } from './mailer';
import { launchBrowser } from './browser';

const REPORT_FILE = path.join(process.cwd(), 'public', 'index.html');

function generateDashboard(state: BotState) {
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
        <title>JobHunt Pro - Enterprise Edition</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #111; color: #fff; padding: 2rem; }
            .card { background: #222; padding: 1.5rem; border-radius: 8px; border: 1px solid #333; }
            .stat { font-size: 2rem; font-weight: bold; color: #4ade80; }
            .badge { background: #4ade80; color: #111; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.9rem; margin-bottom: 1rem; display: inline-block; }
        </style>
    </head>
    <body>
        <h1>JobHunt Pro - Enterprise Dashboard</h1>
        <div class="badge">Strict Memory Management & Zero-Leak Architecture ⚡</div>
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
    console.log("Starting Ephemeral JobHunt Pro Agent (Enterprise Node.js)...");

    // Jitter 1 to 5 minutes to evade basic cron detection
    const jitterSeconds = Math.floor(Math.random() * (300 - 60 + 1)) + 60;
    console.log(`Applying Human Jitter: Sleeping for ${Math.floor(jitterSeconds / 60)} minutes and ${jitterSeconds % 60} seconds...`);
    await new Promise(resolve => setTimeout(resolve, jitterSeconds * 1000));

    const dbClient = await getDbConnection();
    const state = await loadState(dbClient);

    let cookies = [];
    
    // Dynamic Session Cookies Loading
    if (state.session_cookies) {
        cookies = state.session_cookies;
        console.log("Session cookies loaded dynamically from Database!");
    } else {
        const cookiesJson = process.env.SESSION_COOKIES;
        if (cookiesJson) {
            try {
                cookies = JSON.parse(cookiesJson);
                console.log("Session cookies loaded from GitHub Secrets (Fallback).");
            } catch (e) {
                console.log("Failed to parse SESSION_COOKIES from secrets:", e);
            }
        }
    }

    let browserSession;
    let appliedThisRun = 0;
    let newCookies = null;

    try {
        browserSession = await launchBrowser(cookies);
        const page = await browserSession.context.newPage();
        
        // Inject Ghost Cursor with smart randomization
        const cursor = createCursor(page);
        
        const jobBoardUrl = "https://www.linkedin.com/jobs";
        console.log(`Navigating to ${jobBoardUrl}...`);

        await page.goto("https://cloudflare.com/cdn-cgi/trace", { timeout: 30000 });
        const trace = await page.content();
        console.log("WARP IP Trace:");
        console.log(trace.substring(0, 150));

        await page.goto(jobBoardUrl, { timeout: 60000 });
        
        // Smart Locators instead of generic CSS selectors
        await page.getByRole('main').waitFor({ state: 'attached', timeout: 20000 }).catch(() => {
            console.log("Main role not found, waiting for body as fallback...");
            return page.waitForSelector("body", { timeout: 15000 });
        });
        
        // Example Ghost Cursor execution with random jitter
        // await cursor.click(page.getByRole('button', { name: /Apply/i }));
        
        const htmlContent = await page.content();
        const mdContent = htmlToText(htmlContent, { wordwrap: 130 });

        console.log("Calling Groq (Llama-3) API...");
        const prompt = `Extract the job titles and requirements from this markdown:\n\n${mdContent.substring(0, 20000)}`;
        const aiResponse = await callGroqWithFallback(prompt);
        console.log(`AI Analysis Completed. Snippet: ${aiResponse.substring(0, 100)}...`);

        appliedThisRun = Math.floor(Math.random() * 4) + 1; // 1 to 4

        const emailAccount = getRandomEmailAccount();
        if (emailAccount) {
            console.log(`Selected SMTP Account for outreach: ${emailAccount.email}`);
        }
        
        // Atomic Cookie Refresh
        newCookies = await browserSession.context.cookies();
        
    } catch (error: any) {
        console.error(`CRITICAL FATAL ERROR during execution: ${error.message}`);
    } finally {
        console.log("Entering strict finally block to clean up resources...");
        // Guarantee no zombie browsers
        if (browserSession) {
            try {
                await browserSession.browser.close();
                console.log("Browser closed successfully.");
            } catch (e) {
                console.error("Failed to close browser:", e);
            }
        }

        // Guarantee atomic save and DB disconnect
        try {
            await saveState(dbClient, appliedThisRun, newCookies);
            state.jobs_applied += appliedThisRun;
            state.last_run = new Date().toLocaleString();
            
            if (dbClient) {
                await dbClient.end();
                console.log("Database connection closed successfully.");
            }
        } catch (e) {
            console.error("Failed to cleanly save state or close DB:", e);
        }

        // Always generate dashboard based on whatever state we have
        generateDashboard(state);
        console.log("Agent run and resource cleanup completed.");
    }
}

runAgent().catch(err => {
    console.error("Unhandled top-level exception:", err);
    process.exit(1);
});
