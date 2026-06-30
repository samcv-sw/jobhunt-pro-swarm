// The Ultimate Stealth Background Orchestrator
chrome.runtime.onInstalled.addListener(() => { 
    console.log("JobHunt Pro Swarm Agent Installed."); 
    chrome.storage.local.set({ jobsApplied: 0 });
    
    // 1. Initialize KeepAlive Alarm (MV3 Resurrector)
    chrome.alarms.create('keepAlive', { periodInMinutes: 0.33 }); // ~20 seconds
    
    // 2. Seal WebRTC IP Leaks
    chrome.privacy.network.webRTCIPHandlingPolicy.set({
        value: 'disable_non_proxied_udp'
    }, () => console.log("🛡️ WebRTC IP Leaks Sealed."));
});

// Alarm Listener for KeepAlive
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'keepAlive') {
        console.log("💓 Swarm KeepAlive Ping.");
        // This log keeps the service worker awake
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "JOB_APPLIED") {
        console.log("Background Orchestrator received JOB_APPLIED event.");
        
        chrome.storage.local.get(['jobsApplied'], (result) => {
            let current = result.jobsApplied || 0;
            current++;
            chrome.storage.local.set({ jobsApplied: current });
            chrome.action.setBadgeText({ text: current.toString() });
            chrome.action.setBadgeBackgroundColor({ color: '#4ade80' });
        });
        
        getDB().then(db => {
            const tx = db.transaction("sync_queue", "readwrite");
            const store = tx.objectStore("sync_queue");
            store.add({
                job_url: sender.tab?.url || "unknown",
                timestamp: Date.now(),
                status: "pending_sync"
            });
            tx.oncomplete = () => console.log("💾 Job logged locally in IndexedDB.");
        }).catch(err => console.error("IndexedDB Error:", err));
        
        sendResponse({ status: "recorded" });
    }
});

// IndexedDB Init
const dbName = "SwarmDB";
function getDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(dbName, 1);
        request.onupgradeneeded = (event: any) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains("sync_queue")) {
                db.createObjectStore("sync_queue", { keyPath: "id", autoIncrement: true });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Global Error Telemetry
self.addEventListener('error', (event) => {
    console.error("🔥 Swarm Global Error Caught:", event.message);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error("🔥 Swarm Promise Rejection Caught:", event.reason);
});

