chrome.runtime.onInstalled.addListener(() => { 
    console.log("JobHunt Pro Swarm Agent Installed."); 
    chrome.storage.local.set({ jobsApplied: 0 });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "JOB_APPLIED") {
        console.log("Background Orchestrator received JOB_APPLIED event.");
        
        chrome.storage.local.get(['jobsApplied'], (result) => {
            let current = result.jobsApplied || 0;
            current++;
            chrome.storage.local.set({ jobsApplied: current });
            
            // Update the extension badge icon to show the count
            chrome.action.setBadgeText({ text: current.toString() });
            chrome.action.setBadgeBackgroundColor({ color: '#4ade80' });
        });
        
        sendResponse({ status: "recorded" });
    }
});
