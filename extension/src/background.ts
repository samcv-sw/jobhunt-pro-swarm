// God-Tier Background Orchestrator with IndexedDB Sync
chrome.runtime.onInstalled.addListener(() => { 
    console.log("JobHunt Pro Swarm Agent Installed."); 
    chrome.storage.local.set({ jobsApplied: 0 });
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
    // In production, sync this to /api/log
});

self.addEventListener('unhandledrejection', (event) => {
    console.error("🔥 Swarm Promise Rejection Caught:", event.reason);
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "JOB_APPLIED") {
        console.log("Background Orchestrator received JOB_APPLIED event.");
        
        // 1. Update Badge immediately for UX
        chrome.storage.local.get(['jobsApplied'], (result) => {
            let current = result.jobsApplied || 0;
            current++;
            chrome.storage.local.set({ jobsApplied: current });
            chrome.action.setBadgeText({ text: current.toString() });
            chrome.action.setBadgeBackgroundColor({ color: '#4ade80' });
        });
        
        // 2. Local-First IndexedDB Logging
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
