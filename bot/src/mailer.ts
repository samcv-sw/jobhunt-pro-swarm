export function getRandomEmailAccount(): any {
    const accountsJson = process.env.GMAIL_ACCOUNTS_JSON;
    if (!accountsJson) {
        console.warn("WARNING: GMAIL_ACCOUNTS_JSON not set.");
        return null;
    }
    
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
