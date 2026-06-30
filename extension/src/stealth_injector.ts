// The Infinite Swarm Engine - Stealth Injector
// Runs at document_start in the MAIN world to remove automation traces

(function() {
    try {
        // 1. Remove navigator.webdriver
        if (navigator.webdriver) {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        }
        
        // 2. Hide CDP/Chrome variables
        const cdc_pattern = /[a-zA-Z0-9]{22}_[a-zA-Z0-9]+/;
        for (const key in window) {
            if (cdc_pattern.test(key)) {
                delete (window as any)[key];
            }
        }
        
        // 3. Override window.chrome if needed (though usually okay for extensions)
        // We ensure we don't look like Puppeteer/Selenium
        
        // 4. Spoof Permissions API for notifications/push (often checked by Datadome)
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission } as PermissionStatus) :
                originalQuery(parameters)
        );
        
        console.log("[Ghost Swarm] MAIN world stealth payload injected successfully.");
    } catch (e) {
        // Silently fail to avoid detection
    }
})();
