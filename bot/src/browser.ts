import { chromium, Browser, BrowserContext } from 'rebrowser-playwright';

export interface BrowserSession {
    browser: Browser;
    context: BrowserContext;
}

export async function launchBrowser(cookies: any[]): Promise<BrowserSession> {
    console.log("Launching rebrowser-playwright with strict memory optimizations...");
    
    const browser = await chromium.launch({
        headless: true,
        args: [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage", // CRITICAL for GitHub Actions memory limits
            "--no-sandbox",            // Required for GitHub Actions
            "--disable-gpu",           // Save resources
            "--disable-setuid-sandbox"
        ],
        proxy: { server: "socks5://127.0.0.1:40000" } // WARP IP Cloaking
    });

    const context = await browser.newContext();
    if (cookies.length > 0) {
        await context.addCookies(cookies);
    }
    
    return { browser, context };
}
