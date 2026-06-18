let backendUrl = "https://jhfguf.pythonanywhere.com";
const ENCRYPTION_KEY = "jh_pro_secure_key_2026"; // Shared secret with backend

// XOR Encryption Helper
function xorEncryptDecrypt(input, key) {
    let output = '';
    for (let i = 0; i < input.length; i++) {
        output += String.fromCharCode(input.charCodeAt(i) ^ key.charCodeAt(i % key.length));
    }
    return output;
}

chrome.runtime.onInstalled.addListener(() => {
    // Poll every 1 minute
    chrome.alarms.create("pollBackend", { periodInMinutes: 1 });
});

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "pollBackend") {
        pollTasks();
    }
});

let isProcessing = false;
let ghostWindowId = null;
let activeTasksInWindow = 0;

// Ghost Window Management
async function getOrCreateGhostWindow() {
    if (ghostWindowId) {
        try {
            await chrome.windows.get(ghostWindowId);
            return ghostWindowId;
        } catch (e) {
            ghostWindowId = null; // Window was closed
        }
    }
    
    // Create a new minimized, popup window
    const win = await chrome.windows.create({
        url: "about:blank",
        type: "popup",
        state: "minimized",
        focused: false
    });
    ghostWindowId = win.id;
    return ghostWindowId;
}

async function cleanupGhostWindow() {
    activeTasksInWindow--;
    if (activeTasksInWindow <= 0 && ghostWindowId) {
        try {
            await chrome.windows.remove(ghostWindowId);
        } catch(e) {}
        ghostWindowId = null;
        activeTasksInWindow = 0;
    }
}

async function pollTasks() {
    if (isProcessing) return;
    
    try {
        const { userToken } = await chrome.storage.local.get('userToken');
        if (!userToken) return;

        isProcessing = true;
        const response = await fetch(`${backendUrl}/api/ext/poll-tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: userToken })
        });
        
        const data = await response.json();
        if (data.task) {
            // Decrypt Payload
            let decryptedPayload = data.task.payload;
            if (data.task.encrypted) {
                try {
                    const decoded = atob(data.task.payload);
                    const decryptedStr = xorEncryptDecrypt(decoded, ENCRYPTION_KEY);
                    decryptedPayload = JSON.parse(decryptedStr);
                } catch(e) {
                    console.error("Decryption failed", e);
                }
            }
            
            data.task.payload = decryptedPayload;
            await handleTask(data.task);
        }
    } catch (e) {
        console.error("Polling failed:", e);
    } finally {
        isProcessing = false;
    }
}

async function handleTask(task) {
    const windowId = await getOrCreateGhostWindow();
    activeTasksInWindow++;
    
    if (task.type === "SCRAPE_JOBS") {
        const url = `https://www.linkedin.com/jobs/search?keywords=${encodeURIComponent(task.payload.keyword)}&location=${encodeURIComponent(task.payload.location)}&f_WT=2`;
        const tab = await chrome.tabs.create({ windowId: windowId, url: url, active: false });
        
        // Wait for scraper-content.js to do its job
        chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
            if (tabId === tab.id && info.status === 'complete') {
                chrome.tabs.onUpdated.removeListener(listener);
                // The content script will automatically scrape and message back
                chrome.tabs.sendMessage(tab.id, { action: "DO_SCRAPE", taskId: task.id }, (response) => {
                    if (response && response.jobs) {
                        submitResult(task.id, { jobs: response.jobs });
                        chrome.tabs.remove(tab.id);
                        cleanupGhostWindow();
                    }
                });
            }
        });
    }
    else if (task.type === "SEND_EMAIL") {
        const url = `https://mail.google.com/mail/u/0/#inbox`;
        const tab = await chrome.tabs.create({ windowId: windowId, url: url, active: false });
        
        chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
            if (tabId === tab.id && info.status === 'complete') {
                chrome.tabs.onUpdated.removeListener(listener);
                chrome.tabs.sendMessage(tab.id, { action: "SEND_GMAIL", payload: task.payload, taskId: task.id }, (response) => {
                    if (response && response.success) {
                        submitResult(task.id, { success: true });
                        setTimeout(() => {
                            chrome.tabs.remove(tab.id);
                            cleanupGhostWindow();
                        }, 2000);
                    }
                });
            }
        });
    }
    else if (task.type === "GENERATE_COVER_LETTER") {
        const prompt = `Write a short, professional cover letter for the position of "${task.payload.title}" at "${task.payload.company}".\nJob Description: ${task.payload.description}\n\nMy Base CV:\n${task.payload.baseCv}\n\nKeep it under 250 words and don't include placeholders.`;
        
        const url = `https://chatgpt.com/`;
        const tab = await chrome.tabs.create({ windowId: windowId, url: url, active: false });
        
        chrome.storage.local.set({ 
            pendingPrompt: { taskId: task.id, prompt: prompt, tabId: tab.id } 
        });
    }
}

async function submitResult(taskId, result) {
    const { userToken } = await chrome.storage.local.get('userToken');
    try {
        // Encrypt Result
        const resultStr = JSON.stringify(result);
        const encryptedResult = btoa(xorEncryptDecrypt(resultStr, ENCRYPTION_KEY));
        
        await fetch(`${backendUrl}/api/ext/submit-results`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: userToken, taskId: taskId, result: encryptedResult, encrypted: true })
        });
    } catch(e) {
        console.error("Failed to submit result", e);
    }
}

// Handle responses from chatgpt-content.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "AI_GENERATION_COMPLETE") {
        submitResult(request.taskId, { cover_letter: request.text });
        if (request.tabId) chrome.tabs.remove(request.tabId);
    }
    else if (request.action === "TRIGGER_POLL") {
        pollTasks();
        sendResponse({status: "ok"});
    }
    return true;
});
